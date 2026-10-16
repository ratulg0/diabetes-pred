import { useMemo, useState } from 'react'
import type { ElementType, FormEvent, ReactNode } from 'react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import {
  Activity, ArrowRight, ArrowUpRight, Bell, CalendarDays,
  Check, ChevronDown, CircleHelp, ClipboardList, Download, FileHeart, HeartPulse,
  LayoutDashboard, Menu, MoreHorizontal, Search, Settings, ShieldCheck,
  SlidersHorizontal, Sparkles, Stethoscope, X, Zap,
} from 'lucide-react'
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
  BarChart, Bar, Cell,
} from 'recharts'

type Patient = { id: string; date: string; age: number; glucose: number; bmi: number; status: 'Higher risk' | 'Lower risk'; score: number }

const initialPatients: Patient[] = [
  { id: 'DP-1048', date: 'Oct 16, 2026', age: 52, glucose: 148, bmi: 31.6, status: 'Higher risk', score: 72 },
  { id: 'DP-1047', date: 'Oct 15, 2026', age: 34, glucose: 102, bmi: 25.4, status: 'Lower risk', score: 18 },
  { id: 'DP-1046', date: 'Oct 14, 2026', age: 46, glucose: 136, bmi: 29.8, status: 'Higher risk', score: 64 },
  { id: 'DP-1045', date: 'Oct 12, 2026', age: 28, glucose: 91, bmi: 22.1, status: 'Lower risk', score: 12 },
  { id: 'DP-1044', date: 'Oct 11, 2026', age: 57, glucose: 159, bmi: 34.2, status: 'Higher risk', score: 81 },
]

const glucoseTrend = [
  { day: 'Mon', value: 112 }, { day: 'Tue', value: 126 }, { day: 'Wed', value: 119 },
  { day: 'Thu', value: 138 }, { day: 'Fri', value: 131 }, { day: 'Sat', value: 145 }, { day: 'Sun', value: 128 },
]
const featureData = [
  { name: 'Glucose', value: 88 }, { name: 'Age', value: 66 }, { name: 'BMI', value: 54 },
  { name: 'Family history', value: 38 }, { name: 'Blood pressure', value: 27 },
]

function cn(...values: Array<string | false | undefined>) { return values.filter(Boolean).join(' ') }

