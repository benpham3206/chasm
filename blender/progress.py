"""Persist coordinator progress after each completed build/render step."""
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent

def record(what, next_step, files, status='WORKING'):
    stamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    with (HERE / 'PROGRESS.md').open('a', encoding='utf8') as fp:
        fp.write(f'- [{stamp}] {status} (Sol) {what} | next: {next_step} | files: {files}\n')
    text = (f'# Rev3 {status.lower()} (Sol)\n\nDone: {what}\n\n'
            f'Half-done: {next_step}\n\nFiles: {files}\n\n'
            'Exact render commands: Blender -b --factory-startup --python-exit-code 1 '
            '--python blender/render_shots.py -- --draft; use --preview --shots 1,4 for previews.\n\n'
            'Open: inspect every delivered PNG; no git or finals; deletions only recycle.py.\n')
    temp = HERE / 'tmp' / 'NEXT_rev3.tmp'
    temp.write_text(text, encoding='utf8')
    temp.replace(HERE / 'NEXT.md')
