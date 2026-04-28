import json
import os
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from scraper import scrape_jobs, fingerprint
from notifier import send_telegram, send_email, test_telegram

# Serve React build from /static
app = Flask(__name__, static_folder="static", static_url_path="")

DATA_FILE = "data.json"
lock = threading.Lock()


# ── Data helpers ─────────────────────────────────────────────────────────────

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {
        "config": {
            "bot_token": "",
            "chat_id": "",
            "gmail_user": "",
            "gmail_pass": "",
            "to_email": "",
            "interval": 5,
        },
        "sites": [],   # list of {id, name, url, enabled, seen: [], last_checked, last_status}
        "log": [],     # list of {time, site_name, url, job}
    }

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def now_str() -> str:
    return datetime.now().strftime("%d %b %Y, %I:%M:%S %p")


# ── Watcher ───────────────────────────────────────────────────────────────────

def check_site(site: dict, config: dict, log: list) -> dict:
    url = site["url"]
    name = site.get("name") or url
    jobs, err = scrape_jobs(url)

    if err:
        site["last_status"] = f"❌ Error: {err[:80]}"
        site["last_checked"] = now_str()
        return site

    seen = set(site.get("seen", []))
    new_jobs = [j for j in jobs if j["id"] not in seen]

    for job in new_jobs:
        seen.add(job["id"])

        # Telegram (instant)
        send_telegram(
            config.get("bot_token", ""),
            config.get("chat_id", ""),
            job["text"], url, name
        )
        # Gmail (backup)
        send_email(
            config.get("gmail_user", ""),
            config.get("gmail_pass", ""),
            config.get("to_email", ""),
            job["text"], url, name
        )
        # Log
        log.insert(0, {
            "time": now_str(),
            "site_name": name,
            "url": url,
            "job": job["text"],
        })

    site["seen"] = list(seen)
    site["last_checked"] = now_str()
    site["last_status"] = (
        f"✅ {len(new_jobs)} new" if new_jobs else f"✅ No change ({len(jobs)} items)"
    )
    return site


def watcher_loop():
    while True:
        with lock:
            data = load_data()
        config = data["config"]
        interval = int(config.get("interval", 5))

        enabled_sites = [s for s in data.get("sites", []) if s.get("enabled", True)]

        if enabled_sites:
            for i, site in enumerate(data["sites"]):
                if not site.get("enabled", True):
                    continue
                data["sites"][i] = check_site(site, config, data["log"])

            data["log"] = data["log"][:100]  # keep last 100

            with lock:
                save_data(data)

        time.sleep(interval * 60)


# ── Routes ────────────────────────────────────────────────────────────────────

# Serve React SPA
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# Config
@app.route("/api/config", methods=["GET"])
def get_config():
    data = load_data()
    cfg = dict(data["config"])
    cfg["has_password"] = bool(cfg.get("gmail_pass"))
    cfg.pop("gmail_pass", None)
    return jsonify(cfg)

@app.route("/api/config", methods=["POST"])
def save_config():
    body = request.json
    with lock:
        data = load_data()
        existing = data.get("config", {})
        if not body.get("gmail_pass") and existing.get("gmail_pass"):
            body["gmail_pass"] = existing["gmail_pass"]
        data["config"] = body
        save_data(data)
    return jsonify({"ok": True})

# Sites (multi-URL)
@app.route("/api/sites", methods=["GET"])
def get_sites():
    data = load_data()
    # Don't expose seen hashes to frontend — only metadata
    sites_meta = [
        {
            "id": s["id"],
            "name": s.get("name", ""),
            "url": s["url"],
            "enabled": s.get("enabled", True),
            "last_checked": s.get("last_checked", "Never"),
            "last_status": s.get("last_status", "Pending"),
            "seen_count": len(s.get("seen", [])),
        }
        for s in data.get("sites", [])
    ]
    return jsonify(sites_meta)

@app.route("/api/sites", methods=["POST"])
def add_site():
    body = request.json
    url = (body.get("url") or "").strip()
    name = (body.get("name") or "").strip()
    if not url:
        return jsonify({"ok": False, "error": "URL required"}), 400
    with lock:
        data = load_data()
        # Avoid duplicates
        if any(s["url"] == url for s in data["sites"]):
            return jsonify({"ok": False, "error": "URL already added"}), 400
        import uuid
        data["sites"].append({
            "id": str(uuid.uuid4())[:8],
            "name": name or url,
            "url": url,
            "enabled": True,
            "seen": [],
            "last_checked": "Never",
            "last_status": "Pending",
        })
        save_data(data)
    return jsonify({"ok": True})

@app.route("/api/sites/<site_id>", methods=["DELETE"])
def delete_site(site_id):
    with lock:
        data = load_data()
        data["sites"] = [s for s in data["sites"] if s["id"] != site_id]
        save_data(data)
    return jsonify({"ok": True})

@app.route("/api/sites/<site_id>/toggle", methods=["POST"])
def toggle_site(site_id):
    with lock:
        data = load_data()
        for s in data["sites"]:
            if s["id"] == site_id:
                s["enabled"] = not s.get("enabled", True)
                break
        save_data(data)
    return jsonify({"ok": True})

@app.route("/api/sites/<site_id>/reset", methods=["POST"])
def reset_site(site_id):
    """Reset seen jobs — forces re-alert on next check."""
    with lock:
        data = load_data()
        for s in data["sites"]:
            if s["id"] == site_id:
                s["seen"] = []
                s["last_status"] = "Reset — will re-scan next cycle"
                break
        save_data(data)
    return jsonify({"ok": True})

# Log
@app.route("/api/log", methods=["GET"])
def get_log():
    data = load_data()
    return jsonify(data.get("log", []))

@app.route("/api/log", methods=["DELETE"])
def clear_log():
    with lock:
        data = load_data()
        data["log"] = []
        save_data(data)
    return jsonify({"ok": True})

# Test
@app.route("/api/test/telegram", methods=["POST"])
def test_tg():
    data = load_data()
    cfg = data["config"]
    ok, msg = test_telegram(cfg.get("bot_token", ""), cfg.get("chat_id", ""))
    return jsonify({"ok": ok, "message": msg})

@app.route("/api/status", methods=["GET"])
def get_status():
    data = load_data()
    sites = data.get("sites", [])
    return jsonify({
        "total_sites": len(sites),
        "active_sites": sum(1 for s in sites if s.get("enabled", True)),
        "total_alerts": len(data.get("log", [])),
        "total_seen": sum(len(s.get("seen", [])) for s in sites),
    })

# Catch-all: serve React SPA for any non-API route
@app.route("/<path:path>")
def catch_all(path):
    # Try to serve static file first (JS, CSS, images)
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_from_directory(app.static_folder, path)
    # Otherwise serve index.html (SPA routing)
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    t = threading.Thread(target=watcher_loop, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
