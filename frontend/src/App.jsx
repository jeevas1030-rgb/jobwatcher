import { useState, useEffect, useCallback, useRef } from 'react'

/* ═══════════════════════════════════════════════════════════════════════════
   JobWatch Pro — React Dashboard
   ═══════════════════════════════════════════════════════════════════════════ */

// ── Helpers ────────────────────────────────────────────────────────────────
function esc(s) {
  return String(s || '')
}

// ── Toast System ───────────────────────────────────────────────────────────
function ToastContainer({ toasts }) {
  return (
    <div className="toast-container" aria-live="polite" aria-atomic="true">
      {toasts.map(t => (
        <div
          key={t.id}
          className={`toast toast--${t.type} ${t.show ? 'toast--show' : ''}`}
        >
          {t.msg}
        </div>
      ))}
    </div>
  )
}

export default function App() {
  // ── State ──────────────────────────────────────────────────────────────
  const [config, setConfig]     = useState({})
  const [sites, setSites]       = useState([])
  const [log, setLog]           = useState([])
  const [status, setStatus]     = useState({ active_sites: 0, total_alerts: 0, total_seen: 0 })
  const [toasts, setToasts]     = useState([])
  const [newName, setNewName]   = useState('')
  const [newUrl, setNewUrl]     = useState('')
  const [botToken, setBotToken] = useState('')
  const [chatId, setChatId]     = useState('')
  const [gmailUser, setGmailUser] = useState('')
  const [gmailPass, setGmailPass] = useState('')
  const [toEmail, setToEmail]   = useState('')
  const [interval, setInterval_] = useState('5')
  const [hasPass, setHasPass]   = useState(false)
  const [tgLoading, setTgLoading] = useState(false)
  const [addLoading, setAddLoading] = useState(false)
  const toastId = useRef(0)

  // ── Toast helper ───────────────────────────────────────────────────────
  const toast = useCallback((msg, type = 'ok', dur = 3500) => {
    const id = ++toastId.current
    setToasts(prev => [...prev, { id, msg, type, show: false }])
    setTimeout(() => setToasts(prev => prev.map(t => t.id === id ? { ...t, show: true } : t)), 20)
    setTimeout(() => setToasts(prev => prev.map(t => t.id === id ? { ...t, show: false } : t)), dur)
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), dur + 300)
  }, [])

  // ── Data Fetchers ──────────────────────────────────────────────────────
  const loadConfig = useCallback(async () => {
    try {
      const r = await fetch('/api/config')
      const c = await r.json()
      setConfig(c)
      if (c.bot_token) setBotToken(c.bot_token)
      if (c.chat_id) setChatId(c.chat_id)
      if (c.gmail_user) setGmailUser(c.gmail_user)
      if (c.to_email) setToEmail(c.to_email)
      if (c.has_password) setHasPass(true)
      if (c.interval) setInterval_(String(c.interval))
    } catch (err) { console.error('Config load failed:', err) }
  }, [])

  const loadSites = useCallback(async () => {
    try {
      const r = await fetch('/api/sites')
      setSites(await r.json())
    } catch (err) { console.error('Sites load failed:', err) }
  }, [])

  const loadLog = useCallback(async () => {
    try {
      const r = await fetch('/api/log')
      setLog(await r.json())
    } catch (err) { console.error('Log load failed:', err) }
  }, [])

  const loadStatus = useCallback(async () => {
    try {
      const r = await fetch('/api/status')
      setStatus(await r.json())
    } catch (err) { console.error('Status load failed:', err) }
  }, [])

  // ── Initial + Interval Load ────────────────────────────────────────────
  useEffect(() => {
    loadConfig()
    loadSites()
    loadLog()
    loadStatus()
    const timer = window.setInterval(() => {
      loadSites()
      loadLog()
      loadStatus()
    }, 12000)
    return () => window.clearInterval(timer)
  }, [loadConfig, loadSites, loadLog, loadStatus])

  // ── Config Patch (merges with existing) ────────────────────────────────
  const patchConfig = async (partial) => {
    const r = await fetch('/api/config')
    const existing = await r.json()
    await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...existing, ...partial })
    })
  }

  // ── Telegram ───────────────────────────────────────────────────────────
  const saveAndTestTg = async () => {
    if (!botToken.trim() || !chatId.trim()) {
      toast('Enter both Bot Token and Chat ID', 'err')
      return
    }
    setTgLoading(true)
    try {
      await patchConfig({ bot_token: botToken.trim(), chat_id: chatId.trim() })
      const r = await fetch('/api/test/telegram', { method: 'POST' })
      const d = await r.json()
      if (d.ok) toast('✅ Telegram connected! Check your phone.', 'ok')
      else toast('❌ ' + d.message, 'err', 5000)
    } catch { toast('❌ Network error', 'err') }
    finally { setTgLoading(false) }
  }

  // ── Gmail ──────────────────────────────────────────────────────────────
  const saveGmail = async () => {
    const obj = { gmail_user: gmailUser.trim(), to_email: toEmail.trim() }
    if (gmailPass) obj.gmail_pass = gmailPass
    await patchConfig(obj)
    toast('✅ Gmail settings saved', 'ok')
  }

  // ── Interval ───────────────────────────────────────────────────────────
  const saveInterval = async (v) => {
    setInterval_(v)
    await patchConfig({ interval: parseInt(v) })
    toast(`✅ Interval updated to ${v} min`, 'ok')
  }

  // ── Sites ──────────────────────────────────────────────────────────────
  const addSite = async (e) => {
    e.preventDefault()
    if (!newUrl.trim()) { toast('Enter a URL first', 'err'); return }
    setAddLoading(true)
    try {
      const r = await fetch('/api/sites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: newUrl.trim(), name: newName.trim() })
      })
      const d = await r.json()
      if (d.ok) {
        setNewUrl('')
        setNewName('')
        toast(`✅ Site added! First scan in ~${interval} min`, 'ok')
        loadSites()
        loadStatus()
      } else {
        toast('❌ ' + d.error, 'err')
      }
    } catch { toast('❌ Network error', 'err') }
    finally { setAddLoading(false) }
  }

  const toggleSite = async (id) => {
    await fetch(`/api/sites/${id}/toggle`, { method: 'POST' })
    loadSites()
    loadStatus()
  }

  const resetSite = async (id) => {
    await fetch(`/api/sites/${id}/reset`, { method: 'POST' })
    toast('↺ Reset — will re-scan next cycle', 'info')
    loadSites()
  }

  const deleteSite = async (id) => {
    await fetch(`/api/sites/${id}`, { method: 'DELETE' })
    toast('Site removed', 'ok')
    loadSites()
    loadStatus()
  }

  const clearLog = async () => {
    await fetch('/api/log', { method: 'DELETE' })
    toast('Log cleared', 'ok')
    loadLog()
  }

  // ── Render ─────────────────────────────────────────────────────────────
  const isWatching = status.active_sites > 0

  return (
    <div className="app">

      {/* ═══ Header ═══ */}
      <header className="header">
        <div className="header__logo" aria-hidden="true">🔭</div>
        <div className="header__text">
          <h1>JobWatch Pro</h1>
          <p>Real-time multi-site career page monitor</p>
        </div>
        <nav className="header__badges" aria-label="Status indicators">
          <span className="badge badge--blue">{sites.length} Site{sites.length !== 1 ? 's' : ''}</span>
          <span className="badge badge--tg">{status.total_alerts} Alert{status.total_alerts !== 1 ? 's' : ''}</span>
          <span className={`badge ${isWatching ? 'badge--green' : 'badge--yellow'}`}>
            <span className={`badge__dot ${isWatching ? 'badge__dot--active' : 'badge__dot--idle'}`} />
            {isWatching ? 'Watching' : 'Idle'}
          </span>
        </nav>
      </header>

      {/* ═══ Stats ═══ */}
      <section className="stats" aria-label="Statistics">
        <article className="stat">
          <div className="stat__value">{status.active_sites}</div>
          <div className="stat__label">Watching</div>
        </article>
        <article className="stat">
          <div className="stat__value">{status.total_alerts}</div>
          <div className="stat__label">Alerts Sent</div>
        </article>
        <article className="stat">
          <div className="stat__value">{status.total_seen}</div>
          <div className="stat__label">Jobs Indexed</div>
        </article>
        <article className="stat">
          <div className="stat__value">{interval}m</div>
          <div className="stat__label">Poll Interval</div>
        </article>
      </section>

      {/* ═══ Main Grid ═══ */}
      <main className="grid">

        {/* ── Left Column ── */}
        <div className="col">

          {/* Careers Pages */}
          <section className="card" aria-label="Monitored career pages">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">🌐</span> Careers Pages</h2>
            </div>
            <form className="add-row" onSubmit={addSite}>
              <input
                type="text"
                value={newName}
                onChange={e => setNewName(e.target.value)}
                placeholder="Company name"
                style={{ maxWidth: 160 }}
                aria-label="Company name"
                id="input-company-name"
              />
              <input
                type="url"
                value={newUrl}
                onChange={e => setNewUrl(e.target.value)}
                placeholder="https://company.com/careers"
                required
                aria-label="Careers page URL"
                id="input-careers-url"
              />
              <button
                type="submit"
                className="btn btn--primary"
                disabled={addLoading}
                id="btn-add-site"
              >
                {addLoading ? '⏳' : '＋ Add'}
              </button>
            </form>

            <div className="site-list" role="list" id="site-list">
              {sites.length === 0 ? (
                <div className="empty">
                  <div className="empty__icon">🔗</div>
                  <p className="empty__text">No sites added yet.<br />Paste a careers page URL above.</p>
                </div>
              ) : sites.map(s => {
                const statusCls = (s.last_status || '').includes('✅') ? 'ok' : (s.last_status || '').includes('❌') ? 'err' : ''
                return (
                  <div
                    key={s.id}
                    className={`site ${s.enabled ? '' : 'site--off'}`}
                    role="listitem"
                    id={`site-${s.id}`}
                  >
                    <div className={`site__dot ${s.enabled ? 'site__dot--on' : 'site__dot--off'}`} aria-label={s.enabled ? 'Active' : 'Paused'} />
                    <div className="site__info">
                      <div className="site__name">{esc(s.name)}</div>
                      <div className="site__url">{esc(s.url)}</div>
                      <div className="site__meta">
                        <span className={statusCls}>{esc(s.last_status)}</span> · {esc(s.last_checked)} · {s.seen_count} indexed
                      </div>
                    </div>
                    <div className="site__actions">
                      <button className="btn--icon" onClick={() => toggleSite(s.id)} title={s.enabled ? 'Pause' : 'Resume'} aria-label={s.enabled ? 'Pause site' : 'Resume site'}>{s.enabled ? '⏸' : '▶'}</button>
                      <button className="btn--icon" onClick={() => resetSite(s.id)} title="Re-scan" aria-label="Reset site">↺</button>
                      <button className="btn--icon danger" onClick={() => deleteSite(s.id)} title="Remove" aria-label="Remove site">✕</button>
                    </div>
                  </div>
                )
              })}
            </div>
          </section>

          {/* Alert Log */}
          <section className="card" aria-label="Job alert history">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">📋</span> Alert Log</h2>
              <button className="btn btn--outline btn--sm" onClick={clearLog} id="btn-clear-log">Clear</button>
            </div>
            <div className="log-list" role="log" id="log-list">
              {log.length === 0 ? (
                <div className="empty">
                  <div className="empty__icon">📭</div>
                  <p className="empty__text">No alerts yet.<br />New jobs will appear here in real time.</p>
                </div>
              ) : log.slice(0, 50).map((l, i) => (
                <div className="log-item" key={i}>
                  <div className="log-item__icon" aria-hidden="true">💼</div>
                  <div className="log-item__body">
                    <div className="log-item__job">{esc(l.job)}</div>
                    <div className="log-item__site">
                      🏢 {esc(l.site_name)}
                      {l.experience && l.experience !== 'Not specified' && (
                        <span style={{ marginLeft: 8, color: 'var(--green)', fontWeight: 600 }}>
                          📊 {esc(l.experience)}
                        </span>
                      )}
                    </div>
                    <div className="log-item__time">
                      {esc(l.time)}
                      {l.link && (
                        <> · <a href={l.link} target="_blank" rel="noopener noreferrer">Apply ↗</a></>
                      )}
                      {' · '}<a href={l.url} target="_blank" rel="noopener noreferrer">Careers Page</a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

        </div>

        {/* ── Right Column ── */}
        <div className="col">

          {/* Telegram */}
          <section className="card" aria-label="Telegram notification setup">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">✈️</span> Telegram (Instant)</h2>
              <span className="badge badge--tg">Recommended</span>
            </div>

            <div className="steps">
              <div className="step">
                <div className="step__num">1</div>
                <div className="step__text">
                  Open Telegram → search <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer">@BotFather</a> → send <code>/newbot</code> → copy the <strong>token</strong>
                </div>
              </div>
              <div className="step">
                <div className="step__num">2</div>
                <div className="step__text">
                  Search <a href="https://t.me/userinfobot" target="_blank" rel="noopener noreferrer">@userinfobot</a> → send any message → copy your <strong>Chat ID</strong>
                </div>
              </div>
              <div className="step">
                <div className="step__num">3</div>
                <div className="step__text">Paste both below → click <strong>Save & Test</strong></div>
              </div>
            </div>

            <div className="field">
              <label className="field__label" htmlFor="input-bot-token">Bot Token</label>
              <input
                className="field__input field__input--mono"
                type="text"
                id="input-bot-token"
                value={botToken}
                onChange={e => setBotToken(e.target.value)}
                placeholder="123456:ABCdef..."
                autoComplete="off"
              />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="input-chat-id">Your Chat ID</label>
              <input
                className="field__input field__input--mono"
                type="text"
                id="input-chat-id"
                value={chatId}
                onChange={e => setChatId(e.target.value)}
                placeholder="123456789"
                autoComplete="off"
              />
            </div>

            <div className="btn-row">
              <button className="btn btn--tg" onClick={saveAndTestTg} disabled={tgLoading} id="btn-test-telegram">
                {tgLoading ? '⏳ Testing…' : '💾 Save & Test Telegram'}
              </button>
            </div>
          </section>

          {/* Gmail */}
          <section className="card" aria-label="Gmail notification setup">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">📧</span> Gmail Backup</h2>
              <span className="badge badge--yellow">Optional</span>
            </div>

            <div className="field">
              <label className="field__label" htmlFor="input-gmail-user">Your Gmail (sender)</label>
              <input
                className="field__input"
                type="email"
                id="input-gmail-user"
                value={gmailUser}
                onChange={e => setGmailUser(e.target.value)}
                placeholder="you@gmail.com"
              />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="input-gmail-pass">
                App Password <span className="hint">(not your real password)</span>
              </label>
              <input
                className="field__input field__input--mono"
                type="password"
                id="input-gmail-pass"
                value={gmailPass}
                onChange={e => setGmailPass(e.target.value)}
                placeholder={hasPass ? '••••••••••••••••' : '16-char app password'}
              />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="input-to-email">Send Alerts To</label>
              <input
                className="field__input"
                type="email"
                id="input-to-email"
                value={toEmail}
                onChange={e => setToEmail(e.target.value)}
                placeholder="recipient@gmail.com"
              />
            </div>

            <div className="btn-row">
              <button className="btn btn--outline" onClick={saveGmail} id="btn-save-gmail">💾 Save Gmail</button>
            </div>
          </section>

          {/* Poll Interval */}
          <section className="card" aria-label="Poll interval settings">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">⏱</span> Poll Interval</h2>
            </div>
            <div className="field">
              <label className="field__label" htmlFor="select-interval">Check every</label>
              <select
                className="field__input"
                id="select-interval"
                value={interval}
                onChange={e => saveInterval(e.target.value)}
              >
                <option value="1">Every 1 minute (fastest)</option>
                <option value="3">Every 3 minutes</option>
                <option value="5">Every 5 minutes (recommended)</option>
                <option value="10">Every 10 minutes</option>
                <option value="15">Every 15 minutes</option>
                <option value="30">Every 30 minutes</option>
                <option value="60">Every 60 minutes</option>
              </select>
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 'var(--sp-2)', lineHeight: 1.5 }}>
              💡 <strong style={{ color: 'var(--text-secondary)' }}>5 min</strong> is the sweet spot — detects new jobs within 5 min of posting.
            </p>
          </section>

        </div>
      </main>

      {/* ═══ Footer ═══ */}
      <footer className="footer">
        <p>JobWatch Pro · Runs 24/7 on <a href="https://railway.app" target="_blank" rel="noopener noreferrer">Railway</a> or Docker</p>
      </footer>

      {/* ═══ Toasts ═══ */}
      <ToastContainer toasts={toasts} />
    </div>
  )
}
