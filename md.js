// md.js - tiny markdown renderer (safe subset)
(function(){
  "use strict";

  function esc(s){
    return String(s).replace(/[&<>"']/g, (m)=>({
      "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"
    }[m]));
  }

  function renderInline(s){
    s = esc(s);
    // images ![alt](url)
    s = s.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_m, alt, url)=>`<img class="post-img" alt="${alt}" src="${url}">`);
    // links [text](url)
    s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_m, txt, url)=>`<a href="${url}" target="_blank" rel="noopener">${txt}</a>`);
    // inline code `code`
    s = s.replace(/`([^`]+)`/g, (_m, code)=>`<code>${code}</code>`);
    // bold **text**
    s = s.replace(/\*\*([^*]+)\*\*/g, (_m, b)=>`<strong>${b}</strong>`);
    // italic *text*
    s = s.replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, (_m, pre, it)=>`${pre}<em>${it}</em>`);
    return s;
  }

  function mdToHtml(md){
    const lines = String(md).replace(/\r\n/g,"\n").split("\n");
    let html = "";
    let inCode = false;
    let codeBuf = [];
    let inList = false;

    function flushList(){
      if(inList){ html += "</ul>"; inList = false; }
    }
    function flushCode(){
      if(inCode){
        html += `<pre><code>${esc(codeBuf.join("\n"))}</code></pre>`;
        inCode = false;
        codeBuf = [];
      }
    }

    for(const raw of lines){
      const line = raw;

      if(line.trim().startsWith("```")){
        if(inCode){ flushCode(); }
        else{ flushList(); inCode = true; }
        continue;
      }
      if(inCode){ codeBuf.push(line); continue; }

      // headings
      const m1 = line.match(/^(#{1,3})\s+(.*)$/);
      if(m1){
        flushList();
        const lvl = m1[1].length;
        html += `<h${lvl}>${renderInline(m1[2])}</h${lvl}>`;
        continue;
      }

      // list
      const m2 = line.match(/^\s*[-*]\s+(.*)$/);
      if(m2){
        if(!inList){ html += "<ul>"; inList = true; }
        html += `<li>${renderInline(m2[1])}</li>`;
        continue;
      }else{
        flushList();
      }

      // blank
      if(line.trim()===""){ html += "<div class='sp'></div>"; continue; }

      // paragraph
      html += `<p>${renderInline(line)}</p>`;
    }

    flushList();
    flushCode();
    return html;
  }

  window._mdToHtml = mdToHtml;
})();
