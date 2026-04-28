import { useState, useEffect, useCallback, useRef } from 'react'

/* ═══════════════════════════════════════════════════════════════════════════
   JobWatch Pro — Apple-Inspired Dashboard
   100+ companies · Grouped job feed · Location · Posted time · Description
   ═══════════════════════════════════════════════════════════════════════════ */

const API = ''

// ── Exp pill helper ─────────────────────────────────────────────────────────
function expPillClass(exp) {
  if (!exp || exp === 'Not specified') return 'exp-pill exp-pill--none'
  const l = exp.toLowerCase()
  if (l === 'fresher' || l === 'entry level') return 'exp-pill exp-pill--fresher'
  const m = exp.match(/(\d+)/)
  if (m && parseInt(m[1]) <= 1) return 'exp-pill exp-pill--fresher'
  return 'exp-pill exp-pill--entry'
}

// ── Preset companies (100+) ─────────────────────────────────────────────────
const PRESETS = [
  {
    label: '🏢 MNC Giants',
    variant: '',
    hint: 'Accenture, TCS, Wipro… (JS sites, Playwright)',
    companies: [
      { name: 'Accenture',      url: 'https://www.accenture.com/in-en/careers/jobsearch?jk=software+engineer&sb=0&vw=1&is_rj=0' },
      { name: 'TCS',            url: 'https://careers.tcs.com/content/tcs/in/en/students-and-freshers.html' },
      { name: 'Wipro',          url: 'https://careers.wipro.com/search-jobs/' },
      { name: 'Infosys',        url: 'https://career.infosys.com/jobdesc?jobReferenceCode=INFSYS-EXTERNAL-175977' },
      { name: 'Cognizant',      url: 'https://careers.cognizant.com/global/en/search-results?keywords=fresher' },
      { name: 'HCL Tech',       url: 'https://www.hcltech.com/careers' },
      { name: 'Tech Mahindra',  url: 'https://careers.techmahindra.com/search/#' },
      { name: 'Capgemini',      url: 'https://www.capgemini.com/in-en/careers/job-search/' },
      { name: 'LTIMindtree',    url: 'https://www.ltimindtree.com/careers/job-listings' },
      { name: 'IBM India',      url: 'https://www.ibm.com/careers/search?field_of_study=Computer%20Science&country=IN' },
      { name: 'Deloitte',       url: 'https://www2.deloitte.com/in/en/pages/careers/articles/join-deloitte.html' },
      { name: 'Oracle India',   url: 'https://careers.oracle.com/jobs/#en/sites/jobsearch/requisitions?keyword=fresher' },
    ],
  },
  {
    label: '🔧 Service & Mid-Tier IT',
    variant: 'green',
    hint: 'SLK, Hexaware, Mphasis… quiet but solid companies',
    companies: [
      { name: 'Hexaware',       url: 'https://hexaware.com/careers/' },
      { name: 'Mphasis',        url: 'https://careers.mphasis.com/search/#' },
      { name: 'Coforge',        url: 'https://jobs.greenhouse.io/coforge' },
      { name: 'Zensar',         url: 'https://jobs.greenhouse.io/zensar' },
      { name: 'Nagarro',        url: 'https://jobs.greenhouse.io/nagarro' },
      { name: 'Happiestminds',  url: 'https://jobs.greenhouse.io/happiestminds' },
      { name: 'KPIT',           url: 'https://www.kpit.com/careers/opportunities/' },
      { name: 'Birlasoft',      url: 'https://api.lever.co/v0/postings/birlasoft?mode=json' },
      { name: 'Cyient',         url: 'https://api.lever.co/v0/postings/cyient?mode=json' },
      { name: 'Tata Elxsi',     url: 'https://api.lever.co/v0/postings/tata-elxsi?mode=json' },
      { name: 'Sasken',         url: 'https://api.lever.co/v0/postings/sasken?mode=json' },
      { name: 'SLK Software',   url: 'https://slkgroup.com/careers/' },
      { name: 'ITC Infotech',   url: 'https://www.itcinfotech.com/careers/job-openings/' },
      { name: 'Sonata Software',url: 'https://www.sonata-software.com/careers' },
      { name: 'CSS Corp/Movate',url: 'https://movate.com/careers/' },
      { name: 'Sutherland',     url: 'https://www.sutherlandglobal.com/careers' },
      { name: 'Mastech',        url: 'https://mastech.com/careers' },
      { name: 'Trigent',        url: 'https://trigent.com/careers/' },
    ],
  },
  {
    label: '🌆 Chennai Companies',
    variant: 'orange',
    hint: 'Chennai-based and Chennai-heavy offices',
    companies: [
      { name: 'Zoho',           url: 'https://careers.zohocorp.com/jobs/Careers' },
      { name: 'Freshworks',     url: 'https://boards.greenhouse.io/freshworks/jobs' },
      { name: 'Aspire Systems', url: 'https://boards.greenhouse.io/aspiresystems/jobs' },
      { name: 'm2p Fintech',    url: 'https://boards.greenhouse.io/m2pfintech/jobs' },
      { name: 'Payoda',         url: 'https://boards.greenhouse.io/payoda/jobs' },
      { name: 'Ramco Systems',  url: 'https://www.ramco.com/careers/' },
      { name: 'Soliton Tech',   url: 'https://solitontech.com/careers/' },
      { name: 'Mad Street Den', url: 'https://www.madstreetden.com/careers/' },
      { name: 'Movate Chennai', url: 'https://movate.com/careers/' },
      { name: 'Accolite',       url: 'https://www.accolite.com/careers/' },
      { name: 'CSS Corp',       url: 'https://movate.com/careers/' },
      { name: 'Bosch India',    url: 'https://jobs.smartrecruiters.com/BoschGroup/careers' },
      { name: 'Verizon India',  url: 'https://www.verizon.com/about/careers' },
      { name: 'DBS Tech India', url: 'https://www.dbs.com/careers' },
    ],
  },
  {
    label: '🦄 Unicorns & Startups',
    variant: 'purple',
    hint: 'Razorpay, Swiggy, CRED, Meesho…',
    companies: [
      { name: 'Razorpay',      url: 'https://boards.greenhouse.io/razorpay/jobs' },
      { name: 'Swiggy',        url: 'https://boards.greenhouse.io/swiggy/jobs' },
      { name: 'Zomato',        url: 'https://jobs.lever.co/zomato' },
      { name: 'CRED',          url: 'https://boards.greenhouse.io/dreamplug/jobs' },
      { name: 'PhonePe',       url: 'https://jobs.lever.co/phonepe' },
      { name: 'Meesho',        url: 'https://boards.greenhouse.io/meesho/jobs' },
      { name: 'Zepto',         url: 'https://boards.greenhouse.io/zepto/jobs' },
      { name: 'Groww',         url: 'https://boards.greenhouse.io/groww/jobs' },
      { name: 'Nykaa',         url: 'https://jobs.lever.co/nykaa' },
      { name: 'ShareChat',     url: 'https://jobs.lever.co/sharechat' },
      { name: 'BharatPe',      url: 'https://jobs.lever.co/bharatpe' },
      { name: 'Ather Energy',  url: 'https://jobs.lever.co/ather-energy' },
      { name: 'Licious',       url: 'https://jobs.lever.co/licious' },
      { name: 'BrowserStack',  url: 'https://boards.greenhouse.io/browserstack/jobs' },
      { name: 'Postman',       url: 'https://boards.greenhouse.io/postmanlabs/jobs' },
      { name: 'Chargebee',     url: 'https://boards.greenhouse.io/chargebee/jobs' },
      { name: 'DarwinBox',     url: 'https://boards.greenhouse.io/darwinbox/jobs' },
      { name: 'Sprinklr',      url: 'https://boards.greenhouse.io/sprinklr/jobs' },
      { name: 'MoEngage',      url: 'https://jobs.lever.co/moengage' },
      { name: 'LeadSquared',   url: 'https://jobs.lever.co/leadsquared' },
      { name: 'CleverTap',     url: 'https://boards.greenhouse.io/clevertap/jobs' },
      { name: 'Physics Wallah',url: 'https://jobs.lever.co/physicswallah' },
      { name: 'Urban Company', url: 'https://boards.greenhouse.io/urbanclap/jobs' },
      { name: 'Spinny',        url: 'https://boards.greenhouse.io/spinny/jobs' },
      { name: 'Purplle',       url: 'https://boards.greenhouse.io/purplle/jobs' },
    ],
  },
  {
    label: '🤖 AI & Deep Tech',
    variant: 'teal',
    hint: 'Sarvam, Yellow.ai, Observe.AI…',
    companies: [
      { name: 'Sarvam AI',     url: 'https://boards.greenhouse.io/sarvam-ai/jobs' },
      { name: 'Yellow.ai',     url: 'https://boards.greenhouse.io/yellowmessenger/jobs' },
      { name: 'Haptik',        url: 'https://boards.greenhouse.io/haptik/jobs' },
      { name: 'Observe.AI',    url: 'https://boards.greenhouse.io/observeai/jobs' },
      { name: 'Uniphore',      url: 'https://boards.greenhouse.io/uniphore/jobs' },
      { name: 'Gnani.ai',      url: 'https://jobs.lever.co/gnani' },
      { name: 'Krutrim (Ola)', url: 'https://krutrim.ai/careers' },
      { name: 'Entropik',      url: 'https://entropiktech.com/careers/' },
      { name: 'Simplismart',   url: 'https://simplismart.ai/careers' },
      { name: 'Murf AI',       url: 'https://murf.ai/careers' },
      { name: 'HashedIn (Deloitte)', url: 'https://hashedin.com/careers/' },
    ],
  },
  {
    label: '💰 FinTech',
    variant: 'green',
    hint: 'Slice, Jupiter, m2p, KreditBee…',
    companies: [
      { name: 'Slice',         url: 'https://boards.greenhouse.io/slicecard/jobs' },
      { name: 'Jupiter Money', url: 'https://boards.greenhouse.io/jupitermoney/jobs' },
      { name: 'KreditBee',     url: 'https://boards.greenhouse.io/kreditbee/jobs' },
      { name: 'MoneyView',     url: 'https://boards.greenhouse.io/moneyview/jobs' },
      { name: 'Lendingkart',   url: 'https://boards.greenhouse.io/lendingkart/jobs' },
      { name: 'Navi',          url: 'https://jobs.lever.co/navi' },
      { name: 'Fibe (EarlySalary)', url: 'https://jobs.lever.co/earlysalary' },
      { name: 'Rupeek',        url: 'https://jobs.lever.co/rupeek' },
      { name: 'CoinDCX',       url: 'https://coindcx.com/careers' },
      { name: 'KoinX',         url: 'https://jobs.lever.co/koinx' },
      { name: 'Fi Money',      url: 'https://jobs.lever.co/epifi' },
    ],
  },
  {
    label: '📍 City Job Feeds',
    variant: 'purple',
    hint: 'Naukri fresher searches by city — gets real updated listings',
    companies: [
      { name: '🏙 Bangalore Freshers',  url: 'https://www.naukri.com/fresher-jobs-in-bangalore' },
      { name: '🌊 Chennai Freshers',    url: 'https://www.naukri.com/fresher-jobs-in-chennai' },
      { name: '🌴 Hyderabad Freshers',  url: 'https://www.naukri.com/fresher-jobs-in-hyderabad' },
      { name: '🏔 Pune Freshers',       url: 'https://www.naukri.com/fresher-jobs-in-pune' },
      { name: '🌉 Mumbai Freshers',     url: 'https://www.naukri.com/fresher-jobs-in-mumbai' },
      { name: '🏛 Noida Freshers',      url: 'https://www.naukri.com/fresher-jobs-in-noida' },
    ],
  },
]

