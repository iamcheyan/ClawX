#!/usr/bin/env python3
import json
import os
import requests
import subprocess
import concurrent.futures
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path (resolve real path to handle symlinks correctly)
script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_dir, '..'))
from core.utils_security import load_config, resolve_path

# Load Project Config
SEC_CONFIG = load_config()

# ANSI Color Codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Resolve Paths
CONFIG_PATH = resolve_path(SEC_CONFIG["paths"].get("openclaw_config", "~/.openclaw/openclaw.json"))
OUTPUT_DIR = resolve_path(SEC_CONFIG["paths"].get("output_dir", "./docs"))
STATUS_FILE = "model-status.html"
JSON_FILE = "model-status.json"
REPORT_HTML = OUTPUT_DIR / STATUS_FILE
REPORT_JSON = OUTPUT_DIR / JSON_FILE
AUTO_PUSH = os.environ.get("CLAWX_AUTO_PUSH", "1") == "1"

def test_opencode_cli(model_id):
    try:
        start = datetime.now()
        cmd = ["opencode", "run", "--model", model_id]
        result = subprocess.run(cmd, input="hi", capture_output=True, text=True, timeout=30)
        latency = (datetime.now() - start).total_seconds()
        if result.returncode == 0:
            return True, f"OK (CLI {latency:.2f}s)", result.stdout.strip().replace('\n', ' ')[:50]
        else:
            return False, f"CLI Err {result.returncode}", result.stderr[:100]
    except Exception as e:
        return False, "CLI Err", str(e)[:100]

def test_openai_compatible(name, base_url, api_key, model_id):
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key and api_key not in ["qwen-oauth", ""]:
        headers["Authorization"] = f"Bearer {api_key}"
    
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 10
    }
    
    try:
        start = datetime.now()
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        latency = (datetime.now() - start).total_seconds()
        
        if response.status_code == 200:
            res_json = response.json()
            if 'choices' in res_json and len(res_json['choices']) > 0:
                content = res_json['choices'][0]['message']['content'].strip().replace('\n', ' ')
                return True, f"OK ({latency:.2f}s)", content[:50]
            return False, "Empty Error", "No choices in JSON"
        else:
            return False, f"Err {response.status_code}", response.text[:60].replace('\n', ' ')
    except Exception as e:
        return False, "HTTP Timeout", str(e)[:60]

def test_google_gemini(name, api_key, model_id="gemini-2.5-flash"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": "hi"}]}],
        "generationConfig": {"maxOutputTokens": 10}
    }
    
    try:
        start = datetime.now()
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        latency = (datetime.now() - start).total_seconds()
        
        if response.status_code == 200:
            result = response.json()
            try:
                content = result['candidates'][0]['content']['parts'][0]['text'].strip()
                return True, f"OK ({latency:.2f}s)", content[:50]
            except (KeyError, IndexError):
                return True, f"OK ({latency:.2f}s)", "Response matched but unexpected format"
        else:
            return False, f"Err {response.status_code}", response.text[:60]
    except Exception as e:
        return False, "HTTP Timeout", str(e)[:60]

def test_via_openclaw_spawn(model_id):
    """Use OpenClaw sessions spawn for quick verification (Fallback)"""
    try:
        start = datetime.now()
        cmd = [
            "openclaw", "sessions", "spawn",
            "--agent", "main",
            "--model", model_id,
            "--run-timeout", "20",
            "--cleanup", "delete",
            "--task", "Reply 'TEST_OK' and stop."
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=50)
        latency = (datetime.now() - start).total_seconds()
        
        if result.returncode == 0:
            if "completed successfully" in result.stdout.lower() or "test_ok" in result.stdout.lower():
                return True, f"OK (Spawn {latency:.1f}s)", "Spawn accepted"
            return True, f"OK (Spawn {latency:.1f}s)", "CLI responded"
        else:
            err = (result.stderr + result.stdout).lower()
            if "not allowed" in err:
                return False, "Not Allowed", "Model not in config"
            elif "401" in err or "auth" in err:
                return False, "Auth Failed", "API key rejected"
            return False, "Spawn Error", (result.stderr[:60] or "Unknown error").replace('\n', ' ')
    except subprocess.TimeoutExpired:
        return False, "Spawn Timeout", "Took too long (>50s)"
    except Exception as e:
        return False, "Spawn CLI Err", str(e)[:60]

