import React, { useMemo, useRef, useState } from "react";
import {
  Activity, AlertTriangle, BarChart3, BookOpenCheck, Check, ChevronRight,
  CircleUserRound, CloudUpload, FileSearch, FileText, Gauge, Globe2,
  History, LoaderCircle, Menu, RefreshCcw, Search, Settings2, ShieldCheck,
  Sparkles, X, Zap
} from "lucide-react";
import { analyzeDocument } from "./api.js";

const fmtPct = (v) => {
  const n = Number(v ?? 0);
  return Number.isFinite(n) ? `${n.toFixed(1)}%` : "0.0%";
};
const pick = (o, keys, fallback = 0) => {
  for (const k of keys) if (o?.[k] !== undefined && o?.[k] !== null) return o[k];
  return fallback;
};
const list = (o, keys) => {
  for (const k of keys) if (Array.isArray(o?.[k])) return o[k];
  return [];
};

function Logo() {
  return <div className="brand">
    <div className="logo">IL</div>
    <div><strong>IntegrityLens Pro <sup>v2.6</sup></strong><span>Evidence-first academic integrity analysis</span></div>
  </div>;
}

function Metric({label, value, note, tone=""}) {
  return <div className={`metric ${tone}`}>
    <div className="metric-label">{label}</div>
    <div className="metric-value">{value}</div>
    <div className="meter"><i style={{width: value === "—" ? "0%" : value}} /></div>
    {note && <div className="metric-note">{note}</div>}
  </div>;
}

function EmptyReport() {
  return <div className="empty-report">
    <div className="orb"><ShieldCheck size={34}/></div>
    <div className="eyebrow">ANALYSIS WORKSPACE</div>
    <h2>Ready when your document is.</h2>
    <p>Upload a file or paste text to inspect textual overlap, attributable web sources, quotations, paraphrase signals and AI-writing indicators.</p>
    <div className="empty-grid">
      <div><FileSearch/><strong>Source tracing</strong><span>Search and attribute discoverable overlap.</span></div>
      <div><Sparkles/><strong>AI-writing signals</strong><span>Probabilistic signals with uncertainty shown.</span></div>
      <div><BookOpenCheck/><strong>Quote-aware</strong><span>Separate quoted material from issue similarity.</span></div>
    </div>
    <div className="notice"><AlertTriangle size={18}/><span>AI-writing detection is probabilistic. Use source evidence and human review for academic decisions.</span></div>
  </div>;
}

function Results({data}) {
  const [tab, setTab] = useState("Overview");
  const similarity = pick(data, ["potential_issue_similarity","overall_similarity","similarity"]);
  const matched = pick(data, ["matched_word_coverage","all_matched_text","matched_coverage"]);
  const exact = pick(data, ["exact_near_exact_coverage","exact_coverage"]);
  const paraphrase = pick(data, ["paraphrase_coverage","likely_paraphrase"]);
  const quoted = pick(data, ["quoted_coverage","detected_quotations"]);
  const ai = pick(data, ["ai_score","ai_like_writing_signal","ai_likelihood"]);
  const sources = list(data, ["sources","attributed_sources","matches_by_source"]);
  const matches = list(data, ["matches","matched_sentences"]);
  const queries = list(data?.diagnostics || data, ["queries"]);
  const diagnostics = data?.diagnostics || {};
  const words = pick(data, ["word_count","words_analyzed"], null);

  const tabs = ["Overview","Document","Sources","Matches","AI Analysis","Diagnostics"];
  return <div className="results">
    <div className="result-head">
      <div><div className="eyebrow">INTEGRITY REPORT</div><h2>{words ? `${Number(words).toLocaleString()} words analyzed` : "Analysis complete"}</h2></div>
      <button className="ghost" onClick={() => window.print()}><FileText size={17}/> Print / PDF</button>
    </div>

    <div className="metrics">
      <Metric label="Potential issue similarity" value={fmtPct(similarity)} note="Matched text excluding detected quotations."/>
      <Metric label="All matched text" value={fmtPct(matched)}/>
      <Metric label="Exact / near-exact" value={fmtPct(exact)}/>
      <Metric label="Likely paraphrase" value={fmtPct(paraphrase)}/>
      <Metric label="Detected quotations" value={fmtPct(quoted)}/>
      <Metric label="AI-like writing signal" value={fmtPct(ai)} tone="ai" note="Probabilistic, not a finding of authorship."/>
    </div>

    <div className="web-status">
      <Globe2 size={18}/><strong>Web search:</strong>
      <span>{diagnostics.api_connected === false ? "Not connected" : "Connected"}</span>
      {diagnostics.candidate_sources !== undefined && <b>{diagnostics.candidate_sources} candidate source(s)</b>}
    </div>

    <div className="tabs">{tabs.map(t => <button key={t} className={tab===t?"active":""} onClick={()=>setTab(t)}>{t}</button>)}</div>

    <div className="tab-body">
      {tab==="Overview" && <Overview data={data} sources={sources} matches={matches}/>}
      {tab==="Document" && <DocumentView data={data}/>}
      {tab==="Sources" && <SourceView sources={sources}/>}
      {tab==="Matches" && <MatchView matches={matches}/>}
      {tab==="AI Analysis" && <AIView data={data} ai={ai}/>}
      {tab==="Diagnostics" && <DiagnosticView diagnostics={diagnostics} queries={queries}/>}
    </div>
  </div>;
}

