"""Small edition context shared by publication, verification and rendering.

The application revision is always a Git object, never the moving main branch.
Historical rebuilding reads the historical Git source; new editions may also
require the current engineering worktree to match the selected revision.
"""
from pathlib import Path
import argparse, hashlib, json, sys

MANUAL = Path(__file__).resolve().parents[1]
ROOT = MANUAL.parent
HISTORICAL_PDF = MANUAL/'dist/Enterprise-Full-Stack-Engineering.pdf'
HISTORICAL_SHA = 'dd00cbfb1cfeb58cea6f28e13c6ea0dd6d72df68bc4668ba6016f1c8edf66166'
DEFAULT = MANUAL/'editions/template-first/book.json'

def load(manifest=None):
    if manifest is None:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--manifest')
        manifest = parser.parse_known_args()[0].manifest
    path = Path(manifest) if manifest else DEFAULT
    if not path.is_absolute():
        path = (ROOT/path) if (ROOT/path).is_file() else (MANUAL/path)
    path = path.resolve()
    if not path.is_relative_to(MANUAL):
        raise ValueError('Publication manifest must be inside manual/')
    config = json.loads(path.read_text(encoding='utf-8-sig'))
    config['manifestPath'] = str(path.relative_to(MANUAL)).replace('\\','/')
    config.setdefault('id', 'historical')
    config.setdefault('chapterRoot', 'chapters')
    config.setdefault('figureCatalog', 'figures/catalog.json')
    config.setdefault('buildDirectory', 'build/historical')
    config.setdefault('output', 'build/historical/Enterprise-Full-Stack-Engineering-Rebuilt.pdf')
    config.setdefault('verifyWorkingTree', False)
    config.setdefault('invariantPdf', False)
    return config

def protected_history():
    actual = hashlib.sha256(HISTORICAL_PDF.read_bytes()).hexdigest()
    if actual != HISTORICAL_SHA:
        raise ValueError('The preserved historical PDF changed')
    return actual

def output_path(config, override=None):
    path = Path(override) if override else MANUAL/config['output']
    if not path.is_absolute(): path = ROOT/path
    path = path.resolve()
    if path == HISTORICAL_PDF.resolve():
        raise ValueError('Historical PDF is immutable; choose a distinct rebuild output')
    return path

def specifications(config):
    if not config.get('sourceSelections'): return None
    return json.loads((MANUAL/config['sourceSelections']).read_text(encoding='utf-8'))
