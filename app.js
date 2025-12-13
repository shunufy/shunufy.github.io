
(() => {
  "use strict";

  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  // ---------------------------
  // Theme (auto / light / dark)
  // ---------------------------
  const THEME_KEY = "shunufy_theme_mode"; // auto | light | dark
  const modes = ["auto", "light", "dark"];
  const modeLabel = { auto: "自動", light: "昼", dark: "夜" };
  const modeIcon = { auto: "◑", light: "☀", dark: "☾" };

  function getSavedMode() {
    const m = localStorage.getItem(THEME_KEY);
    return modes.includes(m) ? m : "auto";
  }

  function applyTheme(mode) {
    const root = document.documentElement;
    root.dataset.themeMode = mode; // for CSS
    if (mode === "auto") {
      root.dataset.theme = "";
    } else {
      root.dataset.theme = mode;
    }
    const btn = $("#themeToggleBtn");
    if (btn) {
      btn.setAttribute("data-mode", mode);
      btn.innerHTML = `<span class="theme-ic" aria-hidden="true">${modeIcon[mode]}</span><span class="theme-tx">${modeLabel[mode]}</span>`;
      btn.setAttribute("aria-label", `テーマ: ${modeLabel[mode]}`);
    }
  }

  function initThemeToggle() {
    const btn = $("#themeToggleBtn");
    if (!btn) return;

    const saved = getSavedMode();
    applyTheme(saved);

    btn.addEventListener("click", () => {
      const cur = getSavedMode();
      const next = modes[(modes.indexOf(cur) + 1) % modes.length];
      localStorage.setItem(THEME_KEY, next);
      applyTheme(next);
      toast(`テーマ: ${modeLabel[next]}`);
    });

    // When system theme changes, re-apply auto
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener?.("change", () => {
      if (getSavedMode() === "auto") applyTheme("auto");
    });
  }

  // ---------------------------
  // Tiny toast
  // ---------------------------
  let toastTimer = null;
  function toast(msg) {
    const el = $("#toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 1600);
  }

  // ---------------------------
  // Scroll progress + back to top
  // ---------------------------
  function initScrollUI() {
    const bar = $("#scrollProgress");
    const topBtn = $("#backToTop");
    if (!bar && !topBtn) return;

    function onScroll() {
      const y = window.scrollY || document.documentElement.scrollTop || 0;
      const h = document.documentElement.scrollHeight - window.innerHeight;
      const p = h > 0 ? Math.min(1, Math.max(0, y / h)) : 0;

      if (bar) bar.style.transform = `scaleX(${p})`;
      if (topBtn) topBtn.classList.toggle("show", y > 650);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    if (topBtn) {
      topBtn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
    }
  }

  // ---------------------------
  // Active nav link highlight
  // ---------------------------
  function initNavActive() {
    const path = (location.pathname.split("/").pop() || "index.html").toLowerCase();
    $$(".nav-links a").forEach(a => {
      const href = (a.getAttribute("href") || "").toLowerCase();
      a.classList.toggle("is-active", href === path);
    });
  }

  // ---------------------------
  // Games page: search / tags / sort / modal play / copy link
  // ---------------------------
  function initGamesPage() {
    const grid = $("#gamesGrid");
    if (!grid) return;

    const cards = $$(".game-card", grid);

    // Ensure each card has dataset fields
    cards.forEach(card => {
      const title = $("h3", card)?.textContent?.trim() || "";
      const desc = $(".game-desc", card)?.textContent?.trim() || "";
      const tags = $$(".tag", card).map(t => t.textContent.trim()).filter(Boolean);
      const link = $(".btn-primary", card)?.getAttribute("href") || "";
      card.dataset.title = title;
      card.dataset.desc = desc;
      card.dataset.tags = tags.join(",");
      card.dataset.link = link;

      // Add action row
      const ops = $(".game-actions", card);
      if (!ops) {
        const actions = document.createElement("div");
        actions.className = "game-actions";
        actions.innerHTML = `
          <button class="btn-sub" type="button" data-act="modal">ページ内で開く</button>
          <button class="btn-sub" type="button" data-act="copy">リンクをコピー</button>
        `;
        card.appendChild(actions);
      }
    });

    const input = $("#gameSearch");
    const sortSel = $("#gameSort");
    const chipWrap = $("#tagChips");
    const countEl = $("#gameCount");

    let activeTag = "すべて";

    function getAllTags() {
      const s = new Set();
      cards.forEach(c => {
        (c.dataset.tags || "").split(",").map(x => x.trim()).filter(Boolean).forEach(t => s.add(t));
      });
      return Array.from(s).sort((a,b)=>a.localeCompare(b,"ja"));
    }

    function renderChips() {
      if (!chipWrap) return;
      const all = getAllTags();
      const total = cards.length;
      const counts = {};
      all.forEach(t => counts[t] = 0);
      cards.forEach(c => (c.dataset.tags || "").split(",").map(x=>x.trim()).filter(Boolean).forEach(t => counts[t] = (counts[t]||0)+1));

      chipWrap.innerHTML = "";
      const make = (label, n) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "chip";
        b.dataset.tag = label;
        b.textContent = `${label} (${n})`;
        b.addEventListener("click", () => {
          activeTag = label;
          update();
        });
        return b;
      };

      chipWrap.appendChild(make("すべて", total));
      all.forEach(t => chipWrap.appendChild(make(t, counts[t] || 0)));
    }

    function normalize(str) {
      return (str || "")
        .toLowerCase()
        .replace(/\s+/g, " ")
        .trim();
    }

    function matches(card, q) {
      const title = normalize(card.dataset.title);
      const desc  = normalize(card.dataset.desc);
      const tags  = normalize(card.dataset.tags);
      if (!q) return true;
      return title.includes(q) || desc.includes(q) || tags.includes(q);
    }

    function passesTag(card) {
      if (activeTag === "すべて") return true;
      const tags = (card.dataset.tags || "").split(",").map(x=>x.trim());
      return tags.includes(activeTag);
    }

    function sortCards(list) {
      const mode = sortSel?.value || "title";
      const collator = new Intl.Collator("ja", { numeric: true, sensitivity: "base" });
      if (mode === "title") {
        return list.sort((a,b) => collator.compare(a.dataset.title, b.dataset.title));
      }
      if (mode === "tag") {
        return list.sort((a,b) => collator.compare(a.dataset.tags, b.dataset.tags) || collator.compare(a.dataset.title, b.dataset.title));
      }
      return list;
    }

    function update() {
      const q = normalize(input?.value || "");
      let visible = cards.filter(c => matches(c,q) && passesTag(c));

      // Set active chip styles
      if (chipWrap) {
        $$(".chip", chipWrap).forEach(ch => ch.classList.toggle("is-active", ch.dataset.tag === activeTag));
      }

      visible = sortCards(visible);

      // Re-append in sorted order, but keep hidden ones too (for accessibility)
      cards.forEach(c => c.classList.add("is-hidden"));
      visible.forEach(c => c.classList.remove("is-hidden"));

      if (countEl) countEl.textContent = `表示: ${visible.length} / ${cards.length} 件`;
    }

    renderChips();
    update();

    input?.addEventListener("input", update);
    sortSel?.addEventListener("change", update);

    // Actions
    grid.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-act]");
      if (!btn) return;
      const card = e.target.closest(".game-card");
      if (!card) return;
      const act = btn.dataset.act;
      const link = card.dataset.link || "";
      const abs = new URL(link, location.href).toString();

      if (act === "copy") {
        navigator.clipboard?.writeText(abs).then(() => toast("リンクをコピーしました")).catch(() => toast("コピーできませんでした"));
      }
      if (act === "modal") {
        openModal(abs, card.dataset.title || "Game");
      }
    });

    // Modal open for card primary button too (shift-click)
    grid.addEventListener("click", (e) => {
      const a = e.target.closest("a.btn-primary");
      if (!a) return;
      if (e.shiftKey) {
        e.preventDefault();
        const card = e.target.closest(".game-card");
        openModal(new URL(a.getAttribute("href"), location.href).toString(), card?.dataset.title || "Game");
      }
    });
  }

  // ---------------------------
  // Modal
  // ---------------------------
  function openModal(url, title) {
    const modal = $("#modal");
    const frame = $("#modalFrame");
    const ttl = $("#modalTitle");
    if (!modal || !frame || !ttl) {
      window.open(url, "_blank", "noopener");
      return;
    }
    ttl.textContent = title;
    frame.src = url;
    modal.classList.add("open");
    document.body.classList.add("modal-open");
  }

  function closeModal() {
    const modal = $("#modal");
    const frame = $("#modalFrame");
    if (!modal || !frame) return;
    modal.classList.remove("open");
    document.body.classList.remove("modal-open");
    // Stop game audio
    frame.src = "about:blank";
  }

  function initModal() {
    const modal = $("#modal");
    if (!modal) return;

    $("#modalClose")?.addEventListener("click", closeModal);
    $("#modalOpenNew")?.addEventListener("click", () => {
      const frame = $("#modalFrame");
      if (frame?.src) window.open(frame.src, "_blank", "noopener");
    });
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal();
    });
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("open")) closeModal();
    });
  }

  // ---------------------------
  // PWA
  // ---------------------------
  function initPWA() {
    if (!("serviceWorker" in navigator)) return;
    const isLocal = location.protocol === "http:" || location.hostname === "localhost";
    // GitHub Pages is https, ok
    navigator.serviceWorker.register("sw.js").catch(()=>{});
  }

  // ---------------------------
  // Year
  // ---------------------------

  function initYear(){ const y=document.getElementById('year'); if(y) y.textContent=String(new Date().getFullYear()); }

  // ---------------------------
  // Boot
  // ---------------------------
  document.addEventListener("DOMContentLoaded", () => {
    initYear();
    initNavActive();
    initThemeToggle();
    initScrollUI();
    initGamesPage();
    initModal();
    initPWA();
  });
})();
