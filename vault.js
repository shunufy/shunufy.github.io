// vault.js - 'secret' public posts behind a gimmick lock
(function(){
  "use strict";
  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  const SECRET_HASH = "f70d3fb537cc8312c9eb4f1f67877f1b101d5e2c88587a5d56f95c8992e4b03d";
  const UNLOCK_KEY = "shunufy_vault_unlocked";

  function esc(s){ return String(s).replace(/[&<>"']/g, (m)=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[m])); }
  function fmtDate(iso){ try{ const [y,m,d]=iso.split("-"); return `${y}/${m}/${d}`; }catch(_e){ return iso; } }

  async function loadPosts(){
    const res = await fetch("secret/secret-posts.json", {cache:"no-store"});
    if(!res.ok) throw new Error("secret-posts.json not found");
    const data = await res.json();
    return Array.isArray(data) ? data : (data.posts || []);
  }

  async function tryUnlock(pass){
    const h = await window._sha256Hex((pass||"").trim());
    if(h === SECRET_HASH){
      localStorage.setItem(UNLOCK_KEY, "1");
      window._toast("いらっしゃいませ（演出です）");
      return true;
    }
    window._toast("違いますわ");
    return false;
  }

  function showUnlocked(){ $("#lockedBox").style.display="none"; $("#unlockedBox").style.display="block"; }
  function showLocked(){ $("#lockedBox").style.display="block"; $("#unlockedBox").style.display="none"; }

  function render(posts){
    const grid = $("#vaultGrid");
    const q = ($("#vaultSearch")?.value || "").trim().toLowerCase();
    const filtered = posts.filter(p=>{
      if(!q) return true;
      const text = [p.title||"", p.summary||"", (p.tags||[]).join(",")].join("\n").toLowerCase();
      return text.includes(q);
    });
    grid.innerHTML = filtered.map(p=>{
      const tags = (p.tags||[]).map(t=>`<span class="tag">${esc(t)}</span>`).join("");
      const href = `post.html?set=secret&id=${encodeURIComponent(p.id)}`;
      return `
        <article class="blog-card">
          <div class="blog-card-top">
            <div class="blog-date">${esc(fmtDate(p.date||""))}</div>
            <div class="blog-tags">${tags}</div>
          </div>
          <h3>${esc(p.title||"")}</h3>
          <p class="blog-summary">${esc(p.summary||"")}</p>
          <div class="blog-actions">
            <a class="btn-primary" href="${href}">▶ 読む</a>
          </div>
        </article>
      `;
    }).join("");
    $("#vaultCount").textContent = `表示: ${filtered.length} / ${posts.length} 件`;
  }

  async function init(){
    window._initThemeToggle?.();

    // lock state
    const unlocked = localStorage.getItem(UNLOCK_KEY) === "1";
    if(unlocked) showUnlocked(); else showLocked();

    $("#unlockForm")?.addEventListener("submit", async (e)=>{
      e.preventDefault();
      const ok = await tryUnlock($("#unlockInput").value);
      $("#unlockInput").value = "";
      if(ok){ showUnlocked(); }
    });

    let posts = [];
    try{ posts = await loadPosts(); }catch(_e){
      $("#vaultGrid").innerHTML = `<div class="profile-block">secret/secret-posts.json が見つかりませんでした。</div>`;
      return;
    }

    const search = $("#vaultSearch");
    let t = null;
    search?.addEventListener("input", ()=>{
      clearTimeout(t);
      t = setTimeout(()=>render(posts), 120);
    });

    render(posts);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
