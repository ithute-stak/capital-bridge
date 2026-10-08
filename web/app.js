"use strict";
// Illustrative demo only. No production data, storage, or network calls.
const invoices=[
{ref:"INV-2026-014",client:"Maseru Business Group",division:"Consultancy",date:"2026-10-07",status:"Issued",amount:17250,net:15000},
{ref:"INV-2026-013",client:"Lesotho Education Partners",division:"Training",date:"2026-10-06",status:"Paid",amount:8625,net:7500},
{ref:"INV-2026-012",client:"Southern Mobility Client",division:"Immigration",date:"2026-10-04",status:"Issued",amount:4600,net:4000},
{ref:"INV-2026-011",client:"Maseru Engineering Co.",division:"Engineering",date:"2026-10-02",status:"Paid",amount:23000,net:20000},
{ref:"INV-2026-010",client:"Tech Services Partner",division:"IT",date:"2026-10-01",status:"Overdue",amount:11500,net:10000}
];
const quotations=[
{ref:"Q-2026-022",client:"Regional Mobility Group",division:"Immigration",date:"2026-10-08",status:"Accepted",amount:6900},
{ref:"Q-2026-021",client:"Maseru Business Group",division:"Consultancy",date:"2026-10-07",status:"Approved",amount:17250},
{ref:"Q-2026-020",client:"Tech Services Partner",division:"IT",date:"2026-10-06",status:"Draft",amount:9200},
{ref:"Q-2026-019",client:"Training Academy",division:"Training",date:"2026-10-02",status:"Rejected",amount:5750}
];
const receipts=[
{ref:"RCT-2026-023",client:"Lesotho Education Partners",division:"Training",date:"2026-10-07",status:"Paid",amount:8625},
{ref:"RCT-2026-022",client:"Maseru Engineering Co.",division:"Engineering",date:"2026-10-03",status:"Paid",amount:23000}
];
const ledger=[
{ref:"INV:INV-2026-014",client:"Accounts receivable / revenue",division:"Consultancy",date:"2026-10-07",status:"Posted",amount:17250},
{ref:"RCT:RCT-2026-023",client:"Bank / accounts receivable",division:"Training",date:"2026-10-07",status:"Posted",amount:8625},
{ref:"INV:INV-2026-013",client:"Accounts receivable / revenue",division:"Training",date:"2026-10-06",status:"Posted",amount:8625}
];
const datasets={overview:invoices,quotations,invoices,receipts,ledger};
const headings={overview:["Finance overview","Your financial performance, all in one place."],quotations:["Quotations","Track offers, decisions and client acceptance."],invoices:["Invoices","Review service invoices and outstanding amounts."],receipts:["Receipts","Review recorded client payments."],ledger:["General ledger","Sample journal references and posting activity."]};
const money=n=>new Intl.NumberFormat("en-LS",{style:"currency",currency:"LSL",minimumFractionDigits:2}).format(n);
const safe=t=>String(t).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const state={section:"overview"};
const $=id=>document.getElementById(id);
function renderOverview(){
$("metric-invoiced").textContent=money(invoices.reduce((s,r)=>s+r.amount,0));
$("metric-received").textContent=money(receipts.reduce((s,r)=>s+r.amount,0));
$("metric-outstanding").textContent=money(invoices.reduce((s,r)=>s+r.amount,0)-receipts.reduce((s,r)=>s+r.amount,0));
$("metric-accepted").textContent=money(quotations.filter(r=>r.status==="Accepted").reduce((s,r)=>s+r.amount,0));
const divisions=[...new Set(invoices.map(r=>r.division))].map(name=>({name,value:invoices.filter(r=>r.division===name).reduce((s,r)=>s+r.net,0)})).sort((a,b)=>b.value-a.value);
const max=Math.max(1,...divisions.map(x=>x.value));
$("division-chart").innerHTML=divisions.map(x=>'<div><div class="bar-label"><span>'+safe(x.name)+'</span><b>'+money(x.value)+'</b></div><div class="track"><div class="fill" style="width:'+Math.round(x.value/max*100)+'%"></div></div></div>').join("");
$("activity-list").innerHTML=[...receipts.map(x=>({...x,type:"Receipt recorded"})),...quotations.map(x=>({...x,type:"Quotation "+x.status.toLowerCase()}))].sort((a,b)=>b.date.localeCompare(a.date)).slice(0,4).map(x=>'<div class="activity-row"><span class="dot">↗</span><div><strong>'+safe(x.type)+' · '+safe(x.ref)+'</strong><small>'+safe(x.client)+' · '+safe(x.date)+'</small></div></div>').join("");
}
function rows(){const needle=$("search").value.trim().toLowerCase(),status=$("status").value;return datasets[state.section].filter(r=>(status==="all"||r.status===status)&&(!needle||[r.ref,r.client,r.division].some(s=>s.toLowerCase().includes(needle))));}
function renderRows(){const data=rows();$("records-count").textContent=data.length+" records";$("record-rows").innerHTML=data.length?data.map(r=>'<tr><td>'+safe(r.ref)+'</td><td>'+safe(r.client)+'</td><td>'+safe(r.division)+'</td><td>'+safe(r.date)+'</td><td><span class="status-chip '+safe(r.status.toLowerCase())+'">'+safe(r.status)+'</span></td><td class="amount">'+money(r.amount)+'</td></tr>').join(""):'<tr><td colspan="6">No records match your search.</td></tr>';}
function setSection(section){state.section=datasets[section]?section:"overview";$("overview").classList.toggle("hidden",state.section!=="overview");$("section-heading").textContent=headings[state.section][0];$("section-description").textContent=headings[state.section][1];$("breadcrumb").textContent=headings[state.section][0];$("records-heading").textContent=state.section==="overview"?"Recent invoices":headings[state.section][0];$("records-subtitle").textContent="Illustrative "+state.section+" records";document.querySelectorAll("#navigation a").forEach(a=>{const active=a.dataset.section===state.section;a.classList.toggle("active",active);if(active)a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");});$("search").value="";$("status").innerHTML='<option value="all">All statuses</option>'+[...new Set(datasets[state.section].map(r=>r.status))].sort().map(s=>'<option value="'+safe(s)+'">'+safe(s)+'</option>').join("");renderRows();}
function exportCurrent(){const columns=["Reference","Client","Division","Date","Status","Amount LSL"];const cells=v=>'"'+String(v).replace(/"/g,'""')+'"';const csv=[columns,...rows().map(r=>[r.ref,r.client,r.division,r.date,r.status,r.amount.toFixed(2)])].map(row=>row.map(cells).join(",")).join("\r\n");const blob=new Blob([csv],{type:"text/csv;charset=utf-8"}),url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="capitalbridge-demo-"+state.section+".csv";document.body.append(a);a.click();a.remove();URL.revokeObjectURL(url);}
document.querySelectorAll("#navigation a").forEach(a=>a.addEventListener("click",e=>{e.preventDefault();setSection(a.dataset.section);history.replaceState(null,"","#"+a.dataset.section);}));
$("search").addEventListener("input",renderRows);$("status").addEventListener("change",renderRows);$("export").addEventListener("click",exportCurrent);
renderOverview();setSection(decodeURIComponent(location.hash.slice(1))||"overview");