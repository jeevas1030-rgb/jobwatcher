import { useState, useEffect, useCallback, useRef } from 'react'

/* ═══════════════════════════════════════════════════════════════════════════
   JobWatch Pro — React Dashboard
   ═══════════════════════════════════════════════════════════════════════════ */

function esc(s) { return String(s || '') }

// ── Preset companies ────────────────────────────────────────────────────────
const PRESETS = [
  { name: 'Accenture',            url: 'https://www.accenture.com/in-en/careers/jobsearch?jk=software+engineer&sb=0&vw=1&is_rj=0', tag: 'JS' },
  { name: 'Wipro',                url: 'https://careers.wipro.com/search-jobs/', tag: 'JS' },
  { name: 'TCS',                  url: 'https://careers.tcs.com/search-jobs', tag: 'JS' },
  { name: 'Infosys',              url: 'https://career.infosys.com/joblist', tag: 'JS' },
  { name: 'Cognizant',            url: 'https://careers.cognizant.com/global/en/search-results?keywords=software+engineer', tag: 'JS' },
  { name: 'HCL Tech',             url: 'https://www.hcltech.com/careers/job-search', tag: 'JS' },
  { name: 'Tech Mahindra',        url: 'https://careers.techmahindra.com/search/?q=engineer', tag: 'JS' },
  { name: 'Capgemini',            url: 'https://www.capgemini.com/in-en/careers/job-search/?country=India', tag: 'JS' },
  { name: 'LTIMindtree',          url: 'https://www.ltimindtree.com/careers/job-openings/', tag: 'JS' },
  { name: 'Freshworks',           url: 'https://careers.freshworks.com/jobs', tag: 'Static' },
  { name: 'Zoho',                 url: 'https://careers.zohocorp.com/jobs/Careers', tag: 'Static' },
  { name: 'Razorpay',             url: 'https://razorpay.com/jobs/', tag: 'Static' },
  { name: 'Persistent',           url: 'https://careers.persistent.com/jobs', tag: 'Static' },
  { name: 'Mphasis',              url: 'https://careers.mphasis.com/search/', tag: 'Static' },
  { name: 'Hexaware',             url: 'https://hexaware.com/careers/', tag: 'Static' },
  { name: 'Fresher Jobs – BLR',   url: 'https://www.naukri.com/fresher-jobs-in-bangalore?experience=0', tag: 'City' },
  { name: 'Fresher Jobs – CHN',   url: 'https://www.naukri.com/fresher-jobs-in-chennai?experience=0',   tag: 'City' },
  { name: 'Fresher Jobs – HYD',   url: 'https://www.naukri.com/fresher-jobs-in-hyderabad?experience=0', tag: 'City' },
  { name: 'Fresher Jobs – Pune',  url: 'https://www.naukri.com/fresher-jobs-in-pune?experience=0',      tag: 'City' },
]