function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const links = [
    { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
    { to: '/prediction', label: 'New assessment', icon: Activity },
    { to: '/history', label: 'Assessment history', icon: ClipboardList },
    { to: '/settings', label: 'Preferences', icon: Settings },
  ]
  return <>
    <button aria-label="Open navigation" onClick={() => setMobileOpen(true)} className="fixed left-4 top-4 z-40 rounded-xl border border-blue-100 bg-white p-2.5 text-blue-900 shadow-sm lg:hidden"><Menu size={20} /></button>
    {mobileOpen && <button aria-label="Close navigation overlay" className="fixed inset-0 z-40 bg-slate-950/30 lg:hidden" onClick={() => setMobileOpen(false)} />}
    <aside className={cn('fixed inset-y-0 left-0 z-50 flex w-[260px] flex-col border-r border-blue-100/80 bg-white px-5 py-6 transition-transform lg:translate-x-0', mobileOpen ? 'translate-x-0' : '-translate-x-full')}>
      <div className="flex items-center gap-3 px-1">
        <div className="grid h-11 w-11 place-items-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-200"><HeartPulse size={23} strokeWidth={2.4} /></div>
        <div><p className="text-[17px] font-extrabold tracking-tight text-blue-950">GlucoCare</p><p className="text-xs font-medium text-slate-400">Diabetes insights</p></div>
        <button aria-label="Close navigation" onClick={() => setMobileOpen(false)} className="ml-auto rounded-lg p-1 text-slate-400 lg:hidden"><X size={18} /></button>
      </div>
      <div className="mt-10 px-3 text-[10px] font-bold uppercase tracking-[.18em] text-slate-400">Workspace</div>
      <nav className="mt-3 space-y-1.5">
        {links.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} onClick={() => setMobileOpen(false)} className={({ isActive }) => cn('group flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm font-semibold transition', isActive ? 'bg-blue-50 text-blue-700' : 'text-slate-500 hover:bg-slate-50 hover:text-blue-800')}>
          {({ isActive }) => <><Icon size={18} className={isActive ? 'text-blue-600' : 'text-slate-400 group-hover:text-blue-600'} /><span>{label}</span>{to === '/prediction' && <span className="ml-auto rounded-md bg-blue-600 px-1.5 py-0.5 text-[10px] font-bold text-white">NEW</span>}</>}
        </NavLink>)}
      </nav>
      <div className="mt-9 px-3 text-[10px] font-bold uppercase tracking-[.18em] text-slate-400">Resources</div>
      <a href="#clinical-note" className="mt-3 flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm font-semibold text-slate-500 transition hover:bg-slate-50 hover:text-blue-800"><CircleHelp size={18} className="text-slate-400" /> Help & guidance</a>
      <div className="mt-auto">
        <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-white p-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-blue-600 shadow-sm"><ShieldCheck size={18} /></div>
          <p className="mt-3 text-sm font-bold text-blue-950">Your data, handled carefully</p>
          <p className="mt-1.5 text-xs leading-5 text-slate-500">This demo uses sample data only. No patient records are sent or stored.</p>
          <div className="mt-3 flex items-center gap-1.5 text-[11px] font-semibold text-blue-700"><Check size={13} /> Demo environment</div>
        </div>
        <div className="mt-5 flex items-center gap-3 border-t border-slate-100 pt-5">
          <div className="grid h-10 w-10 place-items-center rounded-full bg-blue-100 text-sm font-bold text-blue-700">DR</div>
          <div className="min-w-0 flex-1"><p className="truncate text-sm font-bold text-slate-800">Demo Researcher</p><p className="text-xs text-slate-400">Research workspace</p></div>
          <MoreHorizontal size={19} className="text-slate-400" />
        </div>
      </div>
    </aside>
  </>
}

function Topbar() {
  const location = useLocation()
  const titles: Record<string, string> = { '/': 'Overview', '/prediction': 'New assessment', '/history': 'Assessment history', '/settings': 'Preferences' }
  return <header className="sticky top-0 z-30 flex h-[76px] items-center justify-between border-b border-blue-100/70 bg-white/90 px-5 backdrop-blur-xl sm:px-8 lg:px-10">
    <div className="pl-12 lg:pl-0"><p className="text-xs font-medium text-slate-400">Workspace <span className="px-1.5 text-slate-300">/</span><span className="text-blue-600">{titles[location.pathname] || 'Overview'}</span></p><h1 className="mt-1 text-lg font-bold tracking-tight text-blue-950 sm:text-xl">{titles[location.pathname] || 'Overview'}</h1></div>
    <div className="flex items-center gap-2 sm:gap-4">
      <div className="hidden items-center gap-2 rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-500 md:flex"><CalendarDays size={14} className="text-blue-500" /> Oct 2026 <ChevronDown size={14} /></div>
      <button aria-label="Notifications" className="relative rounded-xl border border-slate-100 p-2.5 text-slate-500 transition hover:border-blue-100 hover:bg-blue-50 hover:text-blue-700"><Bell size={18} /><span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-blue-500 ring-2 ring-white" /></button>
      <div className="hidden h-8 w-px bg-slate-100 sm:block" />
      <div className="hidden text-right sm:block"><p className="text-xs font-bold text-slate-700">Research mode</p><p className="text-[11px] text-slate-400">Sample workspace</p></div>
    </div>
  </header>
}

