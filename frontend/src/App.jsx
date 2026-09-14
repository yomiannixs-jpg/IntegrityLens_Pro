import {useMemo,useState} from "react";
import {motion} from "framer-motion";
import {api} from "./api";

const labels={exact_or_near_exact:"Exact / near-exact",likely_paraphrase:"Likely paraphrase",weak_similarity:"Weak similarity",none:"No notable overlap"};

function Score({label,value,tone,note}){
  const v=Math.max(0,Math.min(100,Number(value||0)));
  return <div className={`score ${tone}`}><span>{label}</span><strong>{v.toFixed(1)}%</strong><div className="track"><div className="fill" style={{width:`${v}%`}}/></div>{note&&<p>{note}</p>}</div>
}

function Sources({rows=[]}){
  if(!rows.length)return <div className="empty">No attributable matching sources were found.</div>;
  return <div className="sources">{rows.map(s=><div className="source" key={s.id}><div><strong>{s.title}</strong><a href={s.source?.startsWith("http")?s.source:undefined} target="_blank" rel="noreferrer">{s.source}</a><small>{s.matched_sentence_count} sentence(s) · {s.exact_sentence_count} exact · {s.paraphrase_sentence_count} paraphrase</small></div><b>{s.contribution}%</b></div>)}</div>
}

function DocumentView({rows=[]}){
  return <div className="doc">{rows.map(r=><span key={r.index} className={`sent ${r.classification} ${r.quoted?"quoted":""}`} title={`${labels[r.classification]} · ${r.similarity}%${r.source_title?` · ${r.source_title}`:""}`}>{r.text} </span>)}</div>
}

