// shared.js - helpers: toast, theme toggle, sha256, nav injection
(function(){
  "use strict";
  const $ = (sel, root=document) => root.querySelector(sel);

  // Toast
  function toast(msg){
    const t = $("#toast");
    if(!t) return;
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toast._timer);
    toast._timer = setTimeout(()=>t.classList.remove("show"), 1700);
  }
  window._toast = toast;

  // SHA-256 hex
  async function sha256Hex(str){
    const enc = new TextEncoder().encode(str);
    const buf = await crypto.subtle.digest("SHA-256", enc);
    return [...new Uint8Array(buf)].map(b=>b.toString(16).padStart(2,"0")).join("");
  }
  window._sha256Hex = sha256Hex;

  // Theme
  const MODE_KEY = "shunufy_theme_mode";
  function applyTheme(mode){
    const html = document.documentElement;
    const m = mode || "auto";
    html.setAttribute("data-theme-mode", m);
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const effective = (m === "auto") ? (prefersDark ? "dark" : "light") : m;
    html.setAttribute("data-theme", effective);

    const btn = $("#themeToggle");
    if(btn){
      const icon = btn.querySelector(".theme-ic");
      const text = btn.querySelector(".theme-tx");
      if(m === "auto"){ icon.textContent = "◐"; text.textContent = "自動"; }
      if(m === "light"){ icon.textContent = "☀"; text.textContent = "昼"; }
      if(m === "dark"){ icon.textContent = "☾"; text.textContent = "夜"; }
    }
  }
  function nextMode(mode){
    if(mode === "auto") return "light";
    if(mode === "light") return "dark";
    return "auto";
  }
  function initThemeToggle(){
    const saved = localStorage.getItem(MODE_KEY) || "auto";
    applyTheme(saved);

    const btn = $("#themeToggle");
    if(btn){
      btn.addEventListener("click", ()=>{
        const cur = localStorage.getItem(MODE_KEY) || "auto";
        const nxt = nextMode(cur);
        localStorage.setItem(MODE_KEY, nxt);
        applyTheme(nxt);
      });
    }
    if(window.matchMedia){
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", ()=>{
        const cur = localStorage.getItem(MODE_KEY) || "auto";
        if(cur === "auto") applyTheme("auto");
      });
    }
  }
  window._initThemeToggle = initThemeToggle;

  // Inject "ブログ" link into nav if not exists
  function injectBlogLink(){
    const nav = document.querySelector(".nav-links");
    if(!nav) return;
    const has = Array.from(nav.querySelectorAll("a")).some(a => (a.getAttribute("href")||"").includes("blog.html"));
    if(has) return;
    const a = document.createElement("a");
    a.href = "blog.html";
    a.textContent = "ブログ";
    const themeBtn = nav.querySelector("#themeToggle, .theme-toggle");
    if(themeBtn) nav.insertBefore(a, themeBtn);
    else nav.appendChild(a);
  }

  document.addEventListener("DOMContentLoaded", ()=>{
    injectBlogLink();
  });
})();