function SectionTitle({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div>{eyebrow && <p className="mb-1.5 text-[10px] font-extrabold uppercase tracking-[.18em] text-blue-600">{eyebrow}</p>}<h2 className="text-2xl font-extrabold tracking-tight text-blue-950">{title}</h2>{description && <p className="mt-1.5 max-w-2xl text-sm leading-6 text-slate-500">{description}</p>}</div>{action}</div>
}

function StatCard({ label, value, detail, icon: Icon, trend, accent = 'blue' }: { label: string; value: string; detail: string; icon: ElementType; trend?: string; accent?: 'blue' | 'mint' | 'violet' }) {
  const tones = { blue: 'bg-blue-50 text-blue-600', mint: 'bg-emerald-50 text-emerald-600', violet: 'bg-violet-50 text-violet-600' }
  return <div className="rounded-2xl border border-blue-100/80 bg-white p-5 shadow-soft transition hover:-translate-y-0.5 hover:shadow-md">
    <div className="flex items-start justify-between"><div><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-2 text-3xl font-extrabold tracking-tight text-blue-950">{value}</p></div><div className={cn('grid h-11 w-11 place-items-center rounded-xl', tones[accent])}><Icon size={20} /></div></div>
    <div className="mt-4 flex items-center gap-1.5 text-xs"><span className={cn('inline-flex items-center gap-1 font-bold', trend ? 'text-emerald-600' : 'text-slate-500')}>{trend && <ArrowUpRight size={13} />}{trend || 'Updated just now'}</span><span className="text-slate-400">{detail}</span></div>
  </div>
}

function StatusBadge({ status }: { status: Patient['status'] }) {
  const high = status === 'Higher risk'
  return <span className={cn('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold', high ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700')}><span className={cn('h-1.5 w-1.5 rounded-full', high ? 'bg-amber-500' : 'bg-emerald-500')} />{status}</span>
}

function RecentTable({ patients }: { patients: Patient[] }) {
  return <div className="overflow-hidden rounded-2xl border border-blue-100/80 bg-white shadow-soft">
    <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 sm:px-6"><div><h3 className="font-bold text-blue-950">Recent assessments</h3><p className="mt-0.5 text-xs text-slate-400">Latest sample predictions</p></div><NavLink to="/history" className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 hover:text-blue-800">View history <ArrowRight size={14} /></NavLink></div>
    <div className="overflow-x-auto"><table className="w-full min-w-[620px] text-left"><thead className="bg-slate-50/80 text-[10px] font-bold uppercase tracking-wider text-slate-400"><tr><th className="px-6 py-3">Assessment ID</th><th className="px-4 py-3">Date</th><th className="px-4 py-3">Age</th><th className="px-4 py-3">Glucose</th><th className="px-4 py-3">Result</th><th className="px-6 py-3 text-right">Score</th></tr></thead><tbody className="divide-y divide-slate-50">{patients.slice(0, 4).map(p => <tr key={p.id} className="transition hover:bg-blue-50/40"><td className="px-6 py-4 text-sm font-bold text-blue-800">{p.id}</td><td className="px-4 py-4 text-xs text-slate-500">{p.date}</td><td className="px-4 py-4 text-sm text-slate-600">{p.age}</td><td className="px-4 py-4 text-sm font-semibold text-slate-700">{p.glucose} <span className="text-xs font-normal text-slate-400">mg/dL</span></td><td className="px-4 py-4"><StatusBadge status={p.status} /></td><td className="px-6 py-4 text-right text-sm font-bold text-blue-800">{p.score}%</td></tr>)}</tbody></table></div>
  </div>
}

function Dashboard({ patients }: { patients: Patient[] }) {
  return <div className="mx-auto max-w-[1440px]">
    <div className="mb-7 overflow-hidden rounded-3xl bg-gradient-to-r from-blue-700 via-blue-600 to-indigo-600 p-6 text-white shadow-lg shadow-blue-200/60 sm:p-8">
      <div className="relative z-10 flex flex-col justify-between gap-6 md:flex-row md:items-center">
        <div className="max-w-xl"><div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-[11px] font-semibold text-blue-50"><Sparkles size={13} /> Your research overview</div><h2 className="text-2xl font-extrabold tracking-tight sm:text-3xl">Better insights start with<br className="hidden sm:block" /> a clearer picture.</h2><p className="mt-3 max-w-lg text-sm leading-6 text-blue-100">Review sample assessment activity and explore the diabetes risk prediction workflow in one simple workspace.</p><NavLink to="/prediction" className="mt-5 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-blue-700 shadow-sm transition hover:bg-blue-50">Start an assessment <ArrowRight size={16} /></NavLink></div>
        <div className="hidden h-36 w-36 items-center justify-center rounded-full border border-white/20 bg-white/10 md:flex"><div className="flex h-24 w-24 items-center justify-center rounded-full border border-white/30 bg-white/10"><HeartPulse size={48} strokeWidth={1.5} /></div></div>
      </div>
    </div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard label="Assessments reviewed" value="128" detail="sample records" icon={ClipboardList} trend="+12.8%" />
      <StatCard label="Higher-risk results" value="34.9%" detail="of dataset outcomes" icon={Activity} accent="violet" />
      <StatCard label="Features available" value="8" detail="patient input fields" icon={SlidersHorizontal} accent="mint" />
      <StatCard label="Model status" value="Not trained" detail="setup in progress" icon={Zap} />
    </div>
    <div className="mt-6 grid gap-5 xl:grid-cols-[1.55fr_1fr]">
      <div className="rounded-2xl border border-blue-100/80 bg-white p-5 shadow-soft sm:p-6"><div className="flex items-start justify-between"><div><h3 className="font-bold text-blue-950">Glucose overview</h3><p className="mt-1 text-xs text-slate-400">Illustrative weekly readings · mg/dL</p></div><span className="rounded-lg bg-blue-50 px-2.5 py-1.5 text-xs font-bold text-blue-700">7 days</span></div><div className="mt-6 h-[230px]"><ResponsiveContainer width="100%" height="100%"><AreaChart data={glucoseTrend} margin={{ top: 8, right: 5, left: -18, bottom: 0 }}><defs><linearGradient id="glucoseFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3b82f6" stopOpacity={0.2} /><stop offset="95%" stopColor="#3b82f6" stopOpacity={0.01} /></linearGradient></defs><CartesianGrid stroke="#edf2fa" vertical={false} /><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} dy={10} /><YAxis domain={[70, 180]} axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} /><Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #dbeafe', fontSize: 12, boxShadow: '0 8px 24px rgba(30,64,175,.08)' }} /><Area type="monotone" dataKey="value" name="Glucose" stroke="#2563eb" strokeWidth={2.5} fill="url(#glucoseFill)" activeDot={{ r: 5, fill: '#2563eb', stroke: '#fff', strokeWidth: 2 }} /></AreaChart></ResponsiveContainer></div><div className="mt-3 flex items-center gap-2 text-xs text-slate-400"><span className="h-2 w-2 rounded-full bg-blue-500" /> Sample visualization only; not a live CGM feed.</div></div>
      <div className="rounded-2xl border border-blue-100/80 bg-white p-5 shadow-soft sm:p-6"><h3 className="font-bold text-blue-950">Key model inputs</h3><p className="mt-1 text-xs text-slate-400">Example feature importance · illustrative</p><div className="mt-5 h-[220px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={featureData} layout="vertical" margin={{ top: 0, right: 10, left: 6, bottom: 0 }}><CartesianGrid stroke="#edf2fa" horizontal={false} /><XAxis type="number" hide domain={[0, 100]} /><YAxis type="category" dataKey="name" width={94} axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} /><Tooltip cursor={{ fill: '#eff6ff' }} contentStyle={{ borderRadius: 12, border: '1px solid #dbeafe', fontSize: 12 }} /><Bar dataKey="value" name="Relative importance" radius={[0, 5, 5, 0]} barSize={13}>{featureData.map((entry, index) => <Cell key={entry.name} fill={index === 0 ? '#2563eb' : '#93c5fd'} />)}</Bar></BarChart></ResponsiveContainer></div><div className="rounded-xl bg-blue-50/70 p-3 text-xs leading-5 text-blue-800"><span className="font-bold">Note:</span> These are design placeholders, not results from a trained model.</div></div>
    </div>
    <div className="mt-6"><RecentTable patients={patients} /></div>
    <div id="clinical-note" className="mt-5 flex gap-3 rounded-2xl border border-amber-100 bg-amber-50/70 p-4"><ShieldCheck size={19} className="mt-0.5 shrink-0 text-amber-600" /><p className="text-xs leading-5 text-amber-900"><span className="font-bold">Research prototype only.</span> This interface displays sample data and illustrative charts. It does not diagnose diabetes, provide medical advice, or connect to a glucose sensor.</p></div>
  </div>
}

const fieldClass = 'mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm text-blue-950 outline-none transition placeholder:text-slate-300 focus:border-blue-400 focus:ring-4 focus:ring-blue-50'
function PredictionPage({ onAdd }: { onAdd: (p: Patient) => void }) {
  const [values, setValues] = useState({ pregnancies: '1', glucose: '110', pressure: '72', skin: '25', insulin: '90', bmi: '28.5', pedigree: '0.45', age: '32' })
  const [result, setResult] = useState<Patient | null>(null)
  const [error, setError] = useState('')
  const update = (key: keyof typeof values, value: string) => setValues(prev => ({ ...prev, [key]: value }))
  const fields: Array<{ key: keyof typeof values; label: string; unit: string; min: number; max: number; step?: string; hint: string }> = [
    { key: 'pregnancies', label: 'Pregnancies', unit: 'count', min: 0, max: 20, hint: 'Number of times pregnant' },
    { key: 'glucose', label: 'Glucose', unit: 'mg/dL', min: 1, max: 300, hint: 'Plasma glucose concentration' },
    { key: 'pressure', label: 'Blood pressure', unit: 'mmHg', min: 1, max: 200, hint: 'Diastolic blood pressure' },
    { key: 'skin', label: 'Skin thickness', unit: 'mm', min: 0, max: 100, hint: 'Triceps skinfold thickness' },
    { key: 'insulin', label: 'Insulin', unit: 'mu U/mL', min: 0, max: 1000, hint: '2-hour serum insulin' },
    { key: 'bmi', label: 'BMI', unit: 'kg/m²', min: 1, max: 100, step: '0.1', hint: 'Body mass index' },
    { key: 'pedigree', label: 'Family history score', unit: 'score', min: 0, max: 3, step: '0.01', hint: 'Diabetes pedigree function' },
    { key: 'age', label: 'Age', unit: 'years', min: 18, max: 120, hint: 'Age in years' },
  ]
  function submit(e: FormEvent) {
    e.preventDefault()
    const invalid = fields.find(f => values[f.key].trim() === '' || !Number.isFinite(Number(values[f.key])) || Number(values[f.key]) < f.min || Number(values[f.key]) > f.max)
    if (invalid) { setError('Please enter a valid ' + invalid.label.toLowerCase() + ' between ' + invalid.min + ' and ' + invalid.max + '.'); setResult(null); return }
    setError('')
    const glucose = Number(values.glucose), bmi = Number(values.bmi), age = Number(values.age)
    const score = Math.max(5, Math.min(95, Math.round((glucose * 0.32) + (bmi * 0.65) + (age * 0.22) - 28)))
    const p: Patient = { id: 'DEMO-' + String(Date.now()).slice(-5), date: new Date().toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }), age, glucose, bmi, status: score >= 50 ? 'Higher risk' : 'Lower risk', score }
    setResult(p)
    onAdd(p)
  }
  return <div className="mx-auto max-w-5xl"><SectionTitle eyebrow="Patient assessment" title="Explore a sample assessment" description="Enter the available patient measurements below. This form currently demonstrates the interface only and does not call a trained prediction model." />
    <form onSubmit={submit} className="grid gap-6 lg:grid-cols-[1fr_310px]">
      <div className="rounded-2xl border border-blue-100/80 bg-white p-5 shadow-soft sm:p-7"><div className="mb-6 flex items-center gap-3 border-b border-slate-100 pb-5"><div className="grid h-10 w-10 place-items-center rounded-xl bg-blue-50 text-blue-600"><FileHeart size={20} /></div><div><h3 className="font-bold text-blue-950">Patient measurements</h3><p className="mt-0.5 text-xs text-slate-400">All fields are required for this demo</p></div></div>
        <div className="grid gap-x-5 gap-y-5 sm:grid-cols-2">{fields.map(f => <label key={f.key} className="block"><span className="flex items-center justify-between gap-2 text-sm font-semibold text-slate-700">{f.label}<span className="text-[10px] font-medium text-slate-400">{f.unit}</span></span><input className={fieldClass} type="number" min={f.min} max={f.max} step={f.step || '1'} value={values[f.key]} onChange={e => update(f.key, e.target.value)} aria-label={f.label} /><span className="mt-1.5 block text-[11px] text-slate-400">{f.hint}</span></label>)}</div>
        {error && <div role="alert" className="mt-5 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
        <div className="mt-7 flex flex-col-reverse gap-3 border-t border-slate-100 pt-5 sm:flex-row sm:justify-between"><button type="button" onClick={() => { setValues({ pregnancies: '1', glucose: '110', pressure: '72', skin: '25', insulin: '90', bmi: '28.5', pedigree: '0.45', age: '32' }); setResult(null); setError('') }} className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold text-slate-600 transition hover:bg-slate-50">Reset fields</button><button type="submit" className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-blue-200 transition hover:bg-blue-700"><Sparkles size={16} /> Generate demo result</button></div>
      </div>
      <div className="space-y-4"><div className="rounded-2xl border border-blue-100/80 bg-gradient-to-br from-blue-50 to-white p-5"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-blue-600 shadow-sm"><Stethoscope size={20} /></div><h3 className="mt-4 font-bold text-blue-950">Before you begin</h3><ul className="mt-3 space-y-3 text-xs leading-5 text-slate-500"><li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-blue-600" /> Use consistent units for each measurement.</li><li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-blue-600" /> Avoid guessing measurements you do not have.</li><li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-blue-600" /> Missing values should be handled explicitly by the future model.</li></ul></div>
        {result ? <div className="rounded-2xl border border-blue-100 bg-white p-5 shadow-soft"><div className="flex items-center justify-between"><p className="text-xs font-bold uppercase tracking-wider text-slate-400">Demo output</p><span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-700">Not clinical</span></div><p className="mt-4 text-3xl font-extrabold text-blue-950">{result.score}%</p><p className="mt-1 text-sm font-semibold text-blue-700">Illustrative score</p><div className="mt-4 h-2 overflow-hidden rounded-full bg-blue-50"><div className="h-full rounded-full bg-blue-500" style={{ width: result.score + '%' }} /></div><div className="mt-4"><StatusBadge status={result.status} /></div><p className="mt-3 text-xs leading-5 text-slate-500">This placeholder score uses a simple illustrative formula. It is not generated by a trained model and must not be used for health decisions.</p></div> : <div className="rounded-2xl border border-dashed border-blue-200 bg-white/70 p-5 text-center"><div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-blue-50 text-blue-500"><Activity size={23} /></div><p className="mt-3 text-sm font-bold text-blue-950">Your result will appear here</p><p className="mt-1 text-xs leading-5 text-slate-400">Complete the form to preview the demo result state.</p></div>}
      </div>
    </form>
  </div>
}

