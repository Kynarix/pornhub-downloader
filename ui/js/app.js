/* Hub Downloader — Pornhub UI */
(() => {
  const $ = (sel) => document.querySelector(sel);
  const DISCORD = "ashtwix";

  const PAGE_META = {
    download: { title: "İndir", sub: "Link yapıştır, kaliteyi seç, indir.", eye: "İndirme" },
    search: { title: "Ara", sub: "Pornhub içinde ara.", eye: "Arama" },
    browse: { title: "Göz at", sub: "Trendler ve kategoriler.", eye: "Keşfet" },
    favorites: { title: "Favoriler", sub: "Kaydettiklerin.", eye: "Koleksiyon" },
    queue: { title: "Kuyruk", sub: "Aktif indirmeler.", eye: "İndirmeler" },
    history: { title: "Geçmiş", sub: "Bitenler.", eye: "Geçmiş" },
    settings: { title: "Ayarlar", sub: "Tema, klasör, tercihler.", eye: "Tercihler" },
  };

  const state = {
    settings: null,
    video: null,
    jobs: [],
    ready: false,
    pollTimer: null,
    lastDone: new Set(),
    currentView: "download",
    search: { query: "", page: 1, hasMore: false },
    browse: { category: "hot", page: 1, hasMore: false, sections: [], categories: [] },
  };

  function api() {
    return window.pywebview?.api;
  }

  async function waitForBridge(timeoutMs = 15000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const a = api();
      if (a?.ping) {
        try {
          const res = await a.ping();
          if (res?.ok) return true;
        } catch (_) {}
      }
      await new Promise((r) => setTimeout(r, 120));
    }
    return false;
  }

  async function call(method, ...args) {
    const a = api();
    if (!a || typeof a[method] !== "function") {
      throw new Error("Uygulama köprüsü henüz hazır değil");
    }
    return a[method](...args);
  }

  function setHint(id, text, isError = false) {
    const el = $(id);
    if (!el) return;
    el.textContent = text || "";
    el.classList.toggle("error", !!isError);
  }

  let toastTimer;
  function toast(msg) {
    const el = $("#toast");
    el.textContent = msg;
    el.classList.remove("hidden");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.add("hidden"), 2200);
  }

  function escapeHtml(s) {
    return String(s || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function fmtDuration(sec) {
    if (!sec && sec !== 0) return "";
    const s = Math.floor(sec);
    const m = Math.floor(s / 60);
    const h = Math.floor(m / 60);
    if (h) return `${h}:${String(m % 60).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
    return `${m}:${String(s % 60).padStart(2, "0")}`;
  }

  function fmtSize(n) {
    if (!n) return "";
    const u = ["B", "KB", "MB", "GB"];
    let v = n, i = 0;
    while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
    return `${v.toFixed(1)} ${u[i]}`;
  }

  function statusLabel(s) {
    return ({ queued: "Sırada", running: "İniyor", done: "Bitti", error: "Hata", cancelled: "İptal" })[s] || s;
  }

  function renderVideoGrid(container, items, emptyText) {
    if (!items?.length) {
      container.innerHTML = `
        <div class="grid-empty">
          <span class="material-icons-outlined big-dim">movie_filter</span>
          <p>${escapeHtml(emptyText || "Sonuç yok.")}</p>
        </div>`;
      return;
    }
    container.innerHTML = items.map((item) => {
      const dur = item.duration_text || fmtDuration(item.duration) || "";
      const favClass = item.favorited ? "fav-on" : "";
      const favPayload = encodeURIComponent(JSON.stringify({
        id: item.id,
        title: item.title,
        url: item.url,
        thumbnail: item.thumbnail,
        duration: item.duration,
        duration_text: item.duration_text || dur,
      }));
      const dlPayload = encodeURIComponent(JSON.stringify({
        url: item.url,
        title: item.title,
        thumbnail: item.thumbnail,
      }));
      return `
        <article class="vcard" data-id="${escapeHtml(item.id)}">
          <div class="vcard-thumb">
            <img src="${escapeHtml(item.thumbnail || "")}" alt="" loading="lazy" />
            ${dur ? `<span class="vcard-dur">${escapeHtml(dur)}</span>` : ""}
            <div class="vcard-actions">
              <button class="btn-icon ${favClass}" type="button" data-fav="${favPayload}" title="Favori">
                <span class="material-icons-outlined">favorite</span>
              </button>
            </div>
          </div>
          <div class="vcard-body">
            <div class="vcard-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</div>
            <div class="vcard-row">
              <button class="btn-primary" type="button" data-dl-best="${dlPayload}">
                <span class="material-icons-outlined">download</span> İndir
              </button>
              <button class="btn-tonal" type="button" data-open-url="${escapeHtml(item.url)}">Detay</button>
            </div>
          </div>
        </article>`;
    }).join("");
  }

  function showLoading(container, text) {
    container.innerHTML = `
      <div class="loading-box">
        <div class="spinner"></div>
        <span>${escapeHtml(text || "Yükleniyor…")}</span>
      </div>`;
  }

  /* ---------- preview / download tab ---------- */
  function renderPreview(video) {
    $("#preview").classList.remove("hidden");
    $("#preview-thumb").src = video.thumbnail || "";
    $("#preview-title").textContent = video.title || "";
    const bits = [];
    if (video.uploader) bits.push(video.uploader);
    if (video.duration) bits.push(fmtDuration(video.duration));
    $("#preview-meta").textContent = bits.join(" · ");
    const sel = $("#format-select");
    sel.innerHTML = "";
    (video.formats || []).forEach((f, idx) => {
      const opt = document.createElement("option");
      opt.value = f.format_id;
      const size = fmtSize(f.filesize);
      opt.textContent = size ? `${f.label} · ${size}` : f.label;
      if (idx === 0) opt.selected = true;
      sel.appendChild(opt);
    });
  }

  async function doResolve(url) {
    if (!state.ready) {
      setHint("#resolve-hint", "Köprü henüz hazır değil.", true);
      return;
    }
    url = (url || $("#url-input").value).trim();
    if (!url) {
      setHint("#resolve-hint", "Bir Pornhub URL’si gir.", true);
      return;
    }
    $("#url-input").value = url;
    $("#btn-resolve").disabled = true;
    setHint("#resolve-hint", "Video bilgisi alınıyor…");
    $("#preview").classList.add("hidden");
    try {
      const result = await call("resolve_url", url);
      if (!result?.ok) {
        setHint("#resolve-hint", result?.error || "Video alınamadı", true);
        return;
      }
      state.video = result.video;
      renderPreview(result.video);
      setHint("#resolve-hint", "Hazır — kalite seçip kuyruğa ekle.");
      toast("Video hazır");
      switchView("download");
    } catch (e) {
      setHint("#resolve-hint", e.message, true);
    } finally {
      $("#btn-resolve").disabled = false;
    }
  }

  /* ---------- search ---------- */
  async function runSearch(page = 1) {
    const query = $("#search-input").value.trim();
    if (!query) {
      setHint("#search-hint", "Bir şey yaz.", true);
      return;
    }
    state.search.query = query;
    state.search.page = page;
    showLoading($("#search-grid"), "Aranıyor…");
    setHint("#search-hint", `"${query}" aranıyor…`);
    $("#search-pager").classList.add("hidden");
    try {
      const res = await call("search", query, page);
      if (!res?.ok) {
        setHint("#search-hint", res?.message || res?.error || "Arama başarısız", true);
        renderVideoGrid($("#search-grid"), [], "Sonuç yok.");
        return;
      }
      state.search.hasMore = !!res.has_more;
      setHint("#search-hint", `${res.items?.length || 0} sonuç · sayfa ${page}`);
      renderVideoGrid($("#search-grid"), res.items || [], "Sonuç bulunamadı.");
      $("#search-page-label").textContent = String(page);
      $("#search-pager").classList.toggle("hidden", page <= 1 && !res.has_more);
      $("#search-prev").disabled = page <= 1;
      $("#search-next").disabled = !res.has_more;
    } catch (e) {
      setHint("#search-hint", e.message, true);
      renderVideoGrid($("#search-grid"), [], e.message);
    }
  }

  /* ---------- browse ---------- */
  function renderBrowseChips() {
    const sec = $("#browse-sections");
    const cats = $("#browse-categories");
    sec.innerHTML = (state.browse.sections || []).map((s) => `
      <button class="chip ${state.browse.category === s.id ? "active" : ""}" type="button" data-browse="${escapeHtml(s.id)}">${escapeHtml(s.label)}</button>
    `).join("");
    cats.innerHTML = (state.browse.categories || []).map((c) => `
      <button class="chip ${state.browse.category === c.id ? "active" : ""}" type="button" data-browse="${escapeHtml(c.id)}">${escapeHtml(c.label)}</button>
    `).join("");
  }

  async function runBrowse(category, page = 1) {
    state.browse.category = category || state.browse.category || "hot";
    state.browse.page = page;
    renderBrowseChips();
    showLoading($("#browse-grid"), "Yükleniyor…");
    setHint("#browse-hint", "İçerik çekiliyor…");
    $("#browse-pager").classList.add("hidden");
    try {
      const res = await call("browse", state.browse.category, page);
      if (res.sections) state.browse.sections = res.sections;
      if (res.categories) state.browse.categories = res.categories;
      renderBrowseChips();
      if (!res?.ok) {
        setHint("#browse-hint", res?.message || res?.error || "Yüklenemedi", true);
        renderVideoGrid($("#browse-grid"), [], "İçerik yok.");
        return;
      }
      state.browse.hasMore = !!res.has_more;
      setHint("#browse-hint", `${res.label || state.browse.category} · ${res.items?.length || 0} video · sayfa ${page}`);
      renderVideoGrid($("#browse-grid"), res.items || [], "İçerik yok.");
      $("#browse-page-label").textContent = String(page);
      $("#browse-pager").classList.toggle("hidden", page <= 1 && !res.has_more);
      $("#browse-prev").disabled = page <= 1;
      $("#browse-next").disabled = !res.has_more;
    } catch (e) {
      setHint("#browse-hint", e.message, true);
      renderVideoGrid($("#browse-grid"), [], e.message);
    }
  }

  async function loadCatalog() {
    try {
      const res = await call("list_catalog");
      if (res?.ok) {
        state.browse.sections = res.sections || [];
        state.browse.categories = res.categories || [];
        renderBrowseChips();
      }
    } catch (_) {}
  }

  /* ---------- favorites ---------- */
  async function renderFavorites() {
    const grid = $("#favorites-grid");
    showLoading(grid, "Favoriler…");
    try {
      const res = await call("get_favorites");
      const items = (res.items || []).map((i) => ({ ...i, favorited: true }));
      $("#fav-status").textContent = `${items.length} favori`;
      renderVideoGrid(grid, items, "Henüz favori yok. Kalbe basarak ekle.");
    } catch (e) {
      renderVideoGrid(grid, [], e.message);
    }
  }

  /* ---------- queue (incremental) ---------- */
  function jobSubText(j) {
    return [j.format_label, j.speed, j.eta ? `ETA ${j.eta}` : "", j.error].filter(Boolean).join(" · ");
  }
  function badgeText(j) {
    return j.status === "running" ? `${statusLabel(j.status)} ${Math.round(j.progress || 0)}%` : statusLabel(j.status);
  }

  function syncQueue(jobs) {
    const list = $("#job-list");
    let empty = list.querySelector(".empty-state");
    if (!empty) {
      empty = document.createElement("div");
      empty.className = "empty-state";
      empty.innerHTML = `<span class="material-icons-outlined">inbox</span><p>Kuyruk boş</p>`;
      list.appendChild(empty);
    }
    if (!jobs.length) {
      list.querySelectorAll(".job").forEach((el) => el.remove());
      empty.classList.remove("hidden");
      $("#queue-status").textContent = "Boşta";
      return;
    }
    empty.classList.add("hidden");
    const running = jobs.filter((j) => j.status === "running").length;
    const queued = jobs.filter((j) => j.status === "queued").length;
    $("#queue-status").textContent = running || queued ? `${running} aktif · ${queued} sırada` : `${jobs.length} kayıt`;

    const seen = new Set();
    for (const j of jobs) {
      seen.add(j.id);
      let el = list.querySelector(`[data-job-id="${CSS.escape(j.id)}"]`);
      if (!el) {
        el = document.createElement("article");
        el.className = "job is-new";
        el.dataset.jobId = j.id;
        el.innerHTML = `
          <div><div class="job-title"></div><div class="job-sub"></div></div>
          <div class="job-actions">
            <span class="badge"></span>
            <button class="btn-tonal btn-cancel" type="button">İptal</button>
            <button class="btn-tonal btn-open hidden" type="button">Aç</button>
          </div>
          <div class="progress hidden"><span></span></div>`;
        list.appendChild(el);
        el.addEventListener("animationend", () => el.classList.remove("is-new"), { once: true });
      }
      const title = el.querySelector(".job-title");
      const sub = el.querySelector(".job-sub");
      const badge = el.querySelector(".badge");
      const cancelBtn = el.querySelector(".btn-cancel");
      const openBtn = el.querySelector(".btn-open");
      const progress = el.querySelector(".progress");
      const fill = progress.querySelector("span");

      if (title.textContent !== j.title) title.textContent = j.title || "";
      const st = jobSubText(j);
      if (sub.textContent !== st) sub.textContent = st;
      const bt = badgeText(j);
      if (badge.textContent !== bt) badge.textContent = bt;
      badge.className = `badge ${j.status}`;

      const canCancel = j.status === "queued" || j.status === "running";
      cancelBtn.classList.toggle("hidden", !canCancel);
      cancelBtn.dataset.cancel = j.id;
      const canOpen = j.status === "done" && !!j.filepath;
      openBtn.classList.toggle("hidden", !canOpen);
      if (canOpen) openBtn.dataset.open = j.filepath;

      const showBar = j.status === "running" || j.status === "queued";
      progress.classList.toggle("hidden", !showBar);
      if (showBar) {
        const w = `${Math.max(0, Math.min(100, j.progress || 0))}%`;
        if (fill.style.width !== w) fill.style.width = w;
      }
    }
    list.querySelectorAll(".job").forEach((el) => {
      if (!seen.has(el.dataset.jobId)) el.remove();
    });
  }

  async function renderHistory() {
    const list = $("#history-list");
    try {
      const res = await call("get_history");
      const items = res.items || [];
      if (!items.length) {
        list.innerHTML = `<div class="empty-state"><span class="material-icons-outlined">history</span><p>Henüz indirme yok</p></div>`;
        return;
      }
      list.innerHTML = items.map((h) => `
        <article class="job">
          <div>
            <div class="job-title">${escapeHtml(h.title)}</div>
            <div class="job-sub">${escapeHtml(h.format_label || "")} · ${statusLabel(h.status)}</div>
          </div>
          <div class="job-actions">
            ${h.filepath ? `<button class="btn-tonal" data-open="${escapeHtml(h.filepath)}" type="button">Aç</button>` : ""}
          </div>
        </article>`).join("");
    } catch (e) {
      list.innerHTML = `<div class="empty-state"><p>${escapeHtml(e.message)}</p></div>`;
    }
  }

  function applyTheme(settings) {
    const theme = settings?.theme || "ph";
    const appearance = settings?.appearance || "dark";
    const motion = settings?.animations === false ? "off" : "on";
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.setAttribute("data-appearance", appearance);
    document.documentElement.setAttribute("data-motion", motion);
  }

  function renderSettingsUI(settings) {
    const themes = settings.themes || [];
    const grid = $("#palette-grid");
    if (grid) {
      grid.innerHTML = themes.map((t) => {
        const [p1, p2] = t.preview || ["#000", t.accent];
        const active = settings.theme === t.id ? "active" : "";
        return `
          <button class="palette ${active}" type="button" data-theme-id="${escapeHtml(t.id)}">
            <div class="palette-swatch" style="--p1:${escapeHtml(p1)};--p2:${escapeHtml(p2)}"></div>
            <div class="palette-name">${escapeHtml(t.label)}</div>
          </button>`;
      }).join("");
    }
    document.querySelectorAll("#appearance-seg button").forEach((b) => {
      b.classList.toggle("active", b.dataset.appearance === settings.appearance);
    });
    const anim = $("#opt-animations");
    if (anim) anim.checked = settings.animations !== false;
    const best = $("#opt-auto-best");
    if (best) best.checked = settings.auto_best_quality !== false;
    const conc = $("#opt-concurrent");
    if (conc) conc.value = String(settings.concurrent_downloads || 1);
    const folder = $("#settings-folder");
    if (folder) folder.textContent = settings.download_dir || "";
  }

  async function saveSettings(patch) {
    const res = await call("update_settings", patch);
    if (!res.ok) throw new Error(res.error || "Kaydedilemedi");
    applySettings(res.settings);
    toast("Ayarlar kaydedildi");
    return res.settings;
  }

  function switchView(name) {
    if (!PAGE_META[name]) return;
    state.currentView = name;
    document.querySelectorAll(".page").forEach((v) => v.classList.remove("active"));
    document.querySelectorAll(".nav-item[data-view]").forEach((b) => b.classList.remove("active"));
    $(`#view-${name}`)?.classList.add("active");
    document.querySelector(`.nav-item[data-view="${name}"]`)?.classList.add("active");
    $("#page-title").textContent = PAGE_META[name].title;
    $("#page-sub").textContent = PAGE_META[name].sub;
    const eye = $("#page-eyebrow");
    if (eye) eye.textContent = PAGE_META[name].eye || "";

    if (name === "browse" && !state.browse.sections.length) {
      loadCatalog().then(() => runBrowse(state.browse.category, 1));
    } else if (name === "browse" && !$("#browse-grid").children.length) {
      runBrowse(state.browse.category, 1);
    }
    if (name === "favorites") renderFavorites();
    if (name === "history") renderHistory();
    if (name === "queue") syncQueue(state.jobs);
    if (name === "settings" && state.settings) renderSettingsUI(state.settings);
  }

  function applySettings(settings) {
    state.settings = settings;
    applyTheme(settings);
    const folder = $("#settings-folder");
    if (folder) folder.textContent = settings.download_dir || "";
    if (state.currentView === "settings") renderSettingsUI(settings);
  }

  async function refreshQueue() {
    if (!state.ready) return;
    try {
      const q = await call("get_queue");
      if (!q.ok) return;
      const jobs = q.jobs || [];
      const done = new Set(jobs.filter((j) => j.status === "done").map((j) => j.id));
      for (const id of done) {
        if (!state.lastDone.has(id)) toast("İndirme tamamlandı");
      }
      state.lastDone = done;
      state.jobs = jobs;
      syncQueue(jobs);
    } catch (_) {}
  }

  async function boot() {
    setHint("#resolve-hint", "Bağlanıyor…");
    const ok = await waitForBridge();
    if (!ok) {
      setHint("#resolve-hint", "Köprü kurulamadı. Yeniden başlat.", true);
      return;
    }
    state.ready = true;
    try {
      const s = await call("get_settings");
      if (s.ok) applySettings(s.settings);
      await refreshQueue();
      clearInterval(state.pollTimer);
      state.pollTimer = setInterval(refreshQueue, 700);
      await loadCatalog();
      setHint("#resolve-hint", "URL yapıştır ve Enter’a bas.");
    } catch (e) {
      setHint("#resolve-hint", e.message, true);
    }
  }

  /* events */
  $("#btn-resolve").addEventListener("click", () => doResolve());
  $("#url-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); doResolve(); }
  });

  $("#btn-enqueue").addEventListener("click", async () => {
    if (!state.video) return;
    const sel = $("#format-select");
    try {
      const res = await call("enqueue", {
        url: state.video.webpage_url || state.video.url,
        title: state.video.title,
        format_id: sel.value,
        format_label: sel.options[sel.selectedIndex]?.textContent || sel.value,
        thumbnail: state.video.thumbnail,
        output_dir: state.settings?.download_dir,
      });
      if (!res.ok) throw new Error(res.error || "Eklenemedi");
      toast("Kuyruğa eklendi");
      await refreshQueue();
      switchView("queue");
    } catch (e) {
      toast(e.message);
    }
  });

  $("#btn-search").addEventListener("click", () => runSearch(1));
  $("#search-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); runSearch(1); }
  });
  $("#search-prev").addEventListener("click", () => runSearch(Math.max(1, state.search.page - 1)));
  $("#search-next").addEventListener("click", () => {
    if (state.search.hasMore) runSearch(state.search.page + 1);
  });

  $("#browse-prev").addEventListener("click", () => runBrowse(state.browse.category, Math.max(1, state.browse.page - 1)));
  $("#browse-next").addEventListener("click", () => {
    if (state.browse.hasMore) runBrowse(state.browse.category, state.browse.page + 1);
  });

  document.body.addEventListener("click", async (e) => {
    const browse = e.target.closest("[data-browse]");
    if (browse) {
      runBrowse(browse.dataset.browse, 1);
      return;
    }

    const favBtn = e.target.closest("[data-fav]");
    if (favBtn) {
      try {
        const item = JSON.parse(decodeURIComponent(favBtn.getAttribute("data-fav")));
        const res = await call("toggle_favorite", item);
        if (res.ok) {
          favBtn.classList.toggle("fav-on", !!res.favorited);
          toast(res.favorited ? "Favorilere eklendi" : "Favoriden çıkarıldı");
          if (state.currentView === "favorites") renderFavorites();
        }
      } catch (err) {
        toast(err.message);
      }
      return;
    }

    const dlBest = e.target.closest("[data-dl-best]");
    if (dlBest) {
      try {
        const payload = JSON.parse(decodeURIComponent(dlBest.getAttribute("data-dl-best")));
        dlBest.disabled = true;
        toast("İndirme hazırlanıyor…");
        const res = await call("enqueue_best", payload);
        if (!res.ok) throw new Error(res.error || "İndirilemedi");
        toast("Kuyruğa eklendi");
        await refreshQueue();
        switchView("queue");
      } catch (err) {
        toast(err.message);
      } finally {
        dlBest.disabled = false;
      }
      return;
    }

    const openUrl = e.target.closest("[data-open-url]");
    if (openUrl) {
      doResolve(openUrl.dataset.openUrl);
      return;
    }

    const cancel = e.target.closest("[data-cancel]");
    if (cancel) {
      await call("cancel_job", cancel.dataset.cancel);
      await refreshQueue();
      return;
    }
    const open = e.target.closest("[data-open]");
    if (open) {
      await call("open_path", open.dataset.open);
    }
  });

  $("#btn-folder").addEventListener("click", async () => {
    try {
      const res = await call("pick_download_dir");
      if (res.ok) {
        applySettings(res.settings);
        toast("Klasör güncellendi");
      }
    } catch (e) {
      toast(e.message);
    }
  });

  $("#btn-settings-folder")?.addEventListener("click", async () => {
    try {
      const res = await call("pick_download_dir");
      if (res.ok) {
        applySettings(res.settings);
        toast("Klasör güncellendi");
      }
    } catch (e) {
      toast(e.message);
    }
  });

  document.body.addEventListener("click", async (e) => {
    const themeBtn = e.target.closest("[data-theme-id]");
    if (themeBtn) {
      try {
        await saveSettings({ theme: themeBtn.dataset.themeId });
      } catch (err) {
        toast(err.message);
      }
      return;
    }
    const appearanceBtn = e.target.closest("#appearance-seg [data-appearance]");
    if (appearanceBtn) {
      try {
        await saveSettings({ appearance: appearanceBtn.dataset.appearance });
      } catch (err) {
        toast(err.message);
      }
      return;
    }
  }, true);

  $("#opt-animations")?.addEventListener("change", async (e) => {
    try { await saveSettings({ animations: e.target.checked }); }
    catch (err) { toast(err.message); }
  });
  $("#opt-auto-best")?.addEventListener("change", async (e) => {
    try { await saveSettings({ auto_best_quality: e.target.checked }); }
    catch (err) { toast(err.message); }
  });
  $("#opt-concurrent")?.addEventListener("change", async (e) => {
    try { await saveSettings({ concurrent_downloads: Number(e.target.value) }); }
    catch (err) { toast(err.message); }
  });

  $("#btn-copy-discord")?.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(DISCORD);
      const el = $("#btn-copy-discord");
      el?.classList.add("copied");
      toast("Discord: ashtwix kopyalandı");
      setTimeout(() => el?.classList.remove("copied"), 1400);
    } catch (_) {
      toast("ashtwix");
    }
  });

  $("#btn-clear-finished").addEventListener("click", async () => {
    const res = await call("clear_finished");
    if (res.ok) {
      state.jobs = res.jobs || [];
      syncQueue(state.jobs);
    }
  });

  $("#btn-clear-history").addEventListener("click", async () => {
    await call("clear_history");
    renderHistory();
    toast("Geçmiş temizlendi");
  });

  $("#btn-clear-favorites").addEventListener("click", async () => {
    await call("clear_favorites");
    renderFavorites();
    toast("Favoriler temizlendi");
  });

  document.querySelectorAll(".nav-item[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
  });

  $("#discord-link").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(DISCORD);
      const el = $("#discord-link");
      el.classList.add("copied");
      toast("Discord: ashtwix kopyalandı");
      setTimeout(() => el.classList.remove("copied"), 1400);
    } catch (_) {
      toast("ashtwix");
    }
  });

  window.addEventListener("pywebviewready", boot);
  if (window.pywebview?.api) boot();
})();
