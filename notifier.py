import smtplib
import requests as _req
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ── Telegram ────────────────────────────────────────────────────────────────

def send_telegram(bot_token: str, chat_id: str, job_text: str, url: str, site_name: str,
                   experience: str = "", job_link: str = "") -> bool:
    """Send an instant Telegram message. Returns True on success."""
    if not bot_token or not chat_id:
        return False

    apply_url = job_link or url
    exp_line = f"📊 *Exp:* {experience}\n" if experience and experience != "Not specified" else ""

    msg = (
        f"🚨 *New Job Alert!*\n\n"
        f"🏢 *Company:* {site_name}\n"
        f"💼 *Role:* {job_text}\n"
        f"{exp_line}\n"
        f"🔗 [Apply / View Job]({apply_url})\n"
        f"🌐 [Careers Page]({url})"
    )
    try:
        r = _req.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        return r.status_code == 200
    except Exception as e:
        print(f"[Telegram error] {e}")
        return False


def test_telegram(bot_token: str, chat_id: str) -> tuple[bool, str]:
    """Send a test message. Returns (success, message)."""
    if not bot_token or not chat_id:
        return False, "Bot token or Chat ID missing."
    try:
        r = _req.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": (
                    "✅ *Job Watcher connected!*\n\n"
                    "You'll receive instant alerts here whenever a new job is posted "
                    "on your watched career pages."
                ),
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        data = r.json()
        if r.status_code == 200:
            return True, "Test message sent!"
        return False, data.get("description", "Unknown error")
    except Exception as e:
        return False, str(e)


# ── Gmail ────────────────────────────────────────────────────────────────────

def send_email(gmail_user: str, gmail_pass: str, to_email: str,
               job_text: str, url: str, site_name: str) -> bool:
    if not gmail_user or not gmail_pass or not to_email:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🆕 New Job Alert — {site_name}"
        msg["From"] = f"Job Watcher <{gmail_user}>"
        msg["To"] = to_email

        html = f"""
<html><body style="margin:0;padding:0;background:#060a14;font-family:'Segoe UI',sans-serif">
  <div style="max-width:560px;margin:40px auto;background:#0d1526;border-radius:16px;
              overflow:hidden;border:1px solid #1e3055">
    <div style="background:linear-gradient(135deg,#00d4ff,#0099cc);padding:28px 32px">
      <h1 style="margin:0;color:#000;font-size:22px;font-weight:800">🔭 Job Watcher</h1>
      <p style="margin:4px 0 0;color:#003344;font-size:13px">New posting detected</p>
    </div>
    <div style="padding:28px 32px">
      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 6px">Company / Site</p>
      <p style="color:#94a3b8;font-size:15px;margin:0 0 24px">{site_name}</p>

      <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 6px">Role Detected</p>
      <div style="background:#131f35;border:1px solid #1e3055;border-left:3px solid #00d4ff;
                  padding:14px 18px;border-radius:8px;margin-bottom:28px">
        <p style="color:#e2e8f0;font-size:17px;font-weight:600;margin:0">{job_text}</p>
      </div>

      <a href="{url}" style="display:inline-block;background:linear-gradient(135deg,#00d4ff,#0099cc);
         color:#000;padding:13px 28px;border-radius:8px;text-decoration:none;
         font-weight:700;font-size:14px">View Careers Page →</a>
    </div>
    <div style="padding:16px 32px;border-top:1px solid #1e3055">
      <p style="color:#334155;font-size:11px;margin:0">Sent by Job Watcher · Unsubscribe by removing your email from the dashboard</p>
    </div>
  </div>
</body></html>"""

        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(gmail_user, gmail_pass)
            s.sendmail(gmail_user, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[Gmail error] {e}")
        return False