// ── Toast ───────────────────────────────────────────────────────────────────
function ToastContainer({ toasts }) {
  return (
    <div className="toast-container" aria-live="polite" aria-atomic="true">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast--${t.type} ${t.show ? 'toast--show' : ''}`}>{t.msg}</div>
      ))}
    </div>
  )
}

export default function App() {
  const [sites, setSites]         = useState([])
  const [log, setLog]             = useState([])
  const [status, setStatus]       = useState({ active_sites: 0, total_alerts: 0, total_seen: 0 })
  const [toasts, setToasts]       = useState([])
  const [newName, setNewName]     = useState('')
  const [newUrl, setNewUrl]       = useState('')
  const [botToken, setBotToken]   = useState('')
  const [chatId, setChatId]       = useState('')
  const [gmailUser, setGmailUser] = useState('')
  const [gmailPass, setGmailPass] = useState('')
  const [toEmail, setToEmail]     = useState('')
  const [pollMin, setPollMin]     = useState('5')
  const [hasPass, setHasPass]     = useState(false)
  const [tgLoading, setTgLoading] = useState(false)
  const [addLoading, setAddLoading] = useState(false)
  const [bulkLoading, setBulkLoading] = useState(false)
  const [bulkText, setBulkText]   = useState('')
  const [showBulk, setShowBulk]   = useState(false)
  const [addedUrls, setAddedUrls] = useState(new Set())
  const toastId = useRef(0)

  const toast = useCallback((msg, type = 'ok', dur = 3500) => {
    const id = ++toastId.current
    setToasts(p => [...p, { id, msg, type, show: false }])
    setTimeout(() => setToasts(p => p.map(t => t.id === id ? { ...t, show: true } : t)), 20)
    setTimeout(() => setToasts(p => p.map(t => t.id === id ? { ...t, show: false } : t)), dur)
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), dur + 300)
  }, [])

  const loadSites = useCallback(async () => {
    try {
      const data = await fetch('/api/sites').then(r => r.json())
      setSites(data)
      setAddedUrls(new Set(data.map(s => s.url)))
    } catch {}
  }, [])

  const loadLog    = useCallback(async () => { try { setLog(await fetch('/api/log').then(r=>r.json())) } catch {} }, [])
  const loadStatus = useCallback(async () => { try { setStatus(await fetch('/api/status').then(r=>r.json())) } catch {} }, [])
  const loadConfig = useCallback(async () => {
    try {
      const c = await fetch('/api/config').then(r => r.json())
      if (c.bot_token) setBotToken(c.bot_token)
      if (c.chat_id) setChatId(c.chat_id)
      if (c.gmail_user) setGmailUser(c.gmail_user)
      if (c.to_email) setToEmail(c.to_email)
      if (c.has_password) setHasPass(true)
      if (c.interval) setPollMin(String(c.interval))
    } catch {}
  }, [])

  useEffect(() => {
    loadConfig(); loadSites(); loadLog(); loadStatus()
    const t = window.setInterval(() => { loadSites(); loadLog(); loadStatus() }, 12000)
    return () => window.clearInterval(t)
  }, [loadConfig, loadSites, loadLog, loadStatus])

  const patchConfig = async (partial) => {
    const existing = await fetch('/api/config').then(r => r.json())
    await fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...existing, ...partial }) })
  }

  const saveAndTestTg = async () => {
    if (!botToken.trim() || !chatId.trim()) { toast('Enter both Bot Token and Chat ID', 'err'); return }
    setTgLoading(true)
    try {
      await patchConfig({ bot_token: botToken.trim(), chat_id: chatId.trim() })
      const d = await fetch('/api/test/telegram', { method: 'POST' }).then(r => r.json())
      if (d.ok) toast('✅ Telegram connected! Check your phone.', 'ok')
      else toast('❌ ' + d.message, 'err', 5000)
    } catch { toast('❌ Network error', 'err') }
    finally { setTgLoading(false) }
  }

  const saveGmail = async () => {
    const obj = { gmail_user: gmailUser.trim(), to_email: toEmail.trim() }
    if (gmailPass) obj.gmail_pass = gmailPass
    await patchConfig(obj)
    toast('✅ Gmail settings saved', 'ok')
  }

  const savePoll = async (v) => {
    setPollMin(v)
    await patchConfig({ interval: parseInt(v) })
    toast(`✅ Interval updated to ${v} min`, 'ok')
  }

  // ── Add helpers ───────────────────────────────────────────────────────────
  const apiAddSite = async (url, name) => {
    const r = await fetch('/api/sites', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, name })
    })
    return r.json()
  }

  const addSite = async (e) => {
    e.preventDefault()
    if (!newUrl.trim()) { toast('Enter a URL first', 'err'); return }
    setAddLoading(true)
    try {
      const d = await apiAddSite(newUrl.trim(), newName.trim())
      if (d.ok) { setNewUrl(''); setNewName(''); toast(`✅ Site added!`, 'ok'); loadSites(); loadStatus() }
      else toast('❌ ' + d.error, 'err')
    } catch { toast('❌ Network error', 'err') }
    finally { setAddLoading(false) }
  }

  const addPreset = async (p) => {
    if (addedUrls.has(p.url)) return
    try {
      const d = await apiAddSite(p.url, p.name)
      if (d.ok) { toast(`✅ ${p.name} added!`, 'ok', 2000); loadSites(); loadStatus() }
    } catch { toast('❌ Network error', 'err') }
  }

  const addAllPresets = async () => {
    setBulkLoading(true)
    let added = 0
    for (const p of PRESETS) {
      if (addedUrls.has(p.url)) continue
      try { const d = await apiAddSite(p.url, p.name); if (d.ok) added++ } catch {}
    }
    await loadSites(); await loadStatus()
    toast(`✅ Added ${added} sites!`, 'ok')
    setBulkLoading(false)
  }

  const addBulkUrls = async () => {
    if (!bulkText.trim()) { toast('Paste some URLs first', 'err'); return }
    setBulkLoading(true)
    const lines = bulkText.split('\n').map(l => l.trim()).filter(l => l.startsWith('http'))
    if (!lines.length) { toast('No valid URLs found', 'err'); setBulkLoading(false); return }
    let added = 0, skipped = 0
    for (const url of lines) {
      try {
        const name = new URL(url).hostname.replace(/^(www\.|careers\.)/, '').split('.')[0]
        const d = await apiAddSite(url, name.charAt(0).toUpperCase() + name.slice(1))
        if (d.ok) added++; else skipped++
      } catch { skipped++ }
    }
    setBulkText(''); setShowBulk(false)
    await loadSites(); await loadStatus()
    toast(`✅ Added ${added} sites${skipped ? ` (${skipped} skipped)` : ''}`, 'ok')
    setBulkLoading(false)
  }

  const toggleSite = async (id) => { await fetch(`/api/sites/${id}/toggle`, { method: 'POST' }); loadSites(); loadStatus() }
  const resetSite  = async (id) => { await fetch(`/api/sites/${id}/reset`, { method: 'POST' }); toast('↺ Reset!', 'info'); loadSites() }
  const deleteSite = async (id) => { await fetch(`/api/sites/${id}`, { method: 'DELETE' }); toast('Removed', 'ok'); loadSites(); loadStatus() }
  const clearLog   = async ()   => { await fetch('/api/log', { method: 'DELETE' }); toast('Cleared', 'ok'); loadLog() }

  const isWatching = status.active_sites > 0
  const bigIT   = PRESETS.filter(p => p.tag === 'JS')
  const startups = PRESETS.filter(p => p.tag === 'Static')
  const cities  = PRESETS.filter(p => p.tag === 'City')
  const bulkCount = bulkText.split('\n').filter(l => l.trim().startsWith('http')).length

  return (
    <div className="app">

      {/* Header */}
      <header className="header">
        <div className="header__logo" aria-hidden="true">🔭</div>
        <div className="header__text">
          <h1>JobWatch Pro</h1>
          <p>Real-time multi-site career page monitor</p>
        </div>
        <nav className="header__badges" aria-label="Status">
          <span className="badge badge--blue">{sites.length} Site{sites.length !== 1 ? 's' : ''}</span>
          <span className="badge badge--tg">{status.total_alerts} Alert{status.total_alerts !== 1 ? 's' : ''}</span>
          <span className={`badge ${isWatching ? 'badge--green' : 'badge--yellow'}`}>
            <span className={`badge__dot ${isWatching ? 'badge__dot--active' : 'badge__dot--idle'}`} />
            {isWatching ? 'Watching' : 'Idle'}
          </span>
        </nav>
      </header>

      {/* Stats */}
      <section className="stats" aria-label="Statistics">
        {[
          [status.active_sites, 'Watching'],
          [status.total_alerts, 'Alerts Sent'],
          [status.total_seen,   'Jobs Indexed'],
          [pollMin + 'm',       'Poll Interval'],
        ].map(([v, l]) => (
          <article className="stat" key={l}>
            <div className="stat__value">{v}</div>
            <div className="stat__label">{l}</div>
          </article>
        ))}
      </section>

      {/* ⚡ Quick Add Panel */}
      <section className="card quick-add-panel" aria-label="Quick add companies">
        <div className="card__head">
          <h2 className="card__title"><span className="icon">⚡</span> Quick Add Companies</h2>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn--outline btn--sm" onClick={() => setShowBulk(b => !b)} id="btn-toggle-bulk">
              {showBulk ? '▲ Hide' : '📋 Bulk Paste'}
            </button>
            <button className="btn btn--primary btn--sm" onClick={addAllPresets} disabled={bulkLoading} id="btn-add-all">
              {bulkLoading ? '⏳' : '＋ Add All'}
            </button>
          </div>
        </div>

        {showBulk && (
          <div style={{ marginBottom: 16 }}>
            <label className="field__label" htmlFor="bulk-urls-input">Paste multiple career page URLs (one per line)</label>
            <textarea
              id="bulk-urls-input"
              className="field__input"
              rows={5}
              value={bulkText}
              onChange={e => setBulkText(e.target.value)}
              placeholder={"https://careers.company1.com\nhttps://company2.com/jobs\nhttps://company3.com/careers"}
              style={{ fontFamily: 'monospace', fontSize: 12, resize: 'vertical', marginTop: 6 }}
            />
            <button className="btn btn--primary" onClick={addBulkUrls} disabled={bulkLoading} id="btn-add-bulk" style={{ marginTop: 8 }}>
              {bulkLoading ? '⏳ Adding…' : `＋ Add ${bulkCount} URL${bulkCount !== 1 ? 's' : ''}`}
            </button>
          </div>
        )}

        {[
          { label: '🏢 Big IT Companies', hint: '(launched via AI-powered browser)', list: bigIT, cls: '' },
          { label: '🚀 Startups & Mid-size', hint: '(fast HTML scraping)', list: startups, cls: 'chip--green' },
          { label: '📍 Fresher Jobs by City', hint: '(Naukri search)', list: cities, cls: 'chip--purple' },
        ].map(({ label, hint, list, cls }) => (
          <div className="preset-group" key={label}>
            <div className="preset-group__label">{label} <span className="hint">{hint}</span></div>
            <div className="preset-chips" role="list">
              {list.map((p, i) => {
                const added = addedUrls.has(p.url)
                return (
                  <button
                    key={i}
                    role="listitem"
                    className={`chip ${cls} ${added ? 'chip--added' : ''}`}
                    onClick={() => addPreset(p)}
                    disabled={added}
                    title={p.url}
                    id={`preset-${p.name.replace(/\W+/g,'-').toLowerCase()}`}
                  >
                    {added ? '✓ ' : '＋ '}{p.name}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </section>

      {/* Main Grid */}
      <main className="grid">
        <div className="col">

          {/* Careers Pages */}
          <section className="card" aria-label="Monitored career pages">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">🌐</span> Careers Pages</h2>
            </div>
            <form className="add-row" onSubmit={addSite}>
              <input type="text" value={newName} onChange={e => setNewName(e.target.value)} placeholder="Company name" style={{ maxWidth: 160 }} aria-label="Company name" id="input-company-name" />
              <input type="url" value={newUrl} onChange={e => setNewUrl(e.target.value)} placeholder="https://company.com/careers" required aria-label="Careers URL" id="input-careers-url" />
              <button type="submit" className="btn btn--primary" disabled={addLoading} id="btn-add-site">
                {addLoading ? '⏳' : '＋ Add'}
              </button>
            </form>

            <div className="site-list" role="list" id="site-list">
              {sites.length === 0 ? (
                <div className="empty">
                  <div className="empty__icon">🔗</div>
                  <p className="empty__text">No sites yet.<br />Use Quick Add above or paste a URL.</p>
                </div>
              ) : sites.map(s => {
                const sc = (s.last_status || '').includes('✅') ? 'ok' : (s.last_status || '').includes('❌') ? 'err' : ''
                return (
                  <div key={s.id} className={`site ${s.enabled ? '' : 'site--off'}`} role="listitem" id={`site-${s.id}`}>
                    <div className={`site__dot ${s.enabled ? 'site__dot--on' : 'site__dot--off'}`} aria-label={s.enabled ? 'Active' : 'Paused'} />
                    <div className="site__info">
                      <div className="site__name">{esc(s.name)}</div>
                      <div className="site__url">{esc(s.url)}</div>
                      <div className="site__meta"><span className={sc}>{esc(s.last_status)}</span> · {esc(s.last_checked)} · {s.seen_count} indexed</div>
                    </div>
                    <div className="site__actions">
                      <button className="btn--icon" onClick={() => toggleSite(s.id)} title={s.enabled ? 'Pause' : 'Resume'}>{s.enabled ? '⏸' : '▶'}</button>
                      <button className="btn--icon" onClick={() => resetSite(s.id)} title="Re-scan">↺</button>
                      <button className="btn--icon danger" onClick={() => deleteSite(s.id)} title="Remove">✕</button>
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
                  <p className="empty__text">No alerts yet.<br />New jobs appear here in real time.</p>
                </div>
              ) : log.slice(0, 50).map((l, i) => (
                <div className="log-item" key={i}>
                  <div className="log-item__icon" aria-hidden="true">💼</div>
                  <div className="log-item__body">
                    <div className="log-item__job">{esc(l.job)}</div>
                    <div className="log-item__site">
                      🏢 {esc(l.site_name)}
                      {l.experience && l.experience !== 'Not specified' && (
                        <span style={{ marginLeft: 8, color: 'var(--green)', fontWeight: 600 }}>📊 {esc(l.experience)}</span>
                      )}
                    </div>
                    <div className="log-item__time">
                      {esc(l.time)}
                      {l.link && <> · <a href={l.link} target="_blank" rel="noopener noreferrer">Apply ↗</a></>}
                      {' · '}<a href={l.url} target="_blank" rel="noopener noreferrer">Careers</a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="col">

          {/* Telegram */}
          <section className="card" aria-label="Telegram setup">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">✈️</span> Telegram (Instant)</h2>
              <span className="badge badge--tg">Recommended</span>
            </div>
            <div className="steps">
              {[
                <>Open Telegram → search <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer">@BotFather</a> → send <code>/newbot</code> → copy the <strong>token</strong></>,
                <>Search <a href="https://t.me/userinfobot" target="_blank" rel="noopener noreferrer">@userinfobot</a> → send any message → copy your <strong>Chat ID</strong></>,
                <>Paste both below → click <strong>Save & Test</strong></>,
              ].map((text, i) => (
                <div className="step" key={i}>
                  <div className="step__num">{i + 1}</div>
                  <div className="step__text">{text}</div>
                </div>
              ))}
            </div>
            <div className="field">
              <label className="field__label" htmlFor="input-bot-token">Bot Token</label>
              <input className="field__input field__input--mono" type="text" id="input-bot-token" value={botToken} onChange={e => setBotToken(e.target.value)} placeholder="123456:ABCdef..." autoComplete="off" />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="input-chat-id">Your Chat ID</label>
              <input className="field__input field__input--mono" type="text" id="input-chat-id" value={chatId} onChange={e => setChatId(e.target.value)} placeholder="123456789" autoComplete="off" />
            </div>
            <div className="btn-row">
              <button className="btn btn--tg" onClick={saveAndTestTg} disabled={tgLoading} id="btn-test-telegram">
                {tgLoading ? '⏳ Testing…' : '💾 Save & Test Telegram'}
              </button>
            </div>
          </section>

          {/* Gmail */}
          <section className="card" aria-label="Gmail setup">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">📧</span> Gmail Backup</h2>
              <span className="badge badge--yellow">Optional</span>
            </div>
            <div className="field">
              <label className="field__label" htmlFor="input-gmail-user">Your Gmail (sender)</label>
              <input className="field__input" type="email" id="input-gmail-user" value={gmailUser} onChange={e => setGmailUser(e.target.value)} placeholder="you@gmail.com" />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="input-gmail-pass">App Password <span className="hint">(not your real password)</span></label>
              <input className="field__input field__input--mono" type="password" id="input-gmail-pass" value={gmailPass} onChange={e => setGmailPass(e.target.value)} placeholder={hasPass ? '••••••••••••••••' : '16-char app password'} />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="input-to-email">Send Alerts To</label>
              <input className="field__input" type="email" id="input-to-email" value={toEmail} onChange={e => setToEmail(e.target.value)} placeholder="recipient@gmail.com" />
            </div>
            <div className="btn-row">
              <button className="btn btn--outline" onClick={saveGmail} id="btn-save-gmail">💾 Save Gmail</button>
            </div>
          </section>

          {/* Poll Interval */}
          <section className="card" aria-label="Poll interval">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">⏱</span> Poll Interval</h2>
            </div>
            <div className="field">
              <label className="field__label" htmlFor="select-interval">Check every</label>
              <select className="field__input" id="select-interval" value={pollMin} onChange={e => savePoll(e.target.value)}>
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

      <footer className="footer">
        <p>JobWatch Pro · Runs 24/7 on <a href="https://railway.app" target="_blank" rel="noopener noreferrer">Railway</a> or Docker</p>
      </footer>

      <ToastContainer toasts={toasts} />
    </div>
  )
}
