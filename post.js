// post.js - single post viewer (post.html?id=xxx&set=posts|secret)
(function(){
  "use strict";
  const $ = (sel, root=document) => root.querySelector(sel);

  function getParam(name){
    const u = new URL(location.href);
    return u.searchParams.get(name) || "";
  }
  function esc(s){
    return String(s).replace(/[&<>"']/g, (m)=>({
      "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"
    }[m]));
  }
  function fmtDate(iso){
    try{
      const [y,m,d] = iso.split("-");
      return `${y}/${m}/${d}`;
    }catch(_e){ return iso; }
  }

  async function loadIndex(set){
    const path = (set === "secret") ? "secret/secret-posts.json" : "posts/posts.json";
    const res = await fetch(path, {cache:"no-store"});
    if(!res.ok) throw new Error("index not found");
    const data = await res.json();
    return Array.isArray(data) ? data : (data.posts || []);
  }

  async function loadMd(path){
    const res = await fetch(path, {cache:"no-store"});
    if(!res.ok) throw new Error("md not found");
    return await res.text();
  }

  function setMeta(p){
    $("#postTitle").textContent = p.title || "";
    $("#postDate").textContent = fmtDate(p.date || "");
    $("#postTags").innerHTML = (p.tags||[]).map(t=>`<span class="tag">${esc(t)}</span>`).join("");
  }

  async function init(){
    window._initThemeToggle?.();

    const id = getParam("id");
    const set = getParam("set") || "posts";

    if(!id){
      $("#postBody").innerHTML = "<p>記事IDがありません。</p>";
      return;
    }

    let posts = [];
    try{
      posts = await loadIndex(set);
    }catch(_e){
      $("#postBody").innerHTML = "<p>記事一覧が読み込めませんでした。</p>";
      return;
    }

    const p = posts.find(x=>String(x.id) === String(id));
    if(!p){
      $("#postBody").innerHTML = "<p>その記事は見つかりませんでした。</p>";
      return;
    }

    setMeta(p);

    try{
      const md = await loadMd(p.file);
      const html = window._mdToHtml ? window._mdToHtml(md) : `<pre>${esc(md)}</pre>`;
      $("#postBody").innerHTML = html;
    }catch(_e){
      $("#postBody").innerHTML = "<p>本文が読み込めませんでした。</p>";
    }

    // Back link
    const back = $("#backLink");
    if(back){
      back.href = (set === "secret") ? "vault.html" : "blog.html";
      back.textContent = (set === "secret") ? "← 秘密ページに戻る" : "← ブログに戻る";
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