function Overview({data,sources,matches}) {
  return <div>
    <div className="section-title"><div><h3>Evidence overview</h3><p>Review source attribution before interpreting headline percentages.</p></div></div>
    <div className="summary-grid">
      <div className="summary-card"><Globe2/><strong>{sources.length}</strong><span>Attributed sources</span></div>
      <div className="summary-card"><FileSearch/><strong>{matches.length}</strong><span>Matched passages</span></div>
      <div className="summary-card"><ShieldCheck/><strong>{data?.validation?.source_confidence ?? "—"}</strong><span>Source confidence</span></div>
    </div>
    <ReviewNotes/>
  </div>
}
function DocumentView({data}) {
  const sentences = list(data, ["matched_sentences","document_sentences"]);
  return <div><div className="section-title"><div><h3>Document evidence</h3><p>Matched passages are separated from unmatched text where the backend provides sentence evidence.</p></div></div>
    {sentences.length ? <div className="passages">{sentences.map((s,i)=><div className={`passage ${s.classification && s.classification!=="none"?"hit":""}`} key={i}><span>{i+1}</span><p>{s.sentence || s.text}</p><b>{s.similarity ? fmtPct(s.similarity) : s.classification || ""}</b></div>)}</div> : <NoData text="No sentence-level document evidence was returned for this scan."/>}
  </div>
}
function SourceView({sources}) {
  return <div><div className="section-title"><div><h3>Attributed sources</h3><p>Inspect source-level evidence rather than relying on a single score.</p></div></div>
    {sources.length ? <div className="sources">{sources.map((s,i)=><div className="source" key={i}><div className="source-index">{i+1}</div><div><strong>{s.title || s.source_title || "Source"}</strong><span>{s.url || s.source || ""}</span><p>{s.snippet || s.matched_text || ""}</p></div><div className="source-score">{fmtPct(s.similarity ?? s.word_overlap ?? s.best_similarity)}</div></div>)}</div> : <NoData text="No attributable matching sources were returned."/>}
  </div>
}
function MatchView({matches}) {
  return <div><div className="section-title"><div><h3>Matched passages</h3><p>Passage-level evidence recovered by the matching engine.</p></div></div>
    {matches.length ? <div className="sources">{matches.map((m,i)=><div className="source" key={i}><div className="source-index">{i+1}</div><div><strong>{m.classification || "Matched passage"}</strong><p>{m.sentence || m.text || m.matched_text || ""}</p><span>{m.source_title || m.source || ""}</span></div><div className="source-score">{fmtPct(m.similarity)}</div></div>)}</div> : <NoData text="No high-confidence passage overlaps were returned."/>}
  </div>
}
function AIView({data,ai}) {
  return <div><div className="section-title"><div><h3>AI-writing signal</h3><p>Stylometric indicators are probabilistic and should not be used alone to accuse or penalize a writer.</p></div></div>
    <div className="ai-panel"><div className="ai-score">{fmtPct(ai)}</div><div><strong>Model signal</strong><p>{data?.ai_label || (Number(ai)<30?"Lower signal":Number(ai)<60?"Mixed / uncertain":"Elevated signal")}</p></div></div><ReviewNotes/>
  </div>
}
function DiagnosticView({diagnostics,queries}) {
  const entries = Object.entries(diagnostics).filter(([k,v])=>!Array.isArray(v) && typeof v!=="object");
  return <div><div className="section-title"><div><h3>Search diagnostics</h3><p>Operational evidence for auditing source discovery and retrieval.</p></div></div>
    <div className="diag-grid">{entries.map(([k,v])=><div key={k}><span>{k.replaceAll("_"," ")}</span><strong>{String(v)}</strong></div>)}</div>
    {queries.length>0 && <div className="query-list"><h4>Queries</h4>{queries.map((q,i)=><div key={i}><Search size={15}/><span>{typeof q==="string"?q:(q.query||q.phrase||JSON.stringify(q))}</span></div>)}</div>}
  </div>
}
function ReviewNotes(){
  return <div className="review-notes"><ShieldCheck size={22}/><div><strong>Human review matters</strong><p>Similarity is evidence of textual overlap, not automatically misconduct. Quotations, citations, common language and source context should be inspected before conclusions are drawn.</p></div></div>
}
function NoData({text}){return <div className="no-data"><FileSearch/><span>{text}</span></div>}

