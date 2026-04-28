# 🔭 JobWatch Pro

Monitor **unlimited careers pages** and get **instant Telegram + Gmail alerts** the moment a new job is posted.

Built with **Flask** (Python backend) + **React** (Vite frontend).

---

## 🚀 Deploy to Railway (PC can be OFF — 24/7)

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → Deploy from GitHub
3. Select this repo → Railway auto-detects the Dockerfile → click Deploy
4. Open the Railway URL → your dashboard is live **24/7**, even when your PC is off

---

## 🐳 Run with Docker (Local)

```bash
docker-compose up -d        # start in background
docker-compose logs -f      # view logs
docker-compose down         # stop
```

Open: **http://localhost:5050**

> ⚠️ Docker local = only works while your PC is ON.
> Use Railway for true 24/7 monitoring.

---

## 🐍 Run with Python (No Docker)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Build the React frontend
cd frontend && npm install && npm run build && cd ..

# 3. Start the server
python app.py
```

Open: **http://localhost:5050**

---

## ⚙️ Dashboard Setup

### Step 1 — Add careers pages
- Enter company name + careers URL → click **＋ Add**
- Add as many as you want — no limit

### Step 2 — Set up Telegram (instant mobile alerts)
1. Open Telegram → search **@BotFather** → `/newbot` → copy the token
2. Search **@userinfobot** → send any message → copy your Chat ID
3. Paste both in the Telegram section → **Save & Test**
4. You'll get a test ping on your phone in ~3 seconds ✅

### Step 3 — Set up Gmail (optional backup alerts)
1. Go to https://myaccount.google.com/apppasswords
2. Generate a 16-char App Password for "Mail"
3. Enter your Gmail, App Password, and recipient email
4. Click **Save Gmail**

### Step 4 — Set poll interval
- Default: every **5 minutes**
- Can go down to **1 minute** for fastest detection

---

## 📱 How fast are alerts?

| Step | Time |
|---|---|
| New job posted on careers page | 0s |
| Watcher detects it (max delay) | 1–5 min |
| Telegram message on your phone | ~3–5 sec after detection |
| Gmail arrives | ~30–60 sec after detection |

---

## 🏗 Architecture

```
Railway / Docker (24/7)
    │
    ├─ Flask API Server (backend)
    │   ├─ /api/config, /api/sites, /api/log, /api/status
    │   └─ Background Watcher Thread
    │         │  every N minutes
    │         ├─ Fetch HTML of each careers page
    │         ├─ Parse job titles with BeautifulSoup
    │         ├─ Compare with fingerprinted hashes
    │         └─ New job found?
    │                ├─ Telegram Bot API → instant phone alert
    │                └─ Gmail SMTP → email backup
    │
    └─ React SPA Dashboard (frontend)
        ├─ Add/remove/toggle career page URLs
        ├─ Configure Telegram + Gmail
        ├─ Live alert log
        └─ Real-time stats (auto-refresh every 12s)
```

---

## 📁 Files

| File | Purpose |
|---|---|
| `app.py` | Flask API + watcher thread |
| `scraper.py` | HTML fetcher + job title parser |
| `notifier.py` | Telegram + Gmail sender |
| `frontend/` | React (Vite) dashboard source |
| `static/` | Built React output (served by Flask) |
| `Dockerfile` | Multi-stage container (Node build → Python runtime) |
| `docker-compose.yml` | Local Docker setup |
| `railway.toml` | Railway deploy config |
| `data.json` | Auto-created: config + seen jobs + log (gitignored) |