// ── Toast hook ──────────────────────────────────────────────────────────────
function useToast() {
  const [toasts, setToasts] = useState([])
  const add = useCallback((msg, type = 'ok') => {
    const id = Date.now()
    setToasts(t => [...t, { id, msg, type, show: false }])
    setTimeout(() => setToasts(t => t.map(x => x.id === id ? { ...x, show: true } : x)), 20)
    setTimeout(() => setToasts(t => t.map(x => x.id === id ? { ...x, show: false } : x)), 3500)
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3800)
  }, [])
  return { toasts, add }
}

// ── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [sites, setSites]         = useState([])
  const [log, setLog]             = useState([])
  const [status, setStatus]       = useState({})
  const [config, setConfig]       = useState({})
  const [addName, setAddName]     = useState('')
  const [addUrl, setAddUrl]       = useState('')
  const [addedUrls, setAddedUrls] = useState(new Set())
  const [bulkText, setBulkText]   = useState('')
  const [showBulk, setShowBulk]   = useState(false)
  const [testingTg, setTestingTg] = useState(false)
  const [saving, setSaving]       = useState(false)
  const { toasts, add: toast }    = useToast()

  // ── Fetch helpers ──────────────────────────────────────────────────────────
  const fetchAll = useCallback(async () => {
    try {
      const [s, l, st, c] = await Promise.all([
        fetch(`${API}/api/sites`).then(r => r.json()),
        fetch(`${API}/api/log`).then(r => r.json()),
        fetch(`${API}/api/status`).then(r => r.json()),
        fetch(`${API}/api/config`).then(r => r.json()),
      ])
      setSites(s)
      setLog(l)
      setStatus(st)
      setConfig(c)
      setAddedUrls(new Set(s.map(x => x.url)))
    } catch (e) {
      console.warn('fetch failed', e)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const t = setInterval(fetchAll, 30_000)
    return () => clearInterval(t)
  }, [fetchAll])

  // ── Site actions ───────────────────────────────────────────────────────────
  const addSite = useCallback(async (name, url) => {
    if (!url.startsWith('http')) { toast('URL must start with http(s)://', 'err'); return }
    const r = await fetch(`${API}/api/sites`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, url }),
    })
    const j = await r.json()
    if (j.ok) {
      toast(`✓ ${name || url} added`, 'ok')
      fetchAll()
    } else {
      toast(j.error || 'Error', 'err')
    }
  }, [fetchAll, toast])

  const handleAdd = useCallback(async () => {
    const url = addUrl.trim()
    const name = addName.trim()
    if (!url) return
    await addSite(name, url)
    setAddName(''); setAddUrl('')
  }, [addName, addUrl, addSite])

  const addChip = useCallback(async ({ name, url }) => {
    await addSite(name, url)
  }, [addSite])

  const addAllPreset = useCallback(async (group) => {
    const toAdd = group.companies.filter(c => !addedUrls.has(c.url))
    if (!toAdd.length) { toast('All already added!', 'info'); return }
    for (const c of toAdd) await addSite(c.name, c.url)
    toast(`✓ Added ${toAdd.length} companies`, 'ok')
  }, [addedUrls, addSite, toast])

  const addAllBulk = useCallback(async () => {
    const lines = bulkText.split('\n').map(l => l.trim()).filter(Boolean)
    let added = 0
    for (const l of lines) {
      const parts = l.split(',').map(p => p.trim())
      const url = parts.find(p => p.startsWith('http')) || l
      const name = parts.find(p => !p.startsWith('http')) || ''
      if (url.startsWith('http') && !addedUrls.has(url)) {
        await addSite(name, url); added++
      }
    }
    setBulkText(''); setShowBulk(false)
    toast(`✓ Added ${added} sites`, 'ok')
  }, [bulkText, addedUrls, addSite, toast])

  const toggleSite = useCallback(async id => {
    await fetch(`${API}/api/sites/${id}/toggle`, { method: 'POST' })
    fetchAll()
  }, [fetchAll])

  const deleteSite = useCallback(async id => {
    await fetch(`${API}/api/sites/${id}`, { method: 'DELETE' })
    fetchAll()
    toast('Removed', 'ok')
  }, [fetchAll, toast])

  const resetSite = useCallback(async id => {
    await fetch(`${API}/api/sites/${id}/reset`, { method: 'POST' })
    fetchAll()
    toast('Reset — will re-scan', 'info')
  }, [fetchAll, toast])

  const clearLog = useCallback(async () => {
    await fetch(`${API}/api/log`, { method: 'DELETE' })
    setLog([])
    toast('Log cleared', 'ok')
  }, [toast])

  const saveConfig = useCallback(async () => {
    setSaving(true)
    await fetch(`${API}/api/config`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    setSaving(false)
    toast('Config saved', 'ok')
  }, [config, toast])

  const testTelegram = useCallback(async () => {
    setTestingTg(true)
    const r = await fetch(`${API}/api/test/telegram`, { method: 'POST' })
    const j = await r.json()
    setTestingTg(false)
    toast(j.message || (j.ok ? '✓ Sent!' : '✗ Failed'), j.ok ? 'ok' : 'err')
  }, [toast])

  // ── Grouped job feed ───────────────────────────────────────────────────────
  const grouped = log.reduce((acc, item) => {
    const key = item.site_name || 'Unknown'
    if (!acc[key]) acc[key] = []
    acc[key].push(item)
    return acc
  }, {})

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="app">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="header">
        <div className="header__logo" aria-hidden="true">🎯</div>
        <div className="header__text">
          <h1>JobWatch Pro</h1>
          <p>Real-time multi-site career page monitor — freshers only</p>
        </div>
        <div className="header__badges">
          <span className="badge badge--blue">
            {status.total_sites ?? '–'} Sites
          </span>
          <span className="badge badge--yellow">
            {status.total_alerts ?? '–'} Alerts
          </span>
          <span className="badge badge--green">
            <span className="badge__dot badge__dot--active" />
            Watching
          </span>
        </div>
      </header>

      {/* ── Stats ──────────────────────────────────────────────────────── */}
      <section className="stats" aria-label="Summary statistics">
        {[
          { v: status.active_sites ?? '–', l: 'Watching' },
          { v: status.total_alerts ?? '–', l: 'Alerts Sent' },
          { v: status.total_seen ?? '–',   l: 'Jobs Indexed' },
          { v: `${config.interval ?? 5}m`, l: 'Poll Interval' },
        ].map(({ v, l }) => (
          <div key={l} className="stat">
            <div className="stat__value">{v}</div>
            <div className="stat__label">{l}</div>
          </div>
        ))}
      </section>

      {/* ── Main Grid ──────────────────────────────────────────────────── */}
      <div className="grid">

        {/* ── LEFT COL ───────────────────────────────────────────────── */}
        <div className="col">

          {/* Careers Pages Card */}
          <div className="card">
            <div className="card__head">
              <div className="card__title"><span className="icon">🌐</span> Careers Pages</div>
            </div>

            {/* Add Single */}
            <div className="add-row">
              <input
                id="add-name" placeholder="Company name"
                value={addName} onChange={e => setAddName(e.target.value)}
                aria-label="Company name"
              />
              <input
                id="add-url" placeholder="https://company.com/careers"
                value={addUrl} onChange={e => setAddUrl(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAdd()}
                aria-label="Careers page URL"
              />
              <button id="btn-add" className="btn btn--primary" onClick={handleAdd}>＋ Add</button>
            </div>

            {/* Quick Add Presets */}
            <div className="quick-add-panel">
              {PRESETS.map(group => (
                <div key={group.label} className="preset-group">
                  <div className="preset-group__label">
                    {group.label}
                    <span className="hint">— {group.hint}</span>
                    <button
                      className="btn btn--sm btn--outline"
                      style={{ marginLeft: 'auto', fontSize: '11px', padding: '4px 10px' }}
                      onClick={() => addAllPreset(group)}
                    >
                      Add All
                    </button>
                  </div>
                  <div className="preset-chips">
                    {group.companies.map(c => (
                      <button
                        key={c.url}
                        className={`chip chip--${group.variant} ${addedUrls.has(c.url) ? 'chip--added' : ''}`}
                        onClick={() => !addedUrls.has(c.url) && addChip(c)}
                        disabled={addedUrls.has(c.url)}
                        title={c.url}
                      >
                        {addedUrls.has(c.url) ? '✓ ' : '＋ '}{c.name}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Bulk Paste */}
            <div style={{ marginTop: 'var(--sp-4)' }}>
              <button
                className="btn btn--outline btn--sm"
                onClick={() => setShowBulk(p => !p)}
              >
                {showBulk ? '▲ Hide Bulk Add' : '📋 Bulk Paste URLs'}
              </button>
              {showBulk && (
                <div style={{ marginTop: 'var(--sp-3)' }}>
                  <textarea
                    className="field__input"
                    rows={5}
                    placeholder={"https://company1.com/careers\nhttps://company2.com/jobs\nCompany Name, https://..."}
                    value={bulkText}
                    onChange={e => setBulkText(e.target.value)}
                    style={{ resize: 'vertical', fontFamily: 'var(--font-mono)', fontSize: '12px' }}
                  />
                  <div className="btn-row">
                    <button className="btn btn--primary btn--sm" onClick={addAllBulk}>Add All URLs</button>
                    <button className="btn btn--outline btn--sm" onClick={() => { setBulkText(''); setShowBulk(false) }}>Cancel</button>
                  </div>
                </div>
              )}
            </div>

            {/* Site list */}
            <div className="site-list" style={{ marginTop: 'var(--sp-5)' }}>
              {sites.length === 0 ? (
                <div className="empty">
                  <div className="empty__icon">🏢</div>
                  <div className="empty__text">No sites yet.<br />Click a company chip above or add a URL.</div>
                </div>
              ) : sites.map(s => (
                <div key={s.id} className={`site ${s.enabled ? '' : 'site--off'}`}>
                  <div className={`site__dot site__dot--${s.enabled ? 'on' : 'off'}`} />
                  <div className="site__info">
                    <div className="site__name">{s.name}</div>
                    <div className="site__url">{s.url}</div>
                    <div className="site__meta">
                      {s.last_status?.startsWith('✅')
                        ? <span className="ok">{s.last_status}</span>
                        : <span className="err">{s.last_status}</span>
                      }
                      {' · '}{s.last_checked}
                    </div>
                  </div>
                  <div className="site__actions">
                    <button className="btn--icon" title="Toggle" onClick={() => toggleSite(s.id)}>
                      {s.enabled ? '⏸' : '▶'}
                    </button>
                    <button className="btn--icon" title="Reset seen" onClick={() => resetSite(s.id)}>↺</button>
                    <button className="btn--icon danger" title="Remove" onClick={() => deleteSite(s.id)}>✕</button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Config — Telegram */}
          <div className="card">
            <div className="card__head">
              <div className="card__title"><span className="icon">✈️</span> Telegram (Instant)</div>
              <span className="badge badge--tg">Recommended</span>
            </div>
            <div className="steps">
              {[
                <>Open Telegram → search <strong>@BotFather</strong> → send <code>/newbot</code> → copy the <strong>token</strong></>,
                <>Search <strong>@userinfobot</strong> → send any message → copy your <strong>Chat ID</strong></>,
                <>Paste both below → click <strong>Save &amp; Test</strong></>,
              ].map((t, i) => (
                <div key={i} className="step">
                  <div className="step__num">{i + 1}</div>
                  <div className="step__text">{t}</div>
                </div>
              ))}
            </div>
            <div className="field">
              <label className="field__label" htmlFor="bot-token">Bot Token</label>
              <input id="bot-token" className="field__input field__input--mono"
                placeholder="123456789:AAH..."
                value={config.bot_token || ''} onChange={e => setConfig(c => ({ ...c, bot_token: e.target.value }))} />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="chat-id">Your Chat ID</label>
              <input id="chat-id" className="field__input field__input--mono"
                placeholder="5615448613"
                value={config.chat_id || ''} onChange={e => setConfig(c => ({ ...c, chat_id: e.target.value }))} />
            </div>
            <div className="btn-row">
              <button id="btn-save-tg" className="btn btn--tg" disabled={testingTg} onClick={async () => { await saveConfig(); testTelegram() }}>
                {testingTg ? '⏳ Sending…' : '✈️ Save & Test Telegram'}
              </button>
              <button className="btn btn--outline" disabled={saving} onClick={saveConfig}>
                {saving ? 'Saving…' : '💾 Save'}
              </button>
            </div>
          </div>
        </div>

        {/* ── RIGHT COL ──────────────────────────────────────────────── */}
        <div className="col">

          {/* Job Feed */}
          <div className="card">
            <div className="card__head">
              <div className="card__title"><span className="icon">📋</span> Job Feed</div>
              <button className="btn btn--sm btn--outline" onClick={clearLog}>Clear</button>
            </div>

            {log.length === 0 ? (
              <div className="empty">
                <div className="empty__icon">🔍</div>
                <div className="empty__text">No jobs yet.<br />Add some companies and the watcher will alert you within 5 minutes.</div>
              </div>
            ) : (
              <div className="job-feed">
                {Object.entries(grouped).map(([company, items]) => (
                  <div key={company} className="company-group">
                    <div className="company-group__header">
                      <span className="company-group__name">🏢 {company}</span>
                      <span className="company-group__count">{items.length} job{items.length !== 1 ? 's' : ''}</span>
                    </div>
                    {items.map((item, i) => {
                      const exp = item.experience || ''
                      return (
                        <div key={`${item.job}${i}`} className="job-card">
                          <div className="job-card__title">{item.job}</div>
                          <div className="job-card__pills">
                            {/* Experience */}
                            <span className={expPillClass(exp)}>
                              {exp === 'Not specified' ? '📋 Exp N/A' : `💼 ${exp}`}
                            </span>
                            {/* Location */}
                            {item.location && (
                              <span className="loc-pill">📍 {item.location}</span>
                            )}
                            {/* Posted */}
                            {item.posted && (
                              <span className="posted-pill">🕐 {item.posted}</span>
                            )}
                          </div>
                          {/* Description snippet */}
                          {item.description && (
                            <div className="job-card__desc">{item.description}</div>
                          )}
                          <div className="job-card__footer">
                            <span className="job-card__time">{item.time}</span>
                            <a href={item.link || item.url} target="_blank" rel="noopener noreferrer" className="apply-btn">
                              Apply ↗
                            </a>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Gmail Backup (optional) */}
          <div className="card">
            <div className="card__head">
              <div className="card__title"><span className="icon">📧</span> Gmail Backup</div>
              <span className="badge badge--yellow">Optional</span>
            </div>
            <div className="field">
              <label className="field__label" htmlFor="gmail-user">
                Your Gmail <span className="hint">(sender)</span>
              </label>
              <input id="gmail-user" className="field__input" type="email" placeholder="you@gmail.com"
                value={config.gmail_user || ''} onChange={e => setConfig(c => ({ ...c, gmail_user: e.target.value }))} />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="gmail-pass">
                App Password <span className="hint">(not your real password — Google → App Passwords)</span>
              </label>
              <input id="gmail-pass" className="field__input field__input--mono" type="password" placeholder="xxxx xxxx xxxx xxxx"
                value={config.gmail_pass || ''} onChange={e => setConfig(c => ({ ...c, gmail_pass: e.target.value }))} />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="to-email">Notify Email</label>
              <input id="to-email" className="field__input" type="email" placeholder="your@email.com"
                value={config.to_email || ''} onChange={e => setConfig(c => ({ ...c, to_email: e.target.value }))} />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="poll-interval">
                Poll Every <span className="hint">(minutes)</span>
              </label>
              <select id="poll-interval" className="field__input"
                value={config.interval || 5} onChange={e => setConfig(c => ({ ...c, interval: parseInt(e.target.value) }))}>
                {[1, 2, 5, 10, 15, 30].map(n => <option key={n} value={n}>{n} min</option>)}
              </select>
            </div>
            <div className="btn-row">
              <button id="btn-save-config" className="btn btn--primary" disabled={saving} onClick={saveConfig}>
                {saving ? 'Saving…' : '💾 Save Config'}
              </button>
            </div>
          </div>

          {/* How it works */}
          <div className="card">
            <div className="card__head">
              <div className="card__title"><span className="icon">💡</span> How It Works</div>
            </div>
            <div className="steps">
              {[
                <><strong>Greenhouse / Lever APIs</strong> → instant JSON, date-filtered to last 48h</>,
                <><strong>JS sites (Accenture, TCS…)</strong> → Playwright renders full page → real jobs</>,
                <><strong>Static sites</strong> → BeautifulSoup HTML scrape</>,
                <>Senior roles (<em>lead, manager, architect…</em>) are auto-blocked</>,
                <>Experience starting from 2+ yrs is auto-blocked — only 0-X or 1-X allowed</>,
              ].map((t, i) => (
                <div key={i} className="step">
                  <div className="step__num">{i + 1}</div>
                  <div className="step__text">{t}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="footer">
        JobWatch Pro · 100% cloud · built for 2026 freshers ·{' '}
        <a href="https://github.com/jeevas1030-rgb/jobwatcher" target="_blank" rel="noopener noreferrer">
          GitHub ↗
        </a>
      </footer>

      {/* ── Toast container ─────────────────────────────────────────────── */}
      <div className="toast-container" aria-live="polite">
        {toasts.map(({ id, msg, type, show }) => (
          <div key={id} className={`toast toast--${type} ${show ? 'toast--show' : ''}`}>{msg}</div>
        ))}
      </div>

    </div>
  )
}
