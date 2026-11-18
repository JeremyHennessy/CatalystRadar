/* Exact retained issuer navigation only. No name/ticker identity resolution. */
(function(){'use strict';
function parse(search=''){const p=new URLSearchParams(search),values=p.getAll('company_cik'),ids=p.getAll('evidence_id');if(!values.length&&!ids.length)return null;if(values.length!==1||!/^\d{1,10}$/.test(values[0])||Number(values[0])===0||ids.length>1||(ids.length&&!/^[a-z_]+:[a-f0-9]{24}$/.test(ids[0])))return{valid:false};return{valid:true,cik:values[0].padStart(10,'0'),recordId:ids[0]||null};}
function current(){return parse(typeof location==='undefined'?'':location.search);}
function href(cik){if(!/^\d{10}$/.test(cik)||Number(cik)===0)throw Error('Invalid issuer CIK');return'datasets.html?company_cik='+cik+'#company-investigation';}
function link(doc,parent,cik){const a=doc.createElement('a');a.href=href(cik);a.setAttribute('style','display:inline-block;padding:6px 0');a.textContent='Investigate issuer CIK '+cik+' across retained sources';const row=doc.createElement('p');row.append(a);parent.append(row);return a;}
const api={parse,current,href,link};if(typeof module!=='undefined')module.exports=api;if(typeof window!=='undefined')window.CatalystCompanyRoute=api;
})();