export default function App(){
  const[text,setText]=useState("");
  const[file,setFile]=useState(null);
  const[includeWeb,setIncludeWeb]=useState(false);
  const[result,setResult]=useState(null);
  const[busy,setBusy]=useState(false);
  const[error,setError]=useState("");
  const[tab,setTab]=useState("overview");

  const can=useMemo(()=>(file||text.trim().split(/\s+/).length>=20)&&!busy,[file,text,busy]);

  async function analyze(){
    try{
      setBusy(true);setError("");setResult(null);setTab("overview");
      let res;
      if(file){
        const f=new FormData();f.append("file",file);f.append("include_web",String(includeWeb));
        res=await api.post("/api/analyze-file",f);
      }else{
        res=await api.post("/api/analyze",{text,include_web:includeWeb});
      }
      setResult(res.data);
    }catch(e){setError(e.response?.data?.detail||e.message||"Analysis failed.");}
    finally{setBusy(false);}
  }

  return <div className="app">
    <header><div className="brand"><div className="mark">IL</div><div><strong>IntegrityLens Pro <sup>v2</sup></strong><span>Evidence-first plagiarism & AI-writing analysis</span></div></div><div className="badge">Source-aware • Quote-aware • Human-review ready</div></header>

    <main className="shell">
      <motion.section className="hero" initial={{opacity:0,y:12}} animate={{opacity:1,y:0}}>
        <div><span className="eyebrow">IntegrityLens Pro v2</span><h1>Plagiarism evidence that shows what matched, where, and why.</h1><p>Multi-passage web discovery, source retrieval, exact and paraphrase matching, quote-aware coverage, attribution, and AI-writing signals.</p></div>
        <div className="proof"><div><b>Exact overlap</b><span>Phrase continuity + lexical similarity</span></div><div><b>Paraphrase</b><span>Sentence-level similarity</span></div><div><b>Coverage</b><span>Share of submitted text attributable to sources</span></div></div>
      </motion.section>

      <section className="workspace">
        <div className="panel">
          <span className="eyebrow dark">Document</span><h2>Analyze text</h2><p className="muted">Paste text or upload TXT, MD, DOCX, or PDF.</p>
          <textarea value={text} placeholder="Paste the document here..." onChange={e=>{setText(e.target.value);setFile(null)}}/>
          <div className="controls">
            <label className="upload"><input type="file" accept=".txt,.md,.docx,.pdf" onChange={e=>{setFile(e.target.files?.[0]||null);if(e.target.files?.[0])setText("")}}/><span>{file?`Selected: ${file.name}`:"Upload document"}</span></label>
            <label className="check"><input type="checkbox" checked={includeWeb} onChange={e=>setIncludeWeb(e.target.checked)}/><span>Search live web sources</span></label>
            <button disabled={!can} onClick={analyze}>{busy?"Searching and analyzing...":"Run IntegrityLens v2"}</button>
          </div>
          {includeWeb&&<p className="tiny">Live web search requires SERPER_API_KEY on the backend.</p>}
          {error&&<div className="error">{error}</div>}
        </div>

        <div className="panel result">
          {!result?<div className="placeholder"><div className="orb">v2</div><h3>Evidence will appear here</h3><p>Exact overlap, likely paraphrase, quotation coverage, sources, and AI-like writing signals are reported separately.</p></div>:
          <motion.div initial={{opacity:0}} animate={{opacity:1}}>
            <div className="reporthead"><div><span className="eyebrow dark">Integrity report</span><h2>{result.summary.word_count.toLocaleString()} words analyzed</h2></div><button className="print" onClick={()=>window.print()}>Print / PDF</button></div>

            <div className="scores">
              <Score label="Potential issue similarity" value={result.summary.potential_issue_similarity} tone="orange" note="Matched text excluding detected quotations."/>
              <Score label="All matched text" value={result.summary.matched_text_coverage} tone="red"/>
              <Score label="Exact / near-exact" value={result.summary.exact_near_exact_coverage} tone="blue"/>
              <Score label="Likely paraphrase" value={result.summary.paraphrase_coverage} tone="purple"/>
              <Score label="Detected quotations" value={result.summary.quoted_coverage} tone="green"/>
              <Score label="AI-like writing signal" value={result.summary.ai_likelihood} tone="slate" note={result.ai_detection.label}/>
            </div>

            <div className="status"><b>Web discovery:</b> {result.web_discovery.enabled?`${result.web_discovery.source_count} candidate source(s) retrieved`:result.web_discovery.message}</div>

            <div className="tabs">
              {["overview","document","sources","matches","ai"].map(x=><button key={x} className={tab===x?"active":""} onClick={()=>setTab(x)}>{x[0].toUpperCase()+x.slice(1)}</button>)}
            </div>

            {tab==="overview"&&<><h3>Top sources</h3><Sources rows={result.plagiarism.sources.slice(0,6)}/></>}
            {tab==="document"&&<><h3>Highlighted document</h3><p className="tiny">Hover over a sentence to inspect its match type and source.</p><DocumentView rows={result.plagiarism.document_sentences}/></>}
            {tab==="sources"&&<><h3>Attributed sources</h3><Sources rows={result.plagiarism.sources}/></>}
            {tab==="matches"&&<><h3>Matched passages</h3><div className="matches">{result.plagiarism.matches?.length?result.plagiarism.matches.slice(0,25).map((m,i)=><div className={`match ${m.classification}`} key={i}><div><b>{labels[m.classification]}</b><strong>{m.similarity}%</strong></div><p><b>Your text:</b> {m.sentence}</p><p><b>Source:</b> {m.matched_text}</p><a href={m.source?.startsWith("http")?m.source:undefined} target="_blank" rel="noreferrer">{m.source_title}</a></div>):<div className="empty">No high-confidence passage overlaps were found.</div>}</div></>}
            {tab==="ai"&&<><div className="aisummary"><b>{result.ai_detection.label}</b><span>Confidence: {result.ai_detection.confidence}</span><p>{result.ai_detection.warning}</p></div><div className="signals">{result.ai_detection.signals?.map(s=><div className="signal" key={s.name}><div><b>{s.name}</b><p>{s.explanation}</p></div><strong>{s.value}%</strong></div>)}</div></>}

            <div className="notes"><b>Review notes</b><ul>{result.limitations.map(x=><li key={x}>{x}</li>)}</ul></div>
          </motion.div>}
        </div>
      </section>
    </main>
  </div>
}
