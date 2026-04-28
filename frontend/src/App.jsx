import { useState, useEffect, useCallback, useRef } from 'react'

/* ═══════════════════════════════════════════════════════════════════════════
   JobWatch Pro — Apple UI Dashboard
   ═══════════════════════════════════════════════════════════════════════════ */

function esc(s) { return String(s || '') }

// ── Massive Pre-loaded Company Database ─────────────────────────────────────
const PRESETS = [
  // MNC & SERVICES
  { name: 'Accenture',            url: 'https://www.accenture.com/in-en/careers/jobsearch?jk=software+engineer&sb=0&vw=1&is_rj=0', tag: 'Big IT' },
  { name: 'Wipro',                url: 'https://careers.wipro.com/search-jobs/', tag: 'Big IT' },
  { name: 'TCS',                  url: 'https://careers.tcs.com/search-jobs', tag: 'Big IT' },
  { name: 'Infosys',              url: 'https://career.infosys.com/joblist', tag: 'Big IT' },
  { name: 'Cognizant',            url: 'https://careers.cognizant.com/global/en/search-results?keywords=software+engineer', tag: 'Big IT' },
  { name: 'HCL Tech',             url: 'https://www.hcltech.com/careers/job-search', tag: 'Big IT' },
  { name: 'Tech Mahindra',        url: 'https://careers.techmahindra.com/search/?q=engineer', tag: 'Big IT' },
  { name: 'Capgemini',            url: 'https://www.capgemini.com/in-en/careers/job-search/?country=India', tag: 'Big IT' },
  { name: 'LTIMindtree',          url: 'https://www.ltimindtree.com/careers/job-openings/', tag: 'Big IT' },
  { name: 'Hexaware',             url: 'https://jobs.lever.co/hexaware', tag: 'Big IT' },
  { name: 'SLK Software',         url: 'https://www.slksoftware.com/careers', tag: 'Big IT' },
  { name: 'Mindtree',             url: 'https://www.ltimindtree.com/careers/', tag: 'Big IT' },
  { name: 'Mphasis',              url: 'https://careers.mphasis.com/search/', tag: 'Big IT' },
  
  // CHENNAI & SAAS GIANTS
  { name: 'Freshworks',           url: 'https://boards.greenhouse.io/freshworks', tag: 'Chennai/SaaS' },
  { name: 'Zoho',                 url: 'https://careers.zohocorp.com/jobs/Careers', tag: 'Chennai/SaaS' },
  { name: 'Kissflow',             url: 'https://boards.greenhouse.io/kissflow', tag: 'Chennai/SaaS' },
  { name: 'Chargebee',            url: 'https://boards.greenhouse.io/chargebee', tag: 'Chennai/SaaS' },
  { name: 'BrowserStack',         url: 'https://boards.greenhouse.io/browserstack', tag: 'Chennai/SaaS' },
  { name: 'Postman',              url: 'https://boards.greenhouse.io/postmanlabs', tag: 'Chennai/SaaS' },
  { name: 'Gupshup',              url: 'https://boards.greenhouse.io/gupshup', tag: 'Chennai/SaaS' },
  { name: 'CleverTap',            url: 'https://boards.greenhouse.io/clevertap', tag: 'Chennai/SaaS' },
  { name: 'Hasura',               url: 'https://boards.greenhouse.io/hasura', tag: 'Chennai/SaaS' },
  { name: 'Khatabook',            url: 'https://boards.greenhouse.io/khatabook', tag: 'Chennai/SaaS' },
  
  // AI, FINTECH & STARTUPS
  { name: 'Razorpay',             url: 'https://boards.greenhouse.io/razorpay', tag: 'AI/Startups' },
  { name: 'Zepto',                url: 'https://boards.greenhouse.io/zepto', tag: 'AI/Startups' },
  { name: 'Groww',                url: 'https://boards.greenhouse.io/groww', tag: 'AI/Startups' },
  { name: 'Meesho',               url: 'https://boards.greenhouse.io/meesho', tag: 'AI/Startups' },
  { name: 'Paytm',                url: 'https://jobs.lever.co/paytm', tag: 'AI/Startups' },
  { name: 'PhonePe',              url: 'https://jobs.lever.co/phonepe', tag: 'AI/Startups' },
  { name: 'Cred',                 url: 'https://boards.greenhouse.io/dreamplug', tag: 'AI/Startups' },
  { name: 'Swiggy',               url: 'https://boards.greenhouse.io/swiggy', tag: 'AI/Startups' },
  { name: 'Eightfold AI',         url: 'https://boards.greenhouse.io/eightfoldai', tag: 'AI/Startups' },
  { name: 'DataBricks',           url: 'https://boards.greenhouse.io/databricks', tag: 'AI/Startups' },
  { name: 'Flipkart',             url: 'https://jobs.lever.co/flipkart', tag: 'AI/Startups' },
  { name: 'Blinkit',              url: 'https://boards.greenhouse.io/blinkit', tag: 'AI/Startups' },
  
  // DIRECT CITIES (Naukri)
  { name: 'Fresher Jobs – BLR',   url: 'https://www.naukri.com/fresher-jobs-in-bangalore?experience=0', tag: 'City Search' },
  { name: 'Fresher Jobs – CHN',   url: 'https://www.naukri.com/fresher-jobs-in-chennai?experience=0',   tag: 'City Search' },
  { name: 'Fresher Jobs – HYD',   url: 'https://www.naukri.com/fresher-jobs-in-hyderabad?experience=0', tag: 'City Search' },
  { name: 'Fresher Jobs – Pune',  url: 'https://www.naukri.com/fresher-jobs-in-pune?experience=0',      tag: 'City Search' },
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
  const [groupedLog, setGroupedLog] = useState({})
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

  const loadLog = useCallback(async () => { 
    try { 
      const rawLog = await fetch('/api/log').then(r=>r.json());
      setLog(rawLog);
      
      // Categorize log by company
      const groups = {};
      rawLog.forEach(l => {
        const key = String(l.site_name || "Unknown");
        if(!groups[key]) groups[key] = [];
        groups[key].push(l);
      });
      setGroupedLog(groups);
    } catch {} 
  }, [])
  
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
  const bulkCount = bulkText.split('\n').filter(l => l.trim().startsWith('http')).length

  return (
    <div className="app">
      <ToastContainer toasts={toasts} />

      {/* Header */}
      <header className="header">
        <div className="header__logo">🚀</div>
        <div className="header__text">
          <h1>JobWatch Pro</h1>
          <p>Real-time automated career portal intelligence</p>
        </div>
        <div className="header__badges">
          <span className="badge badge--blue">{status.active_sites} Sites Watching</span>
          <span className="badge badge--tg" aria-live="polite">
            <span className={`badge__dot ${isWatching ? 'badge__dot--active' : 'badge__dot--idle'}`}></span>
            {isWatching ? 'Engine Running' : 'Idle'}
          </span>
        </div>
      </header>

      {/* Stats */}
      <div className="stats">
        <div className="stat"><div className="stat__value">{status.active_sites}</div><div className="stat__label">Watching</div></div>
        <div className="stat"><div className="stat__value">{status.total_alerts}</div><div className="stat__label">Jobs Sent</div></div>
        <div className="stat"><div className="stat__value">{status.total_seen}</div><div className="stat__label">Scanned</div></div>
        <div className="stat"><div className="stat__value">{pollMin}m</div><div className="stat__label">Interval</div></div>
      </div>

      <div className="grid">
        <div className="col">
          
          {/* Sites & Preset Manager */}
          <section className="card" aria-label="Target Sites">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">🌐</span> Portals & Startups</h2>
            </div>

            {/* Quick Add Apple-style Panel */}
            <div className="quick-add-panel">
              {['Big IT', 'Chennai/SaaS', 'AI/Startups'].map(category => (
                <div className="preset-group" key={category}>
                  <div className="preset-group__label">{category}</div>
                  <div className="preset-chips">
                    {PRESETS.filter(p => p.tag === category).map(p => {
                      const isAdded = addedUrls.has(p.url)
                      let colorClass = category === 'Chennai/SaaS' ? 'chip--purple' : category === 'AI/Startups' ? 'chip--green' : ''
                      return (
                        <button key={p.name} onClick={() => addPreset(p)} disabled={isAdded} className={`chip ${colorClass} ${isAdded ? 'chip--added' : ''}`}>
                          {isAdded && '✓'} {p.name}
                        </button>
                      )
                    })}
                  </div>
                </div>
              ))}
              <div className="btn-row" style={{ marginTop: '16px' }}>
                <button className="btn btn--outline btn--sm" id="btn-add-all" onClick={addAllPresets} disabled={bulkLoading}>
                  {bulkLoading ? 'Adding...' : '⚡ Add All Pre-loaded Sites'}
                </button>
                <button className="btn btn--outline btn--sm" id="btn-show-bulk" onClick={() => setShowBulk(!showBulk)}>
                  📋 Paste URLs...
                </button>
              </div>

              {showBulk && (
                <div style={{ marginTop: '12px' }}>
                  <textarea 
                    className="field__input field__input--mono" 
                    rows="4" 
                    placeholder="https://careers.example.com&#10;https://jobs.test.com"
                    value={bulkText}
                    onChange={e => setBulkText(e.target.value)}
                    style={{ resize: 'vertical' }}
                  />
                  <button className="btn btn--primary btn--sm" style={{ marginTop: '8px' }} onClick={addBulkUrls} disabled={bulkLoading}>
                    {bulkLoading ? 'Adding...' : `Add ${bulkCount > 0 ? bulkCount : ''} URLs`}
                  </button>
                </div>
              )}
            </div>

            <form className="add-row" onSubmit={addSite}>
              <input type="text" id="input-site-name" value={newName} onChange={e => setNewName(e.target.value)} placeholder="Custom Name" style={{ flex: '0.4' }} />
              <input type="url" id="input-site-url" value={newUrl} onChange={e => setNewUrl(e.target.value)} placeholder="https://careers.domain.com" />
              <button className="btn btn--primary" type="submit" disabled={addLoading} style={{ padding: '0 24px' }}>+</button>
            </form>

            <div className="site-list" id="site-list" role="list">
              {sites.length === 0 ? (
                <div className="empty">
                  <div className="empty__icon">🌍</div>
                  <p className="empty__text">No sites are being monitored.<br />Add a careers page to start tracking.</p>
                </div>
              ) : sites.map(s => (
                <div className={`site ${s.is_active ? '' : 'site--off'}`} key={s.id} role="listitem">
                  <div className={`site__dot ${s.is_active ? 'site__dot--on' : 'site__dot--off'}`}></div>
                  <div className="site__info">
                    <div className="site__name">{esc(s.name)}</div>
                    <div className="site__url">{s.url.replace(/^https?:\/\//, '').replace(/\/$/, '')}</div>
                    <div className="site__meta">
                      {s.last_error ? <span className="err">⚠️ {esc(s.last_error)}</span> :
                       s.last_checked ? <><span className="ok">✓ Checked</span> · {esc(s.last_checked)} · {s.seen_count || 0} indexed</> : 'Waiting for first check...'}
                    </div>
                  </div>
                  <div className="site__actions">
                    <button className="btn btn--icon" onClick={() => toggleSite(s.id)} title={s.is_active ? 'Pause' : 'Resume'}>{s.is_active ? '⏸' : '▶'}</button>
                    <button className="btn btn--icon" onClick={() => resetSite(s.id)} title="Reset memory">↺</button>
                    <button className="btn btn--icon danger" onClick={() => deleteSite(s.id)} title="Delete">✕</button>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Categorized Alert Log */}
          <section className="card" aria-label="Alert Log">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">🔔</span> Discovery Feed</h2>
              {log.length > 0 && <button className="btn btn--outline btn--sm" id="btn-clear-log" onClick={clearLog}>Clear</button>}
            </div>
            <div className="log-list" id="log-list" role="log">
              {log.length === 0 ? (
                <div className="empty">
                  <div className="empty__icon">📭</div>
                  <p className="empty__text">No jobs discovered yet.<br />Perfect matches will appear here.</p>
                </div>
              ) : Object.keys(groupedLog).map(companyName => (
                <div key={companyName} className="company-group" style={{ marginBottom: "20px" }}>
                  <h3 style={{ fontSize: "15px", fontWeight: "700", color: "var(--accent)", borderBottom: "1.5px solid var(--border-light)", paddingBottom: "8px", marginBottom: "12px" }}>
                    🏢 {esc(companyName)} <span style={{fontSize: "12px", background: "var(--bg-surface)", padding: "2px 8px", borderRadius: "100px", color: "var(--text-muted)", marginLeft: "8px"}}>{groupedLog[companyName].length} jobs</span>
                  </h3>
                  {groupedLog[companyName].map((l, i) => (
                    <div className="log-item" key={i} style={{ display: 'flex', flexDirection: 'column', gap: '4px', paddingBottom: '16px' }}>
                      <div className="log-item__job" style={{ fontSize: "14px", fontWeight: "700" }}>
                        {esc(l.job)}
                        {l.experience && l.experience !== 'Not specified' && (
                          <span style={{ fontSize: "11px", marginLeft: 8, background: "var(--green-light)", color: "var(--green)", padding: '2px 8px', borderRadius: '100px' }}>
                            {esc(l.experience)}
                          </span>
                        )}
                         <span style={{ fontSize: "11px", marginLeft: 4, background: "var(--accent-light)", color: "var(--accent)", padding: '2px 8px', borderRadius: '100px' }}>
                            {esc(l.posted_date || "Recent")}
                          </span>
                      </div>
                      
                      <div style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.4", margin: "4px 0" }}>
                         {l.location && <span style={{fontWeight: 600, color: "var(--text-primary)"}}>📍 {esc(l.location)} · </span>}
                         {esc(l.description || "No description provided.")}
                      </div>

                      <div className="log-item__time">
                        {esc(l.time)}
                        {l.link && <> · <a href={l.link} target="_blank" rel="noopener noreferrer">Apply Directly ↗</a></>}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="col">
          {/* Telegram Settings */}
          <section className="card" aria-label="Telegram setup">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">📱</span> Notifications</h2>
              <span className="badge badge--tg">Recommended</span>
            </div>
            <div className="steps">
              {[
                <>Open Telegram → search <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer">@BotFather</a> → send <code>/newbot</code> → copy token</>,
                <>Search <a href="https://t.me/userinfobot" target="_blank" rel="noopener noreferrer">@userinfobot</a> → get your Chat ID</>,
                <>Save & Test below</>,
              ].map((text, i) => (
                <div className="step" key={i}>
                  <div className="step__num">{i + 1}</div>
                  <div className="step__text">{text}</div>
                </div>
              ))}
            </div>
            <div className="field">
              <label className="field__label">Bot Token</label>
              <input className="field__input field__input--mono" type="text" value={botToken} onChange={e => setBotToken(e.target.value)} placeholder="123456:ABCdef" autoComplete="off" />
            </div>
            <div className="field">
              <label className="field__label">Your Chat ID</label>
              <input className="field__input field__input--mono" type="text" value={chatId} onChange={e => setChatId(e.target.value)} placeholder="123456789" autoComplete="off" />
            </div>
            <div className="btn-row">
              <button className="btn btn--tg" onClick={saveAndTestTg} disabled={tgLoading}>
                {tgLoading ? '⏳ Testing…' : '🚀 Save & Test'}
              </button>
            </div>
          </section>

          {/* Engine Settings */}
          <section className="card" aria-label="Poll interval">
            <div className="card__head">
              <h2 className="card__title"><span className="icon">⚙️</span> Engine Settings</h2>
            </div>
            <div className="field">
              <label className="field__label">Scan Frequency</label>
              <select className="field__input" value={pollMin} onChange={e => savePoll(e.target.value)}>
                <option value="1">Hyper-Drive (Every 1 min)</option>
                <option value="3">Every 3 minutes</option>
                <option value="5">Every 5 minutes (ideal)</option>
                <option value="15">Every 15 minutes</option>
                <option value="60">Every 1 hour</option>
              </select>
            </div>
          </section>
        </div>
      </div>
      <footer className="footer">
        JobWatch Pro by AI 🚀 <br/> Designed like Apple, Engineered for Scale.
      </footer>
    </div>
  )
}