def check_provider(p_name, p_config):
    results = []
    models_to_test = p_config.get('models', [])[:2]
    
    if not models_to_test:
        if p_name == 'google' or p_name == 'google-alt':
            models_to_test = [{"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"}]
        elif p_name == 'nvidia':
            models_to_test = [{"id": "qwen/qwen2.5-coder-32b-instruct", "name": "NVIDIA Qwen"}]
            
    for m in models_to_test:
        name = f"{p_name}/{m['id']}"
        api_type = p_config.get('api', '')
        base_url = p_config.get('baseUrl', '')
        api_key = p_config.get('apiKey', '')
        
        success, status, msg = False, "Unknown", ""
        
        if api_type == 'google-generative-ai' or 'google' in p_name:
            success, status, msg = test_google_gemini(name, api_key, m['id'])
            
        elif api_type == 'openai-completions' and base_url and api_key and api_key != 'qwen-oauth':
            # Try fast direct HTTP first
            success, status, msg = test_openai_compatible(name, base_url, api_key, m['id'])
            # If HTTP fails, ALWAYS fallback to SPAWN as it might have custom mapping/auth
            if not success:
                fallback_success, fallback_status, fallback_msg = test_via_openclaw_spawn(f"{p_name}/{m['id']}")
                if fallback_success:
                    success, status, msg = fallback_success, fallback_status, fallback_msg
        
        elif api_key == 'qwen-oauth':
            success, status, msg = True, "OAUTH MODE", "Managed by OpenClaw"
            
        else:
            # All other cases (opencode local, custom plugins, etc.)
            success, status, msg = test_via_openclaw_spawn(f"{p_name}/{m['id']}")
            
        results.append({
            "provider": p_name,
            "model": m['id'],
            "success": success,
            "status": status,
            "response": msg
        })
    return results

def _safe_snippet(text, limit=160):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    return text[:limit]

def _truncate(text, limit):
    if not text:
        return ""
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[:limit - 3] + "..."

def print_terminal_report(payload):
    results = payload.get("results", [])
    if not results:
        print("No results.")
        return

    provider_w = max(len("PROVIDER"), max(len(r["provider"]) for r in results))
    model_w = max(len("MODEL"), max(len(r["model"]) for r in results))
    status_w = max(len("STATUS"), max(len(r["status"]) for r in results))
    max_resp = max(len(r.get("response", "")) for r in results)
    response_w = max(len("RESPONSE"), min(80, max_resp))

    sep = "  "
    header = f"{'PROVIDER':<{provider_w}}{sep}{'MODEL':<{model_w}}{sep}{'STATUS':<{status_w}}{sep}{'RESPONSE':<{response_w}}"
    line = "-" * len(header)

    print(line)
    print(header)
    print(line)

    for r in results:
        status_raw = r["status"]
        status_padded = f"{status_raw:<{status_w}}"
        status_colored = f"{GREEN}{status_padded}{RESET}" if r["success"] else f"{RED}{status_padded}{RESET}"
        response = _truncate(r.get("response", ""), response_w)
        print(
            f"{r['provider']:<{provider_w}}{sep}"
            f"{r['model']:<{model_w}}{sep}"
            f"{status_colored}{sep}"
            f"{response:<{response_w}}"
        )

    summary = payload.get("summary", {})
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    print("\nSummary: "
          f"{GREEN}{passed} PASSED{RESET}, "
          f"{RED}{failed} FAILED{RESET}")

def auto_push_report():
    if not AUTO_PUSH:
        return

    repo_root = Path(__file__).resolve().parent.parent
    paths = []
    try:
        paths.append(REPORT_HTML.resolve().relative_to(repo_root))
    except Exception:
        paths.append(REPORT_HTML)
    try:
        paths.append(REPORT_JSON.resolve().relative_to(repo_root))
    except Exception:
        paths.append(REPORT_JSON)

    def _run(cmd):
        return subprocess.run(cmd, capture_output=True, text=True)

    # Check changes on report files
    status = _run(["git", "-C", str(repo_root), "status", "--porcelain", "--"] + [str(p) for p in paths])
    if status.returncode != 0:
        print(f"{YELLOW}⚠️ Git status failed: {status.stderr.strip()}{RESET}")
        return
    if not status.stdout.strip():
        print("No report changes to push.")
        return

    # Force add because dist/ might be ignored
    _run(["git", "-C", str(repo_root), "add", "-f"] + [str(p) for p in paths])
    msg = f"Model status update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    commit = _run(["git", "-C", str(repo_root), "commit", "-m", msg])
    if commit.returncode != 0:
        if commit.stderr.strip():
            print(f"{YELLOW}⚠️ Git commit skipped: {commit.stderr.strip()}{RESET}")
        return

    push = _run(["git", "-C", str(repo_root), "push"])
    if push.returncode != 0:
        print(f"{YELLOW}⚠️ Git push failed: {push.stderr.strip()}{RESET}")
    else:
        print("✅ Pushed model status report.")

