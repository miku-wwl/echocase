"""Controlled evidence corruptions; the committed observations are never changed."""
import argparse
import json
import shutil
import tempfile
from pathlib import Path
from verify_phase2a import ROOT, verify

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=ROOT / "evidence/phase2a/qa/gate-selftest.json")
args = parser.parse_args()
scratch = ROOT / "work"
scratch.mkdir(exist_ok=True)
observed = []
with tempfile.TemporaryDirectory(prefix="phase2a-gate-", dir=scratch) as temp:
    fixture = Path(temp).resolve()
    assert fixture.is_relative_to(scratch.resolve())
    source = ROOT / "evidence/phase2a"
    for path in source.rglob("*"):
        if path.is_file() and path.suffix in (".json", ".trx") and "fresh" not in path.parts:
            target = fixture / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    assert not verify(fixture, frozen=False), "Unmodified fixture must pass"
    latest = json.loads((fixture / "delivery/latest.json").read_text())
    cases = [
        ("changed retry key", "browser/lost-response.json", "Unknown outcome retry", lambda x: x["attempts"][1].update(key="different-intent")),
        ("missing actual Version predicate", "database/migration-tracking.json", "Actual SQL concurrency", lambda x: x.update(commands=["SELECT 1"])),
        ("non-finite measurement", "database/application-query-plan.json", "Invalid finite measurements", lambda x: x["withComposite"]["executionMs"].__setitem__(0, float("nan"))),
        ("omitted rollback", f"delivery/{latest['runId']}/results.json", "Delivery stage missing", lambda x: x.update(steps=[s for s in x["steps"] if s["name"] != "application-rollback-keeps-forward-schema-and-new-data"])),
    ]
    for name, relative, expected, corrupt in cases:
        path = fixture / relative
        original = path.read_bytes()
        data = json.loads(original)
        corrupt(data)
        path.write_text(json.dumps(data), encoding="utf-8")
        errors = verify(fixture, frozen=False)
        assert any(expected in e for e in errors), (name, errors)
        observed.append({"case": name, "rejected": True, "diagnostics": errors})
        path.write_bytes(original)
    assert not verify(fixture, frozen=False), "Restored fixture must pass"
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps({"baseline": "PASS", "restored": "PASS", "cases": observed}, indent=2), encoding="utf-8")
print(json.dumps({"status": "PASS", "rejected": [x["case"] for x in observed]}))
