# MyMoltbot — AI短剧制作 MVP

## What this MVP does
- Runs a deterministic (rule-based) pipeline per episode:
  - outline → script → shotlist (250 shots / 15min / 6 scenes / 5 video clips) → package (JSONL tasks)
- Provides a simple web UI to generate and inspect episode assets.
- ComfyUI integration is stubbed/reserved (no API calls).

## Run locally (Codespace)
```bash
pip install -r requirements.txt
uvicorn server.app.main:app --host 0.0.0.0 --port 18789
```

Then open the forwarded URL for port 18789.
