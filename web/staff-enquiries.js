"use strict";
(async () => {
  const identity=window.capitalBridgeIdentity;
  const company=document.getElementById("enquiry-company");
  const refresh=document.getElementById("enquiry-refresh");
  const rows=document.getElementById("enquiry-rows");
  const status=document.getElementById("enquiry-status");
  const message=document.getElementById("enquiry-message");
  if(!company||!refresh||!rows||!status||!message)return;
  let requestVersion=0;
  let roles=new Map();
  const forward={new:'in_review',in_review:'responded',responded:'closed'};
  const labels={in_review:'In review',responded:'Responded',closed:'Closed'};
  function clear(){rows.replaceChildren();}
  function notice(text){message.textContent=text;}
  async function api(path,{method='GET',body}={}){
    const withBearer=identity&&typeof identity.getAccessToken==="function";
    const headers={Accept:"application/json",...(body?{"Content-Type":"application/json"}:{})};
    let endpoint="/api/v1"+path;
    if(withBearer){
      const token=await identity.getAccessToken();
      if(typeof token!=="string"||!token)throw Error("Staff sign-in required.");
      headers.Authorization="Bearer "+token;
    }else{
      // HttpOnly session BFF: no bearer token and no user-set browser credentials.
      endpoint=path==="/me/companies"
        ? "/api/v1/staff/consultations/companies"
        : "/api/v1"+path.replace(/\/companies\/([0-9a-f-]+)\/consultations/i,
            "/staff/consultations/companies/$1/enquiries");
    }
    const response=await fetch(endpoint,{method,headers,body:body?JSON.stringify(body):undefined,credentials:"same-origin",cache:"no-store",redirect:"error"});
    if(!response.ok)throw Error("Unable to retrieve authorised enquiries ("+response.status+").");
    return response.json();
  }
  async function changeStatus(companyId,enquiryId,next,button){
    if(roles.get(companyId)!=="director")return;
    button.disabled=true;
    notice("Saving enquiry status…");
    try{
      const result=await api("/companies/"+encodeURIComponent(companyId)+"/consultations/"+encodeURIComponent(enquiryId)+"/status",{method:"PATCH",body:{status:next}});
      if(result.company_id!==companyId||result.id!==enquiryId||result.status!==next)throw Error("Unexpected update response.");
      if(company.value===companyId)await load();
    }catch(error){
      notice(error.message||"Unable to update enquiry.");
      button.disabled=false;
    }
  }
  async function load(){
    const version=++requestVersion, id=company.value;
    clear();status.textContent="Loading";notice("Loading enquiries…");
    try{
      if(!/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(id))throw Error("Select an authorised company.");
      const result=await api("/companies/"+encodeURIComponent(id)+"/consultations?limit=100");
      if(version!==requestVersion||id!==company.value)return;
      if(result.company_id!==id||!Array.isArray(result.enquiries))throw Error("Company response mismatch.");
      for(const item of result.enquiries){
        const tr=document.createElement("tr");
        const fields=[
          item.created_at ? new Date(item.created_at).toLocaleDateString() : "—",
          item.name, item.service, item.message, item.status
        ];
        for(const [i,value] of fields.entries()){
          const td=document.createElement("td");
          td.textContent=String(value??"—");
          if(i===3)td.className="enquiry-text";
          tr.appendChild(td);
        }
        if(roles.get(id)==="director"&&forward[item.status]&&/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(String(item.id||""))){
          const actions=document.createElement("td");
          const button=document.createElement("button");
          button.type="button";button.className="advance-status";
          button.textContent="Mark "+labels[forward[item.status]];
          button.setAttribute("aria-label","Advance enquiry for "+String(item.name||"client")+" to "+labels[forward[item.status]]);
          button.addEventListener("click",()=>changeStatus(id,item.id,forward[item.status],button));
          actions.appendChild(button);tr.appendChild(actions);
        }else tr.appendChild(document.createElement("td"));
        rows.appendChild(tr);
      }
      status.textContent=result.enquiries.length+" enquiries";
      notice(result.enquiries.length?"Latest authorised enquiries shown.":"No enquiries for this company.");
    }catch(error){
      if(version!==requestVersion)return;
      clear();status.textContent="Unavailable";notice(error.message||"Unable to load enquiries.");
    }
  }
  company.addEventListener("change",()=>{requestVersion++;refresh.disabled=!company.value;load();});
  refresh.addEventListener("click",load);
  document.addEventListener("visibilitychange",()=>{if(!document.hidden&&company.value)load();});
  // Until the authenticated multi-instance socket fanout is deployed,
  // refresh the authorised queue while visible without leaking tokens into URLs.
  setInterval(()=>{if(!document.hidden&&company.value)load();},30000);
  try{
    const result=await api("/me/companies");
    if(!result||!Array.isArray(result.companies))throw Error("Authorised companies unavailable.");
    roles=new Map();
    company.replaceChildren();
    const prompt=document.createElement("option");prompt.value="";prompt.textContent="Choose company";company.appendChild(prompt);
    for(const c of result.companies){
      if(typeof c.id!=="string"||typeof c.name!=="string")continue;
      roles.set(c.id,c.role);
      const option=document.createElement("option");option.value=c.id;option.textContent=c.name;company.appendChild(option);
    }
    company.disabled=false;status.textContent="Ready";notice("Select an authorised company to load enquiries.");
  }catch(error){
    company.disabled=true;refresh.disabled=true;
    status.textContent="Sign-in required";notice(error.message||"Authorisation unavailable.");
  }
})();