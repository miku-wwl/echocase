"""Semantic acceptance gate for executed Phase 2A evidence, not test counts."""
import argparse
import json
import math
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "f7e0cadb1a1c78d73aff011298a4b2eae84af9d4"


def verify(directory, expected_commit=None, frozen=True):
    errors = []
    def require(condition, message):
        if not condition:
            errors.append(message)
    def read(name):
        return json.loads((directory / name).read_text(encoding="utf-8"))
    try:
        trx = ET.parse(directory / "backend/backend.trx")
        results = {r.attrib["testName"]: r.attrib["outcome"] for r in trx.iter() if r.tag.endswith("}UnitTestResult")}
        require(bool(results) and set(results.values()) == {"Passed"}, "Backend run must have only passed results")
        for name in ("RevisionIsAtomicReplayableAndBoundToBothOwnerAndInvestigation", "StoredPhaseOneLinkReceiptCanBeReplayedAfterContractExpansion", "TwoLoadedAggregateRevisionsRaceAtDatabaseAndRollbackTheLosingReceiptAndChild", "UpgradePreservesExistingInvestigationAndEfRejectsStaleTrackedWriter", "FullWorkflowSurvivesFreshReadAndSubmissionIsImmutable", "CoreHasNoFrameworkOrOutwardDependencies"):
            require(results.get(name) == "Passed", "Required behavior absent: " + name)
        browser = read("browser/results.json")
        stats = browser["stats"]
        require(stats["unexpected"] == stats["flaky"] == stats["skipped"] == 0, "Browser run has failures, flaky results or skipped scenarios")
        specs = [spec for suite in browser["suites"] for spec in suite.get("specs", [])]
        for phrase in ("draft typed", "dirty draft", "committed write", "unreadable success body", "revise an existing link", "five business modules", "injected 503", "two windows", "mobile viewport"):
            require(any(phrase in s["title"] and s["ok"] for s in specs), "Browser scenario absent: " + phrase)
        inflight = read("browser/inflight-draft.json")
        require(inflight["draft"] != inflight["server"]["notes"], "In-flight editing observation must preserve newer input")
        lost = read("browser/lost-response.json")
        require(len(lost["attempts"]) == 2 and lost["attempts"][0] == lost["attempts"][1], "Unknown outcome retry changed key, version or body")
        require(lost["final"]["version"] == lost["later"]["version"] > lost["committed"]["version"], "Replay must not write a new version")
        require(all(v >= lost["later"]["version"] for v in lost["observedVersions"]), "Old receipt regressed the visible version")
        unreadable = read("browser/unreadable-body.json")
        require(len(unreadable["attempts"]) == 2 and unreadable["attempts"][0] == unreadable["attempts"][1] and unreadable["committed"]["version"] == unreadable["final"]["version"], "Unreadable successful response lost the original operation intent")
        revision = read("browser/link-revision.json")
        require(revision["after"]["links"][0]["id"] == revision["before"]["links"][0]["id"] and revision["after"]["version"] == revision["before"]["version"] + 1, "Revision replaced identity or advanced an incorrect version")
        race = read("database/store-race.json")
        require(sorted(race["results"]) == [200, 412] and race["survivingReceipts"] == race["survivingRevisionAudit"] == 1, "Database race is not atomic")
        require(set(race["isolation"]) == {"ReadCommitted"}, "Isolation observation missing")
        migration = read("database/migration-tracking.json")
        require(all(x["State"] == "Unchanged" for x in migration["beforeDetect"]), "Tracking baseline missing")
        require(any('UPDATE "Investigations"' in sql and 'AND "Version" =' in sql for sql in migration["commands"]), "Actual SQL concurrency predicate missing")
        require(migration["legacyRationale"] is None and migration["savedVersion"] == migration["originalVersion"] + 1, "Migration/legacy data observation invalid")
        precision = read("database/timestamp-precision.json")
        require(precision["responseTicks"] == precision["readTicks"], "Response/database timestamp mismatch")
        probe = read("database/application-query-plan.json")
        require('FROM "Investigations"' in probe["sql"] and '"OwnerId"' in probe["sql"] and "LIMIT" in probe["sql"] and probe["returnedInvestigations"] == 50, "Probe is not the actual bounded application query")
        for arm in ("withoutComposite", "ownerOnly", "withComposite"):
            require(len(probe[arm]["executionMs"]) >= 3 and all(math.isfinite(v) and v > 0 for v in probe[arm]["executionMs"]), "Invalid finite measurements: " + arm)
        require("IX_Investigations_OwnerId_UpdatedAt" in json.dumps(probe["withComposite"]["representativePlan"]), "Actual composite-index plan absent")
        latest = read("delivery/latest.json")
        run_id = latest["runId"]
        if not re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{8}", run_id):
            raise ValueError("Invalid delivery run identifier")
        delivery = read(f"delivery/{run_id}/results.json")
        require(latest["status"] == delivery["status"] == "VERIFIED", "Delivery did not pass")
        require(delivery["oldSourceCommit"] == BASELINE and delivery["oldImage"]["id"] != delivery["newImage"]["id"], "Old/new provenance invalid")
        require(bool(delivery["cleanup"]) and all(x["exitCode"] == 0 for x in delivery["cleanup"]), "Owned resource cleanup incomplete")
        steps = {s["name"]: s for s in delivery["steps"]}
        for name in ("schema-expanded-old-application-still-writes", "new-application-revises-existing-link", "database-recovered-with-state-intact", "application-rollback-keeps-forward-schema-and-new-data", "roll-forward-and-five-module-functional-verification"):
            require(name in steps, "Delivery stage missing: " + name)
        outage = steps["real-database-outage-diagnosed"]
        require((outage["liveness"], outage["readiness"], outage["businessStatus"]) == (200, 503, 503) and outage["problem"]["traceId"] == outage["traceId"], "Outage diagnosis/correlation invalid")
        if expected_commit:
            require(delivery["sourceCommit"] == expected_commit and not delivery["workingTreeDirty"], "Fresh OCI source is not the reviewed clean commit")
        if frozen:
            proc = subprocess.run(["git", "diff", "--exit-code", BASELINE, "--", "evidence", ":(exclude)evidence/phase2a", "manual/dist"], cwd=ROOT, capture_output=True)
            require(proc.returncode == 0, "Phase 1 evidence or PDFs were modified")
    except Exception as e:
        errors.append(type(e).__name__ + ": " + str(e))
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, default=ROOT / "evidence/phase2a")
    parser.add_argument("--expected-commit")
    args = parser.parse_args()
    errors = verify(args.evidence_root, args.expected_commit)
    print(json.dumps({"status": "FAIL" if errors else "PASS", "failures": errors}, indent=2))
    raise SystemExit(bool(errors))
