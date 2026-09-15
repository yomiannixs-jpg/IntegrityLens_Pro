import React,{useState} from "react";
import {api} from "./api.js";

const Metric=({title,value,note})=><div className="metric"><small>{title}</small><b>{value}</b>{note&&<span>{note}</span>}</div>;

export default function App(){
 const [text,setText]=useState(""); const [file,setFile]=useState(null);
 const [searchWeb,setSearchWeb]=useState(true); const [loading,setLoading]=useState(false);
 const [result,setResult]=useState(null); const [tab,setTab]=useState("Overview"); const [error,setError]=useState("");
 async function run(){
   setLoading(true);setError("");
   const fd=new FormData();fd.append("text",text);fd.append("search_web",String(searchWeb));if(file)fd.append("file",file);
   try{const r=await api.post("/api/analyze",fd);setResult(r.data)}
   catch(e){setError(e?.response?.data?.detail||e.message)}
   finally{setLoading(false)}
 }
 const web=result?.web||{};
 return <div>
  <header><div className="brand"><div className="logo">IL</div><div><strong>IntegrityLens Pro <sup>v2.5</sup></strong><p>Evidence-first plagiarism & AI-writing analysis</p></div></div><div className="badge">Cascading Search • Exact Quotes • Snippet Evidence • Diagnostics</div></header>
  <main>
   <section className="input card"><div className="eyebrow">DOCUMENT</div><h2>Analyze text</h2><p>Paste text or upload TXT, MD, DOCX, or PDF.</p>
    <textarea value={text} onChange={e=>setText(e.target.value)} placeholder="Paste the document here..."/>
    <input type="file" accept=".txt,.md,.pdf,.docx" onChange={e=>setFile(e.target.files?.[0]||null)}/>
    <label className="check"><input type="checkbox" checked={searchWeb} onChange={e=>setSearchWeb(e.target.checked)}/> Search live web sources</label>
    <button disabled={loading||(!text.trim()&&!file)} onClick={run}>{loading?"Searching exact phrases, fetching, matching...":"Run IntegrityLens v2.5"}</button>
    {error&&<div className="error">{error}</div>}
   </section>
   <section className="report card">
    {!result?<div className="empty"><div className="round">2.5</div><h2>Source-discovery report will appear here</h2><p>Exact-phrase search, fallback queries, snippets, fetched pages and passage matches are separately auditable.</p></div>:<>
     <div className="reporthead"><div><div className="eyebrow">INTEGRITY REPORT</div><h2>{result.engine?.document_sentences||0} sentences analyzed</h2></div><button className="print" onClick={()=>window.print()}>Print / PDF</button></div>
     <div className="metrics">
      <Metric title="Potential issue similarity" value={`${result.overall_similarity}%`}/>
      <Metric title="All matched text" value={`${result.matched_word_coverage}%`}/>
      <Metric title="Exact / near-exact" value={`${result.exact_near_exact_coverage}%`}/>
      <Metric title="Likely paraphrase" value={`${result.paraphrase_coverage}%`}/>
      <Metric title="Detected quotations" value={`${result.quoted_coverage}%`}/>
      <Metric title="AI-like writing signal" value={`${result.ai?.score}%`} note={result.ai?.label}/>
     </div>
     <div className={"webbar "+(web.api_connected?"good":"bad")}><b>Web search:</b> {web.api_connected?"Connected":"Not connected"} · {web.candidate_sources||0} candidate source(s)</div>
     <div className="diag">
      <Metric title="Queries attempted" value={web.queries_attempted??0}/><Metric title="Queries successful" value={web.queries_successful??0}/>
      <Metric title="Candidate URLs" value={web.candidate_urls??0}/><Metric title="HTML fetched" value={web.html_pages_fetched??0}/>
      <Metric title="PDFs fetched" value={web.pdfs_fetched??0}/><Metric title="Pages failed" value={web.pages_failed??0}/>
      <Metric title="Matched sources" value={web.matched_sources??0}/>
     </div>
     <div className="tabs">{["Overview","Sources","Matches","Queries","AI"].map(x=><button className={tab===x?"active":""} onClick={()=>setTab(x)} key={x}>{x}</button>)}</div>
     {tab==="Overview"&&<div><h3>Top attributed sources</h3>{result.sources?.length?result.sources.slice(0,8).map((s,i)=><div className="source" key={i}><b>{s.title}</b><span>{s.matched_words} matched words · best {s.best_similarity}%</span><a href={s.url} target="_blank">{s.url}</a></div>):<div className="notice">No attributable matching sources were found.</div>}</div>}
     {tab==="Sources"&&<div><h3>Attributed sources</h3>{result.sources?.map((s,i)=><div className="source" key={i}><b>{s.title}</b><a href={s.url} target="_blank">{s.url}</a></div>)}</div>}
     {tab==="Matches"&&<div><h3>Matched passages</h3>{result.matches?.length?result.matches.map((m,i)=><div className="match" key={i}><b>{m.classification} · {m.similarity}%</b><p>{m.sentence}</p><small>{m.source_title}</small></div>):<div className="notice">No high-confidence passage overlaps were found.</div>}</div>}
     {tab==="Queries"&&<div><h3>Search audit</h3><p className="muted">These are the manuscript phrases actually sent to web discovery.</p>{web.queries?.map((q,i)=><div className="query" key={i}><b>{q.mode}</b><code>{q.query}</code><span>{q.results?.length||0} result(s)</span>{q.results?.slice(0,3).map((r,j)=><small key={j}>{r.title} — {r.url}</small>)}</div>)}</div>}
     {tab==="AI"&&<div><h3>AI-writing signal</h3><div className="notice">{result.ai?.warning}</div><pre>{JSON.stringify(result.ai?.features,null,2)}</pre></div>}
    </>}
   </section>
  </main>
 </div>
}
