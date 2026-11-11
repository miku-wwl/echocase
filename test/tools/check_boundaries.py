"""Check source ownership, evaluated MSBuild items, resolved packages and outputs."""
import argparse
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYERS = {"EchoCase.Domain": set(), "EchoCase.Application": {"EchoCase.Domain"},
          "EchoCase.Infrastructure": {"EchoCase.Application", "EchoCase.Domain"},
          "EchoCase.Api": {"EchoCase.Application", "EchoCase.Infrastructure", "EchoCase.Domain"}}
TEST_PACKAGE = re.compile(r"^(nunit|nunit3testadapter|microsoft\.net\.test\.sdk|microsoft\.testplatform(?:\.|$)|microsoft\.aspnetcore\.mvc\.testing|xunit|coverlet|moq$|nsubstitute$|fluentassertions$)", re.I)
TEST_IMPORT = re.compile(r"^\s*(?:global\s+)?using\b.*(?:NUnit|Xunit|Moq|NSubstitute|EchoCase\.(?:Tests|UnitTests|IntegrationTests))\b", re.M)
JS_IMPORT = re.compile(r"(?:\bfrom\s*|\bimport\s*\(\s*|\brequire\s*\(\s*|\bimport\s*)['\"]([^'\"]+)['\"]")
TEST_MODULE = re.compile(r"(?:^|[/\\])(?:tests?|fixtures|__tests__|test-results|playwright(?:-core)?|vitest)(?:[/\\]|$)|@playwright/|@testing-library/|^node:test(?:/|$)")