def build_report_payload(all_results):
    passed = sum(1 for r in all_results if r["success"])
    failed = len(all_results) - passed
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "generated_at": now_str,
        "summary": {
            "passed": passed,
            "failed": failed,
            "total": len(all_results)
        },
        "results": [
            {
                "provider": r["provider"],
                "model": r["model"],
                "success": r["success"],
                "status": r["status"],
                "response": _safe_snippet(r.get("response", ""))
            }
            for r in all_results
        ]
    }

def write_html_report(payload):
    status = payload["summary"]
    rows = []
    for r in payload["results"]:
        badge = "ok" if r["success"] else "fail"
        rows.append(
            f"<tr>"
            f"<td>{r['provider']}</td>"
            f"<td>{r['model']}</td>"
            f"<td><span class='badge {badge}'>{'OK' if r['success'] else 'FAIL'}</span></td>"
            f"<td>{r['status']}</td>"
            f"<td class='muted'>{r['response']}</td>"
            f"</tr>"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Digital Physiology Limit</title>
  <link rel="icon" href="./favicon.png">
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #0f1115;
      --card: #151923;
      --text: #e8eaf0;
      --muted: #a4acc4;
      --ok: #2ecc71;
      --fail: #ff5c5c;
      --warn: #f1c40f;
      --border: #27304a;
    }}
    body {{
      margin: 0;
      padding: 24px;
      font-family: "Inter", "Noto Sans", system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    .wrap {{
        max-width: 900px;
        margin: 0 auto;
    }}
    .back-link {{
        text-decoration: none;
        color: var(--muted);
        font-size: 0.9em;
        margin-bottom: 20px;
        display: block;
    }}
    .back-link:hover {{ color: var(--text); }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    }}
    h1 {{
      margin: 0 0 8px 0;
      font-size: 22px;
    }}
    .meta {{
      color: var(--muted);
      margin-bottom: 16px;
      font-size: 0.9em;
    }}
    .summary {{
      display: flex;
      gap: 16px;
      margin-bottom: 24px;
    }}
    .summary .pill {{
      padding: 6px 12px;
      border-radius: 999px;
      background: #1b2233;
      border: 1px solid var(--border);
      font-size: 13px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 12px 10px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-weight: 600;
    }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .badge.ok {{ background: rgba(46, 204, 113, 0.1); color: var(--ok); border: 1px solid rgba(46, 204, 113, 0.2); }}
    .badge.fail {{ background: rgba(255, 92, 92, 0.1); color: var(--fail); border: 1px solid rgba(255, 92, 92, 0.2); }}
    .muted {{ color: var(--muted); font-family: monospace; font-size: 12px; opacity: 0.8; }}
  </style>
</head>
<body>
  <div class="wrap">
    <a href="./index.html" class="back-link">← Back to Consciousness Stream</a>
    <div class="card">
      <h1>🫀 Digital Physiology Report</h1>
      <div class="meta">Generated at: {payload['generated_at']}</div>
      <div class="summary">
        <div class="pill">Cortex Nodes: {status['total']}</div>
        <div class="pill" style="color: var(--ok)">Active: {status['passed']}</div>
        <div class="pill" style="color: var(--fail)">Dead: {status['failed']}</div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Provider</th>
            <th>Model</th>
            <th>Status</th>
            <th>Latency/Error</th>
            <th>Snippet</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""
    REPORT_HTML.write_text(html, encoding="utf-8")
    print(f"HTML report saved to: {REPORT_HTML}")

def main():
    if not os.path.exists(CONFIG_PATH):
        print(f"{RED}Config file not found at {CONFIG_PATH}{RESET}")
        return

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    providers = config.get('models', {}).get('providers', {})
    
    print(f"\n{BLUE}🚀 Claw Model Status Checker v2.0{RESET}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)

    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_p = {executor.submit(check_provider, name, cfg): name for name, cfg in providers.items()}
        for future in concurrent.futures.as_completed(future_to_p):
            all_results.extend(future.result())

    all_results.sort(key=lambda r: (not r["success"], r["provider"], r["model"]))
    payload = build_report_payload(all_results)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print_terminal_report(payload)
    write_html_report(payload)

    # Also save JSON for frontend
    with open(REPORT_JSON, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f"JSON report saved to: {REPORT_JSON}")

    auto_push_report()

if __name__ == "__main__":
    main()