function HistoryPage({ patients }: { patients: Patient[] }) {
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('All results')
  const filtered = useMemo(() => patients.filter(p => (p.id.toLowerCase().includes(query.toLowerCase()) || p.date.toLowerCase().includes(query.toLowerCase())) && (filter === 'All results' || p.status === filter)), [patients, query, filter])
  return <div className="mx-auto max-w-[1440px]"><SectionTitle eyebrow="Records" title="Assessment history" description="Browse the sample assessments created in this session. Data is held in browser memory only." action={<button onClick={() => { const csv = ['id,date,age,glucose,bmi,status,score', ...filtered.map(p => [p.id,p.date,p.age,p.glucose,p.bmi,p.status,p.score].join(','))].join('\n'); const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); const a = document.createElement('a'); a.href = url; a.download = 'assessment-history-demo.csv'; a.click(); URL.revokeObjectURL(url) }} className="inline-flex items-center justify-center gap-2 rounded-xl border border-blue-100 bg-white px-4 py-2.5 text-sm font-bold text-blue-700 shadow-sm hover:bg-blue-50"><Download size={16} /> Export CSV</button>} />
    <div className="mb-5 flex flex-col gap-3 rounded-2xl border border-blue-100/80 bg-white p-4 shadow-soft sm:flex-row"><div className="relative flex-1"><Search size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search assessment ID or date..." className="w-full rounded-xl border border-slate-200 py-3 pl-10 pr-4 text-sm outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-50" /></div><select value={filter} onChange={e => setFilter(e.target.value)} className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-600 outline-none focus:border-blue-400"><option>All results</option><option>Higher risk</option><option>Lower risk</option></select></div>
    <div className="overflow-hidden rounded-2xl border border-blue-100/80 bg-white shadow-soft"><div className="border-b border-slate-100 px-5 py-4"><p className="text-sm font-bold text-blue-950">{filtered.length} assessments</p><p className="mt-0.5 text-xs text-slate-400">Sample and session-only records</p></div><div className="overflow-x-auto"><table className="w-full min-w-[680px] text-left"><thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-400"><tr><th className="px-6 py-4">Assessment</th><th className="px-4 py-4">Date</th><th className="px-4 py-4">Age</th><th className="px-4 py-4">Glucose</th><th className="px-4 py-4">BMI</th><th className="px-4 py-4">Demo status</th><th className="px-6 py-4 text-right">Score</th></tr></thead><tbody className="divide-y divide-slate-50">{filtered.map(p => <tr key={p.id} className="hover:bg-blue-50/40"><td className="px-6 py-4 text-sm font-bold text-blue-800">{p.id}</td><td className="px-4 py-4 text-xs text-slate-500">{p.date}</td><td className="px-4 py-4 text-sm text-slate-600">{p.age}</td><td className="px-4 py-4 text-sm text-slate-600">{p.glucose} mg/dL</td><td className="px-4 py-4 text-sm text-slate-600">{p.bmi}</td><td className="px-4 py-4"><StatusBadge status={p.status} /></td><td className="px-6 py-4 text-right text-sm font-bold text-blue-800">{p.score}%</td></tr>)}</tbody></table>{filtered.length === 0 && <div className="p-12 text-center"><Search size={24} className="mx-auto text-slate-300" /><p className="mt-3 text-sm font-bold text-slate-600">No matching assessments</p><p className="mt-1 text-xs text-slate-400">Try another search or filter.</p></div>}</div></div>
    <p className="mt-4 text-xs leading-5 text-slate-400">Exported records are for UI testing only. This is not a medical record system.</p>
  </div>
}

