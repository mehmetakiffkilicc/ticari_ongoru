"""Web entry point: default to an isolated presentation dataset, never the originals."""
import json
import os
import sys
from pathlib import Path
from analysis import engine


def dispatch(payload):
    base = Path(os.environ.get('DATA_DIR', Path(__file__).resolve().parents[1] / 'data')).resolve()
    if os.environ.get('APP_DATA_MODE') == 'original':
        engine.ROOT = base
    else:
        engine.ROOT = base / 'anonymous'
        if payload.get('action') in {'inspect', 'analyze', 'commit'}:
            raise ValueError('Anonim sunumda dosya aktarımı kapalı. Asıl veriler korunuyor.')
    return engine.main(payload)


if __name__ == '__main__':
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(json.dumps({'ok': True, 'data': dispatch(json.load(sys.stdin))}, ensure_ascii=False))
    except Exception:
        # Original filenames, identities and paths must not appear in error responses.
        print(json.dumps({'ok': False, 'error': 'İşlem tamamlanamadı. Anonim sunumda dosya aktarımı kapalıdır.'}, ensure_ascii=False))