export default function App(){
  const inputRef = useRef();
  const [text,setText]=useState("");
  const [file,setFile]=useState(null);
  const [drag,setDrag]=useState(false);
  const [searchWeb,setSearchWeb]=useState(true);
  const [excludeBib,setExcludeBib]=useState(true);
  const [loading,setLoading]=useState(false);
  const [result,setResult]=useState(null);
  const [error,setError]=useState("");
  const words=useMemo(()=>text.trim()?text.trim().split(/\s+/).length:0,[text]);

  const choose = f => {
    if(!f) return;
    const ok = /\.(pdf|docx|txt|md)$/i.test(f.name);
    if(!ok){setError("Please choose a PDF, DOCX, TXT or MD file.");return}
    setFile(f); setError("");
  };
  async function run(){
    if(!file && !text.trim()){setError("Upload a document or paste text before running an analysis.");return}
    setLoading(true);setError("");
    try{setResult(await analyzeDocument({file,text,searchWeb,excludeBibliography:excludeBib}));}
    catch(e){setError(e?.response?.data?.detail || e?.response?.data?.message || e.message || "Analysis failed.");}
    finally{setLoading(false)}
  }

  return <div className="app">
    <header>
      <Logo/>
      <nav><button className="nav-active"><Zap/>New Scan</button><button><History/>History</button><button><BarChart3/>Reports</button></nav>
      <div className="header-actions"><div className="status"><i/> Engine online</div><button className="icon-btn"><Settings2/></button><button className="icon-btn"><CircleUserRound/></button></div>
    </header>

    <main>
      <section className="intro">
        <div><div className="eyebrow light">DOCUMENT INTEGRITY WORKSPACE</div><h1>Check originality.<br/>Trace the evidence.</h1><p>Source-aware plagiarism analysis and AI-writing signals designed for careful human review.</p></div>
        <div className="trust"><ShieldCheck/><div><strong>Evidence-first analysis</strong><span>Exact overlap • paraphrase signals • source attribution • quote-aware scoring</span></div></div>
      </section>

      <section className="workspace">
        <aside className="input-card">
          <div className="card-head"><div><div className="eyebrow">DOCUMENT</div><h2>Analyze document</h2></div><span className="step">01</span></div>

          {!file ? <div className={`dropzone ${drag?"drag":""}`}
            onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)}
            onDrop={e=>{e.preventDefault();setDrag(false);choose(e.dataTransfer.files?.[0])}}
            onClick={()=>inputRef.current?.click()}>
            <input ref={inputRef} type="file" hidden accept=".pdf,.docx,.txt,.md" onChange={e=>choose(e.target.files?.[0])}/>
            <div className="upload-icon"><CloudUpload/></div><strong>Drop your document here</strong><span>or click to browse</span><small>PDF, DOCX, TXT or MD</small>
          </div> :
          <div className="selected-file"><div className="file-icon"><FileText/></div><div><strong>{file.name}</strong><span>{(file.size/1024/1024).toFixed(2)} MB • Ready for analysis</span></div><button onClick={()=>setFile(null)}><X/></button></div>}

          <div className="divider"><span>OR PASTE TEXT</span></div>
          <div className="editor">
            <textarea value={text} onChange={e=>setText(e.target.value)} placeholder="Paste the document text here..."/>
            <div className="editor-foot"><span>{words.toLocaleString()} words</span><span>{text.length.toLocaleString()} characters</span></div>
          </div>

          <div className="options">
            <label><span><Globe2/>Search live web sources</span><input type="checkbox" checked={searchWeb} onChange={e=>setSearchWeb(e.target.checked)}/></label>
            <label><span><BookOpenCheck/>Exclude bibliography</span><input type="checkbox" checked={excludeBib} onChange={e=>setExcludeBib(e.target.checked)}/></label>
          </div>
          {error && <div className="error"><AlertTriangle/>{error}</div>}
          <button className="analyze" disabled={loading} onClick={run}>{loading?<><LoaderCircle className="spin"/>Searching, matching & validating…</>:<>Analyze document <ChevronRight/></>}</button>
          <div className="privacy"><ShieldCheck/>Your report should be interpreted with source evidence and human judgment.</div>
        </aside>

        <article className="report-card">
          {loading ? <div className="loading-state"><div className="scan-orb"><LoaderCircle className="spin"/></div><h2>Analyzing your document</h2><p>Extracting text, generating search queries, retrieving candidate sources and validating passage overlap.</p><div className="progress"><i/></div><div className="loading-steps"><span><Check/>Text extraction</span><span><Activity/>Source discovery</span><span><Gauge/>Match validation</span></div></div> : result ? <Results data={result}/> : <EmptyReport/>}
        </article>
      </section>
    </main>
    <footer><Logo/><span>IntegrityLens Pro v2.6 • Evidence before inference.</span></footer>
  </div>
}