function SettingsPage() {
  const [notifications, setNotifications] = useState(true)
  const [compact, setCompact] = useState(false)
  const [units, setUnits] = useState('mg/dL')
  const [saved, setSaved] = useState(false)
  return <div className="mx-auto max-w-3xl"><SectionTitle eyebrow="Workspace" title="Preferences" description="Adjust your local demo experience. Settings are not connected to an account or server." />
    <div className="space-y-5"><section className="rounded-2xl border border-blue-100/80 bg-white p-5 shadow-soft sm:p-6"><div className="flex items-center gap-3 border-b border-slate-100 pb-4"><div className="grid h-10 w-10 place-items-center rounded-xl bg-blue-50 text-blue-600"><SlidersHorizontal size={19} /></div><div><h3 className="font-bold text-blue-950">Display preferences</h3><p className="mt-0.5 text-xs text-slate-400">Make the workspace more comfortable to use</p></div></div>
      <div className="divide-y divide-slate-100"><SettingToggle title="Assessment notifications" description="Show visual feedback after a demo assessment." value={notifications} onChange={setNotifications} /><SettingToggle title="Compact tables" description="Prefer tighter spacing in data tables." value={compact} onChange={setCompact} /><div className="flex flex-col justify-between gap-3 py-4 sm:flex-row sm:items-center"><div><p className="text-sm font-semibold text-slate-700">Glucose display unit</p><p className="mt-1 text-xs text-slate-400">Used for labels in the UI preview.</p></div><select value={units} onChange={e => setUnits(e.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-blue-900 outline-none focus:border-blue-400"><option>mg/dL</option><option>mmol/L</option></select></div></div>
    </section><section className="rounded-2xl border border-blue-100/80 bg-white p-5 shadow-soft sm:p-6"><div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-emerald-50 text-emerald-600"><ShieldCheck size={19} /></div><div><h3 className="font-bold text-blue-950">Privacy & prototype status</h3><p className="mt-0.5 text-xs text-slate-400">Current application boundaries</p></div></div><div className="mt-4 space-y-3 text-sm text-slate-600"><div className="flex items-center justify-between gap-3"><span>Live model connection</span><span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-bold text-amber-700">Not configured</span></div><div className="flex items-center justify-between gap-3"><span>Persistent storage</span><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">Disabled</span></div><div className="flex items-center justify-between gap-3"><span>Glucose sensor connection</span><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">Not connected</span></div></div></section>
    <div className="flex items-center justify-between gap-3"><p className="text-xs text-slate-400">{saved ? 'Preferences updated for this session.' : 'Changes apply to this page preview.'}</p><button onClick={() => setSaved(true)} className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold text-white shadow-md shadow-blue-200 hover:bg-blue-700"><Check size={16} /> Save preferences</button></div></div>
  </div>
}

function SettingToggle({ title, description, value, onChange }: { title: string; description: string; value: boolean; onChange: (v: boolean) => void }) {
  return <div className="flex items-center justify-between gap-4 py-4"><div><p className="text-sm font-semibold text-slate-700">{title}</p><p className="mt-1 text-xs leading-5 text-slate-400">{description}</p></div><button type="button" role="switch" aria-checked={value} onClick={() => onChange(!value)} className={cn('relative h-6 w-11 shrink-0 rounded-full transition', value ? 'bg-blue-600' : 'bg-slate-200')}><span className={cn('absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-all', value ? 'left-[22px]' : 'left-0.5')} /></button></div>
}

export default function App() {
  const [patients, setPatients] = useState(initialPatients)
  const addPatient = (p: Patient) => setPatients(prev => [p, ...prev])
  return <div className="min-h-screen bg-canvas text-ink"><Sidebar /><div className="min-h-screen lg:pl-[260px]"><Topbar /><main className="px-4 py-6 sm:px-7 sm:py-8 lg:px-10"><Routes><Route path="/" element={<Dashboard patients={patients} />} /><Route path="/prediction" element={<PredictionPage onAdd={addPatient} />} /><Route path="/history" element={<HistoryPage patients={patients} />} /><Route path="/settings" element={<SettingsPage />} /><Route path="*" element={<Dashboard patients={patients} />} /></Routes><footer className="mt-10 flex flex-col justify-between gap-2 border-t border-blue-100/80 py-5 text-[11px] text-slate-400 sm:flex-row sm:items-center"><span>© 2026 GlucoCare · Diabetes insights prototype</span><span className="inline-flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-amber-400" /> Demo mode · No clinical predictions</span></footer></main></div></div>
}
