"""Real old -> expanded DB -> new -> outage -> old -> new OCI lifecycle.

Only generated, invocation-owned resources are removed. Phase 1's app/volumes
and any existing database are never selected. Python standard library only.
"""
import argparse
import hashlib
import http.cookiejar
import json
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "f7e0cadb1a1c78d73aff011298a4b2eae84af9d4"
PG = "docker.io/library/postgres:17.7-alpine"


def source_hash():
    files = [ROOT / p for p in ("Dockerfile", "global.json", "Directory.Build.props", "EchoCase.slnx")]
    for directory in ("src", "frontend"):
        files.extend(p for p in (ROOT / directory).rglob("*") if p.is_file() and not set(p.relative_to(ROOT).parts) & {
            "bin", "obj", "node_modules", "dist", "test-results", "playwright-report", "wwwroot"
        } and p.suffix != ".tsbuildinfo")
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=("podman", "docker"), default="podman")
    parser.add_argument("--output", default="evidence/phase2a/delivery")
    parser.add_argument("--port", type=int, default=6081)
    args = parser.parse_args()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    prefix = "echocase-p2a-" + uuid.uuid4().hex[:8]
    base = ROOT / args.output
    out = base / run_id
    out.mkdir(parents=True, exist_ok=False)
    scratch = ROOT / "work" / "phase2a-delivery" / run_id
    scratch.mkdir(parents=True, exist_ok=False)
    old_source = scratch / "old"
    old_source.mkdir()
    owned_containers, owned_volumes, owned_networks = set(), set(), set()
    engine = args.engine
    result = {"kind": "REAL_APPLICATION_OCI_UPGRADE_AND_ROLLBACK", "runId": run_id,
              "startedAtUtc": datetime.now(timezone.utc).isoformat(), "engine": engine,
              "oldSourceCommit": BASELINE, "sourceCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "workingTreeDirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
              "sourceTreeSha256": source_hash(), "steps": [], "status": "RUNNING"}

    def command(*parts, check=True, log=None, timeout=120):
        proc = subprocess.run([engine, *parts], cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
        if log:
            (out / log).write_text(proc.stdout + proc.stderr, encoding="utf-8")
        if check and proc.returncode:
            raise RuntimeError(f"{engine} {parts[0]} failed ({proc.returncode}); {log or proc.stderr[-1500:]}")
        return proc

    def build(image, context, label, logfile):
        # Build output stays in the evidence directory, not in chat or a fabricated result.
        with (out / logfile).open("w", encoding="utf-8") as stream:
            p = subprocess.run([engine, "build", "--memory", "1500m", "--label", f"org.opencontainers.image.revision={label}",
                                "-t", image, str(context)], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
        if p.returncode:
            raise RuntimeError(f"Image build failed; see {logfile}")
        inspect = json.loads(command("image", "inspect", image).stdout)[0]
        if inspect["Config"]["User"] in ("", "root", "0"):
            raise RuntimeError("Application image runs as root")
        return {"id": inspect["Id"], "tag": image, "user": inspect["Config"]["User"], "revisionLabel": label}

    def step(name, **facts):
        result["steps"].append({"name": name, "atUtc": datetime.now(timezone.utc).isoformat(), **facts})
        print(name, flush=True)

    net, db, app = prefix + "-net", prefix + "-db", prefix + "-app"
    data, keys = prefix + "-data", prefix + "-keys"
    connection = f"ConnectionStrings__EchoCase=Host={db};Database=echocase;Username=echocase;Password=phase2a-disposable-only;Timeout=3"
    env = ["-e", connection, "-e", "ASPNETCORE_ENVIRONMENT=Development"]
    origin = f"http://127.0.0.1:{args.port}"
    jar = http.cookiejar.CookieJar()
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    token = ""

    def call(path, method="GET", body=None, version=None, key=None):
        headers = {"Accept": "application/json"}
        if method != "GET":
            headers.update({"X-CSRF-TOKEN": token, "Idempotency-Key": key or str(uuid.uuid4())})
        if version is not None:
            headers["If-Match"] = f'"{version}"'
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(origin + path, data=json.dumps(body).encode("utf-8") if body is not None else None, headers=headers, method=method)
        try:
            response = client.open(request, timeout=25)
        except urllib.error.HTTPError as e:
            response = e
        with response:
            raw = response.read()
            payload = json.loads(raw) if "json" in response.headers.get("Content-Type", "") and raw else raw.decode("utf-8")
            return response.status, payload, response.headers.get("X-Trace-Id")

    def ok(path, method="GET", body=None, version=None, key=None):
        status, value, trace = call(path, method, body, version, key)
        if status != 200:
            raise RuntimeError(f"{method} {path} returned {status}: {value}; trace {trace}")
        return value

    def ready():
        for _ in range(80):
            try:
                if call("/health/ready")[0] == 200:
                    return
            except (urllib.error.URLError, TimeoutError, OSError):
                pass
            time.sleep(.5)
        raise RuntimeError("Application readiness timeout")

    def start(image):
        if app in owned_containers:
            command("rm", "-f", app)
            owned_containers.remove(app)
        container = command("run", "-d", "--name", app, "--network", net, "--memory", "384m", "--cpus", "1",
                            "-p", f"127.0.0.1:{args.port}:8080", "-v", keys + ":/home/app/.aspnet/DataProtection-Keys", *env, image).stdout.strip()
        owned_containers.add(app)
        ready()
        return container

    def migrate(image, logfile):
        command("run", "--rm", "--network", net, *env, image, "--migrate", log=logfile)

    def sql(text):
        return command("exec", db, "psql", "-U", "echocase", "-d", "echocase", "-At", "-c", text).stdout.strip()

    try:
        result["engineVersion"] = command("--version").stdout.strip()
        with (scratch / "baseline.tar").open("wb") as stream:
            subprocess.run(["git", "archive", "--format=tar", BASELINE], cwd=ROOT, stdout=stream, check=True)
        with tarfile.open(scratch / "baseline.tar") as archive:
            archive.extractall(old_source, filter="data")
        old_image = "localhost/echocase:phase1-f7e0cad"
        new_image = "localhost/echocase:phase2a-" + result["sourceTreeSha256"][:12]
        result["oldImage"] = build(old_image, old_source, BASELINE, "build-old.txt")
        result["newImage"] = build(new_image, ROOT, result["sourceCommit"] + ":" + result["sourceTreeSha256"][:12], "build-new.txt")
        step("clean-source-images-built", nonRoot=True)
        command("network", "create", net); owned_networks.add(net)
        for volume in (data, keys):
            command("volume", "create", volume); owned_volumes.add(volume)
        command("run", "--rm", "--user", "0", "-v", keys + ":/keys", PG, "chown", "1654:1654", "/keys")
        command("run", "-d", "--name", db, "--network", net, "--memory", "384m", "--cpus", "1",
                "-e", "POSTGRES_USER=echocase", "-e", "POSTGRES_PASSWORD=phase2a-disposable-only", "-e", "POSTGRES_DB=echocase",
                "-v", data + ":/var/lib/postgresql/data", PG)
        owned_containers.add(db)
        for _ in range(60):
            if command("exec", db, "pg_isready", "-h", "127.0.0.1", "-U", "echocase", check=False).returncode == 0:
                break
            time.sleep(.5)
        else:
            raise RuntimeError("PostgreSQL initialization timeout")
        migrate(old_image, "migration-old.txt")
        first_container = start(old_image)
        html = ok("/")
        assert "EchoCase" in html and "/assets/" in html
        token = ok("/api/auth/csrf")["token"]
        credentials = {"email": f"delivery-{uuid.uuid4().hex}@example.test", "password": "StrongLabPassword42"}
        ok("/api/auth/register", "POST", credentials)
        ok("/api/auth/login", "POST", credentials)
        token = ok("/api/auth/csrf")["token"]
        user_id = ok("/api/auth/me")["id"]
        s = ok("/api/investigations", "POST", {"caseId": "harbor-01"})
        path = "/api/investigations/" + s["id"]

        def change(route, method="POST", body=None, key=None, version=None):
            return ok(path + "/" + route, method, body, s["version"] if version is None else version, key)

        for evidence in ("access-log", "badge-ledger", "dispatch"):
            s = change(f"evidence/{evidence}/examine")
        s = change("links", body={"sourceId": "access-log", "targetId": "badge-ledger", "kind": "Corroborates"})
        legacy_key, legacy_version = str(uuid.uuid4()), s["version"]
        legacy_body = {"sourceId": "badge-ledger", "targetId": "dispatch", "kind": "Corroborates"}
        s = change("links", body=legacy_body, key=legacy_key)
        legacy_link_receipt = s
        s = change("notes", "PUT", {"notes": "旧应用升级前保存的原始笔记"})
        original = s
        step("old-application-seeded-real-case", version=s["version"], investigationId=s["id"], linkIds=[l["id"] for l in s["links"]], container=first_container)

        migrate(new_image, "migration-expanded.txt")
        migrate(new_image, "migration-repeat.txt")
        assert len(json.loads(sql('SELECT json_agg("MigrationId" ORDER BY "MigrationId") FROM "__EFMigrationsHistory"'))) == 3
        assert ok(path)["links"] == original["links"]  # Old DTO and binary still read expanded schema.
        s = change("notes", "PUT", {"notes": "扩展模式后仍由旧应用正常保存"})
        step("schema-expanded-old-application-still-writes", version=s["version"], repeatMigration="no-op")

        second_container = start(new_image)
        assert ok("/api/auth/me")["id"] == user_id
        s = ok(path)
        assert s["notes"] == "扩展模式后仍由旧应用正常保存"
        assert all(l["rationale"] is None and l["revisedAt"] is None for l in s["links"])
        replay = change("links", body=legacy_body, key=legacy_key, version=legacy_version)
        assert replay["version"] == legacy_link_receipt["version"]
        assert [l["id"] for l in replay["links"]] == [l["id"] for l in legacy_link_receipt["links"]]
        link_id = s["links"][0]["id"]
        rationale = "升级后核对门禁时钟与领用记录，发现两者目前不能互相印证，需要保留矛盾解释。"
        s = change("links/" + link_id, "PUT", {"kind": "Contradicts", "rationale": rationale})
        revised = s
        step("new-application-revises-existing-link", container=second_container, oldReceiptReplayed=True, cookieSurvived=True, version=s["version"], link=s["links"][0])

        command("stop", db)
        try:
            live, ready_status, business = call("/health/live"), call("/health/ready"), call(path)
            step("real-database-outage-observed", liveness=live[0], readiness=ready_status[0], businessStatus=business[0], problem=business[1], traceId=business[2])
            assert (live[0], ready_status[0], business[0]) == (200, 503, 503)
            assert business[2] and business[1]["traceId"] == business[2]
            step("real-database-outage-diagnosed", liveness=live[0], readiness=ready_status[0], businessStatus=business[0], problem=business[1], traceId=business[2])
            command("logs", app, log="application-outage.txt")
        finally:
            command("start", db)
        ready()
        assert ok(path)["version"] == revised["version"]
        step("database-recovered-with-state-intact", version=revised["version"])

        rollback_container = start(old_image)
        s = ok(path)
        s = change("notes", "PUT", {"notes": "回退旧应用后的写入；新关联解释必须完整保留"})
        stored = json.loads(sql(f'''SELECT json_build_object('id',"Id",'kind',"Kind",'rationale',"Rationale",'revisedAt',"RevisedAt") FROM "Links" WHERE "Id"='{link_id}'::uuid'''))
        assert stored["rationale"] == rationale and stored["id"] == link_id
        assert stored["kind"] == "Contradicts" and stored["revisedAt"] is not None
        step("application-rollback-keeps-forward-schema-and-new-data", container=rollback_container, version=s["version"], storedRevision=stored)

        final_container = start(new_image)
        s = ok(path)
        assert s["links"][0]["rationale"] == rationale
        assert s["links"][0]["id"] == link_id
        assert s["notes"] == "回退旧应用后的写入；新关联解释必须完整保留"
        assert ok("/api/cases")[0]["id"] == "harbor-01"
        assert any(x["id"] == s["id"] for x in ok("/api/investigations"))
        s = change("state/review")
        s = change("verdict", body={"suspect": "林澈", "reasoning": "门禁、领用册与调度消息已核对，关联矛盾有明确解释，提交可复查的调查结论。", "supportingEvidence": ["access-log", "badge-ledger", "dispatch"]})
        final = ok(path)
        assert final["verdict"]["score"] == 100 and final["status"] == "Submitted"
        assert int(sql(f'''SELECT count(*) FROM "Audit" WHERE "InvestigationId"='{s["id"]}'::uuid AND "Operation"='revise-link' ''')) == 1
        step("roll-forward-and-five-module-functional-verification", container=final_container, version=s["version"], score=100, status=final["status"], revisionAuditCount=1)
        result["status"] = "VERIFIED"
        result["finalSession"] = final
        result["limits"] = "Single-host loopback HTTP lab, Development cookie policy, no TLS/load/HA/Azure; forward-compatible app rollback only. Down migration intentionally not executed because it drops new columns."
    except Exception as e:
        result["status"] = "FAILED"
        result["error"] = f"{type(e).__name__}: {e}"
        raise
    finally:
        if app in owned_containers:
            command("logs", app, check=False, log="application-final.txt")
        cleanup = []
        for resource in sorted(owned_containers):
            cleanup.append({"type": "container", "name": resource, "exitCode": command("rm", "-f", resource, check=False).returncode})
        for resource in sorted(owned_volumes):
            cleanup.append({"type": "volume", "name": resource, "exitCode": command("volume", "rm", resource, check=False).returncode})
        for resource in sorted(owned_networks):
            cleanup.append({"type": "network", "name": resource, "exitCode": command("network", "rm", resource, check=False).returncode})
        result["cleanup"] = cleanup
        result["finishedAtUtc"] = datetime.now(timezone.utc).isoformat()
        if any(x["exitCode"] for x in cleanup):
            result["status"] = "CLEANUP_FAILED"
        (out / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        base.mkdir(parents=True, exist_ok=True)
        (base / "latest.json").write_text(json.dumps({"runId": run_id, "status": result["status"], "result": (out / "results.json").relative_to(ROOT).as_posix()}, indent=2), encoding="utf-8")
        print(json.dumps({"status": result["status"], "evidence": str(out)}, ensure_ascii=False), flush=True)
    if result["status"] != "VERIFIED":
        raise RuntimeError("Lifecycle or cleanup did not pass")


if __name__ == "__main__":
    main()