def check_layout(root):
    # The policy concerns tracked source, never ignored local user data.
    result = subprocess.run(["git", "-C", str(root), "ls-files", "--full-name"], capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        return ["Cannot inspect tracked repository layout"]
    directories = {p.split("/", 1)[0] for p in result.stdout.splitlines() if "/" in p}
    expected = {"backend", "frontend", "test", "manual", ".github"}
    return [] if directories == expected else ["Tracked top-level directories must be backend/frontend/test/manual plus .github: " + ", ".join(sorted(directories))]


def check(root, evaluated=True, publish=None, dist=None):
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)
    def refs(project):
        tree = ET.parse(project)
        return tree, [(project.parent / e.attrib["Include"]).resolve() for e in tree.iter("ProjectReference")]
    sources = sorted((root / "backend").glob("*/*.csproj"))
    require({p.stem for p in sources} == set(LAYERS), "Expected four application projects")
    for project in sources:
        tree, references = refs(project)
        for target in references:
            require(target.is_relative_to(root / "backend") and target.stem in LAYERS[project.stem], f"Production reference crosses boundary: {project.name} -> {target}")
        require(not any(e.text == "true" for e in tree.iter("IsTestProject")), "Production project is a test project: " + project.name)
        for e in tree.iter("PackageReference"):
            require(not TEST_PACKAGE.search(e.attrib.get("Include", "")), "Test package in production project: " + project.name)
        for e in tree.iter():
            if e.tag in ("Compile", "Content", "None", "Import", "Reference"):
                require(not any(re.search(r"(?:^|[/\\])tests?[/\\]", value, re.I) for value in e.attrib.values()), "Production MSBuild item imports test source: " + project.name)
    for p in (root / "backend").rglob("*.cs"):
        if not {"bin", "obj"} & set(p.parts):
            require(not TEST_IMPORT.search(p.read_text(encoding="utf-8-sig")), "Production C# imports test utilities: " + str(p.relative_to(root)))
    tests = sorted((root / "test").glob("**/*.csproj"))
    require({p.stem for p in tests} == {"EchoCase.UnitTests", "EchoCase.IntegrationTests", "EchoCase.QueryProbe"}, "Independent test project set is incomplete")
    for p in tests:
        _, references = refs(p)
        for target in references:
            require(target.is_relative_to(root / "backend"), "Tests must reference application only: " + str(p.relative_to(root)))
            if p.stem == "EchoCase.UnitTests":
                require(target.stem in {"EchoCase.Domain", "EchoCase.Application"}, "Unit tests depend on database/API implementation")
    for p in (root / "test/unit").rglob("*.cs"):
        if not {"bin", "obj"} & set(p.parts):
            require(not re.search(r"^\s*using\s+(?:Npgsql|Microsoft\.EntityFrameworkCore|Microsoft\.AspNetCore|EchoCase\.(?:Infrastructure|IntegrationTests))\b", p.read_text(encoding="utf-8-sig"), re.M), "Unit tests import integration implementation: " + str(p))
    solution = ET.parse(root / "EchoCase.slnx")
    require(all((root / p.attrib["Path"]).resolve().is_relative_to(root / "backend") for p in solution.iter("Project")), "Application solution includes testing projects")
    for p in (root / "frontend/src").rglob("*"):
        if p.suffix in {".ts", ".tsx", ".js", ".jsx"}:
            require(not any(TEST_MODULE.search(m) for m in JS_IMPORT.findall(p.read_text(encoding="utf-8-sig"))), "Production frontend imports tests: " + str(p.relative_to(root)))
    package = json.loads((root / "frontend/package.json").read_text(encoding="utf-8"))
    for section in ("dependencies", "devDependencies"):
        require(not any(TEST_MODULE.search(p) for p in package.get(section, {})), "Test runner must live in test/e2e, not frontend: " + section)
    for p in (root / "test/e2e/specs").glob("*.ts"):
        require(not any(re.search(r"(?:frontend/src|(?:^|/)(?:backend|src)/)", m) for m in JS_IMPORT.findall(p.read_text(encoding="utf-8-sig"))), "E2E imports internal application source: " + str(p))
    if errors:  # Do not evaluate an invalid project or a controlled negative fixture.
        return errors
    if evaluated:
        for p in sources:
            result = subprocess.run(["dotnet", "msbuild", str(p), "-nologo", "-getItem:ProjectReference,Compile,PackageReference", "-getProperty:IsTestProject"], cwd=root, capture_output=True, text=True, encoding="utf-8")
            require(result.returncode == 0, "MSBuild evaluation failed: " + p.name)
            if result.returncode:
                continue
            graph = json.loads(result.stdout)
            require(graph["Properties"].get("IsTestProject", "").lower() != "true", "Evaluated production project is a test project")
            for item in graph["Items"]["ProjectReference"]:
                target = Path(item["FullPath"]).resolve()
                require(target.is_relative_to(root / "backend") and target.stem in LAYERS[p.stem], "Evaluated production reference crosses layer boundary: " + p.name)
            require(not any(TEST_PACKAGE.search(item["Identity"]) for item in graph["Items"]["PackageReference"]), "Evaluated production package includes test tooling: " + p.name)
            for item in graph["Items"]["Compile"]:
                require(Path(item["FullPath"]).resolve().is_relative_to(root / "backend"), "Evaluated production compilation contains test/outside source: " + p.name)
            assets = p.parent / "obj/project.assets.json"
            require(assets.is_file(), "Restore application dependencies first: " + p.name)
            if assets.exists():
                libraries = json.loads(assets.read_text(encoding="utf-8"))["libraries"]
                require(not any(TEST_PACKAGE.search(n.split("/")[0]) for n in libraries), "Resolved production dependency graph contains test packages: " + p.name)
    if publish:
        require((publish / "EchoCase.Api.dll").exists(), "Application publish output is missing")
        for p in publish.rglob("*.dll"):
            require(not (p.name.lower().endswith("tests.dll") or TEST_PACKAGE.search(p.stem) or p.stem.lower() == "testhost"), "Test assembly in application publish output: " + p.name)
        for p in publish.glob("*.deps.json"):
            require(not any(TEST_PACKAGE.search(n.split("/")[0]) for n in json.loads(p.read_text(encoding="utf-8"))["libraries"]), "Published runtime dependency graph contains tests")
    if dist:
        maps = list(dist.rglob("*.js.map"))
        require(bool(maps), "Build frontend with --sourcemap before checking bundle origins")
        for p in maps:
            require(not any(TEST_MODULE.search(n) for n in json.loads(p.read_text(encoding="utf-8"))["sources"]), "Test source/package in frontend bundle: " + p.name)
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--structure-only", action="store_true")
    parser.add_argument("--publish-dir", type=Path)
    parser.add_argument("--frontend-dist", type=Path)
    args = parser.parse_args()
    try:
        errors = check_layout(args.root.resolve()) + check(args.root.resolve(), not args.structure_only, args.publish_dir, args.frontend_dist)
    except Exception as e:
        errors = [type(e).__name__ + ": " + str(e)]
    print(json.dumps({"status": "FAIL" if errors else "PASS", "failures": errors}, indent=2))
    raise SystemExit(bool(errors))
