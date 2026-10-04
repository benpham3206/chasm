"""Human-readable tail of a Codex `exec --json` event log.

    python blender/orchestrator/codex/peek.py luna-01 [N]     # last N steps (default 20)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
name = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
rows = []
for line in open(os.path.join(HERE, f"{name}-events.jsonl"), encoding="utf-8", errors="replace"):
    try:
        e = json.loads(line)
    except ValueError:
        continue
    it = e.get("item") or {}
    kind = it.get("type") or e.get("type")
    if e.get("type") not in ("item.completed", "turn.completed", "turn.failed", "error"):
        continue
    if kind == "command_execution":
        txt = f"$ {it.get('command', '')}  -> exit {it.get('exit_code')}"
    elif kind in ("agent_message", "reasoning"):
        txt = it.get("text", "")
    elif kind == "web_search":
        txt = f"search: {it.get('query', '')}"
    elif kind == "file_change":
        txt = "edit: " + ", ".join(c.get("path", "") for c in it.get("changes", []))
    else:
        txt = json.dumps(e)[:200]
    rows.append(f"[{kind}] " + " ".join(str(txt).split())[:220])
print("\n".join(rows[-n:]) or "(no completed steps yet)")
