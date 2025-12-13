// blog.js - public blog listing (posts/posts.json) + search/tags/sort + vault hint
(function(){
  "use strict";
  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  const POSTS_JSON = "posts/posts.json";
  const VAULT_URL = "vault.html";
  const SECRET_HASH = "f70d3fb537cc8312c9eb4f1f67877f1b101d5e2c88587a5d56f95c8992e4b03d"; // gating gimmick only

  function fmtDate(iso){
    // iso: YYYY-MM-DD
    try{
      const [y,m,d] = iso.split("-");
      return `${y}/${m}/${d}`;
    }catch(_e){ return iso; }
  }

  function esc(s){
    return String(s).replace(/[&<>"']/g, (m)=>({
      "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"
    }[m]));
  }

  function toKey(s){ return (s||"").trim().toLowerCase(); }

  async function loadPosts(){
    const res = await fetch(POSTS_JSON, {cache:"no-store"});
    if(!res.ok) throw new Error("posts.json not found");
    const data = await res.json();
    return Array.isArray(data) ? data : (data.posts || []);
  }

  function buildTags(posts){
    const set = new Set();
    posts.forEach(p => (p.tags||[]).forEach(t=>set.add(t)));
    return Array.from(set).sort((a,b)=>a.localeCompare(b,"ja"));
  }

  function renderChips(tags){
    const host = $("#tagChips");
    if(!host) return;
    host.innerHTML = "";
    const all = document.createElement("button");
    all.className = "chip is-active";
    all.type = "button";
    all.dataset.tag = "ALL";
    all.textContent = "すべて";
    host.appendChild(all);

    tags.forEach(t=>{
      const b = document.createElement("button");
      b.className = "chip";
      b.type = "button";
      b.dataset.tag = t;
      b.textContent = t;
      host.appendChild(b);
    });
  }

  function match(post, q, tag){
    if(tag && tag !== "ALL"){
      if(!(post.tags||[]).includes(tag)) return false;
    }
    if(!q) return true;
    const text = [
      post.title||"",
      post.summary||"",
      (post.tags||[]).join(","),
    ].join("\n").toLowerCase();
    return text.includes(q);
  }

  function sortPosts(posts, mode){
    const arr = posts.slice();
    if(mode === "new") arr.sort((a,b)=>String(b.date||"").localeCompare(String(a.date||"")));
    if(mode === "old") arr.sort((a,b)=>String(a.date||"").localeCompare(String(b.date||"")));
    if(mode === "title") arr.sort((a,b)=>String(a.title||"").localeCompare(String(b.title||""),"ja"));
    return arr;
  }

  function renderList(posts){
    const grid = $("#blogGrid");
    if(!grid) return;

    const q = toKey($("#blogSearch")?.value);
    const sort = $("#blogSort")?.value || "new";
    const activeChip = $("#tagChips .chip.is-active");
    const tag = activeChip?.dataset.tag || "ALL";

    const sorted = sortPosts(posts, sort);
    const filtered = sorted.filter(p=>match(p, q, tag));

    grid.innerHTML = filtered.map(p=>{
      const hero = p.hero ? `<img class="post-hero" src="${esc(p.hero)}" alt="">` : "";
      const tags = (p.tags||[]).map(t=>`<span class="tag">${esc(t)}</span>`).join("");
      const href = `post.html?id=${encodeURIComponent(p.id)}`;
      return `
        <article class="blog-card">
          <div class="blog-card-top">
            <div class="blog-date">${esc(fmtDate(p.date||""))}</div>
            <div class="blog-tags">${tags}</div>
          </div>
          <h3>${esc(p.title||"")}</h3>
          <p class="blog-summary">${esc(p.summary||"")}</p>
          ${hero}
          <div class="blog-actions">
            <a class="btn-primary" href="${href}">▶ 読む</a>
          </div>
        </article>
      `;
    }).join("");

    $("#blogCount").textContent = `表示: ${filtered.length} / ${posts.length} 件`;
  }

  async function tryUnlockVaultFromText(text){
    const v = (text||"").trim();
    if(!v) return false;
    const candidate = v.replace(/^秘密\s*[:：]\s*/,"");
    const h = await window._sha256Hex(candidate);
    if(h === SECRET_HASH){
      window._toast("秘密のページのヒントを表示します");
      const a = $("#vaultHint");
      if(a) a.style.display = "inline-flex";
      return true;
    }
    return false;
  }

  function hookControls(posts){
    const search = $("#blogSearch");
    const sort = $("#blogSort");
    const chips = () => $$("#tagChips .chip");

    let t = null;
    search?.addEventListener("input", ()=>{
      clearTimeout(t);
      t = setTimeout(()=>{
        renderList(posts);
        tryUnlockVaultFromText(search.value);
      }, 120);
    });
    search?.addEventListener("keydown", (e)=>{
      if(e.key === "Enter") tryUnlockVaultFromText(search.value);
    });
    sort?.addEventListener("change", ()=>renderList(posts));
    chips().forEach(ch=>{
      ch.addEventListener("click", ()=>{
        chips().forEach(x=>x.classList.remove("is-active"));
        ch.classList.add("is-active");
        renderList(posts);
      });
    });
  }

  async function init(){
    window._initThemeToggle?.();

    const hint = $("#vaultHint");
    if(hint) hint.href = VAULT_URL;

    let posts = [];
    try {
      posts = await loadPosts();
    } catch(e) {
      $("#blogGrid").innerHTML = `<div class="profile-block">posts/posts.json が見つかりませんでした。READMEの手順で追加してください。</div>`;
      return;
    }
    renderChips(buildTags(posts));
    // must hook chips after render
    renderList(posts);
    hookControls(posts);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
