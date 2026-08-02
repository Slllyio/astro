/* ============================================================
   POTHI MANUSCRIPT SHARED MECHANICS
   ------------------------------------------------------------
   - Upward flip state machine
   - Web Audio synthesized page-rustle
   - Dust mote spawner
   - Keyboard + click-edge + nav-bar navigation

   Each page must:
   1. Include the standard .manuscript-stage / .manuscript /
      .leaf[data-page] markup
   2. Include the .nav-bar with #btn-prev / #btn-next /
      #folio-status / #btn-mute / .edge-zone.top + .bottom
   3. Define `window.MANUSCRIPT_LABELS` array BEFORE loading this
      script — one label per leaf in order
   4. Optionally define `window.MANUSCRIPT_ON_FLIP(pageIndex)`
      for per-page hooks
============================================================ */

(function () {
  const leaves = document.querySelectorAll('.leaf');
  const totalPages = leaves.length;
  let currentPage = 0;
  let isFlipping = false;

  // Below 700px the report is ONE continuous scrolling page — no page-flip
  // book, no bottom toolbar (2026-07-28, user-directed simplification: "let
  // it simplify... give report continuously... remove [the nav bar] for
  // mobile version"). Pagination (next/prev/swipe/cover-tap/arrow-keys) only
  // makes sense when leaves are shown one at a time, so all of it is skipped
  // here — every leaf is simply visible via CSS, and the page scrolls like
  // any normal document. Checked once at load, matching how the CSS
  // breakpoint itself is evaluated (not re-checked on rotate/resize).
  const paginated = !window.matchMedia('(max-width: 700px)').matches;

  const status = document.getElementById('folio-status');
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const btnMute = document.getElementById('btn-mute');

  const labels = window.MANUSCRIPT_LABELS || Array.from({ length: totalPages }, (_, i) =>
    i === 0 ? 'COVER' : i === totalPages - 1 ? 'END' : 'FOLIO ' + i
  );

  function render() {
    leaves.forEach((leaf, i) => {
      if (i < currentPage) leaf.classList.add('flipped');
      else leaf.classList.remove('flipped');
    });
    if (status) status.textContent = labels[currentPage] || '';
    if (btnPrev) btnPrev.disabled = currentPage === 0;
    if (btnNext) btnNext.disabled = currentPage === totalPages - 1;
    if (typeof window.MANUSCRIPT_ON_FLIP === 'function') {
      window.MANUSCRIPT_ON_FLIP(currentPage);
    }
  }

  // ----- Web Audio rustle -----
  let audioCtx = null, muted = false;
  function ensureAudioCtx() {
    if (!audioCtx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) audioCtx = new AC();
    }
    return audioCtx;
  }
  function playRustle() {
    if (muted) return;
    const ctx = ensureAudioCtx();
    if (!ctx) return;
    const duration = 0.20;
    const bufferSize = Math.floor(ctx.sampleRate * duration);
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      const env = Math.pow(1 - i / bufferSize, 2.0);
      data[i] = (Math.random() * 2 - 1) * env;
    }
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    const filter = ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.value = 3000;
    filter.Q.value = 0.6;
    const gain = ctx.createGain();
    gain.gain.value = 0.10;
    src.connect(filter).connect(gain).connect(ctx.destination);
    src.start();
    src.stop(ctx.currentTime + duration + 0.02);
  }
  if (btnMute) {
    btnMute.addEventListener('click', () => {
      muted = !muted;
      btnMute.classList.toggle('muted', muted);
      // Keep the .nav-lbl span (hidden on phones by the portrait breakpoint);
      // safe DOM construction — no innerHTML (project rule)
      btnMute.textContent = muted ? '🔇 ' : '🔊 ';
      const lbl = document.createElement('span');
      lbl.className = 'nav-lbl';
      lbl.textContent = muted ? 'muted' : 'sound';
      btnMute.appendChild(lbl);
    });
  }

  // ----- Navigation -----
  function next() {
    if (isFlipping || currentPage >= totalPages - 1) return;
    isFlipping = true;
    currentPage += 1;
    playRustle();
    render();
    setTimeout(() => { isFlipping = false; }, 550);
  }
  function prev() {
    if (isFlipping || currentPage <= 0) return;
    isFlipping = true;
    currentPage -= 1;
    playRustle();
    render();
    setTimeout(() => { isFlipping = false; }, 550);
  }
  window.reopenManuscript = function () {
    if (!paginated) {
      // Continuous mode: "cast another chart" means scroll back up to the
      // birth-form leaf (leaves[1]) rather than resetting an invisible page
      // counter — there is no cover-to-hide/page-to-show state to reset.
      const form = leaves[1];
      if (form) form.scrollIntoView({ behavior: 'smooth', block: 'start' });
      else window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    currentPage = 0;
    render();
  };
  window.goToManuscriptPage = function (idx) {
    if (idx < 0 || idx >= totalPages) return;
    if (!paginated) {
      // Continuous mode: every leaf is already visible — "going to" a page
      // means scrolling its section into view (report.html calls this both
      // when casting starts and when it completes, so the reader's view
      // still jumps to the fresh reading exactly as it did in the book).
      const target = leaves[idx];
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    currentPage = idx;
    render();
  };

  if (btnNext) btnNext.addEventListener('click', next);
  if (btnPrev) btnPrev.addEventListener('click', prev);
  const zonePrev = document.getElementById('zone-prev');
  const zoneNext = document.getElementById('zone-next');
  if (zoneNext) zoneNext.addEventListener('click', next);
  if (zonePrev) zonePrev.addEventListener('click', prev);

  if (paginated) {
    // The FRONT cover's own on-screen hint promises "tap ... to enter" — the
    // generic .edge-zone strips can't cover the cover leaf without also
    // stealing scroll taps on content leaves. Make the whole front cover
    // tappable directly. `.closing` covers (a book's back/reopen cover, used
    // on some pages) are excluded — those have their own explicit reopen
    // button and must not auto-advance on tap.
    const frontCover = document.querySelector('.cover:not(.closing)');
    if (frontCover) {
      frontCover.addEventListener('click', () => { if (currentPage === 0) next(); });
    }

    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault(); next();
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault(); prev();
      } else if (e.key === 'Home') { currentPage = 0; render(); }
      else if (e.key === 'End')    { currentPage = totalPages - 1; render(); }
    });
  }

  // ----- Touch swipe (paginated/book mode only — continuous mode has
  // nothing to swipe TO, and firing a page-turn rustle sound with no
  // visible page turn would just feel like a glitch). -----
  const stage = document.querySelector('.manuscript-stage');
  if (stage && paginated) {
    let touchX = 0, touchY = 0, touchOk = false;

    function inHorizontalScroller(el) {
      for (let n = el; n && n !== stage; n = n.parentElement) {
        if (n.scrollWidth > n.clientWidth + 8) {
          const ox = getComputedStyle(n).overflowX;
          if (ox === 'auto' || ox === 'scroll') return true;
        }
      }
      return false;
    }

    stage.addEventListener('touchstart', (e) => {
      if (e.touches.length !== 1) { touchOk = false; return; }
      const t = e.touches[0];
      const tag = e.target.tagName;
      touchOk = tag !== 'INPUT' && tag !== 'TEXTAREA' && tag !== 'SELECT' &&
                tag !== 'BUTTON' && !inHorizontalScroller(e.target);
      touchX = t.clientX; touchY = t.clientY;
    }, { passive: true });

    stage.addEventListener('touchend', (e) => {
      if (!touchOk) return;
      const t = e.changedTouches[0];
      const dx = t.clientX - touchX;
      const dy = t.clientY - touchY;
      // Deliberate horizontal swipe: >=60px travel, mostly horizontal
      if (Math.abs(dx) < 60 || Math.abs(dy) > Math.abs(dx) * 0.6) return;
      if (dx < 0) next(); else prev();
    }, { passive: true });
  }

  render();

  // ----- Dust motes (paginated/book mode only — the continuous mobile
  // page hides .dust-layer via CSS too; skipping the spawner outright
  // avoids the wasted timers/DOM churn entirely, not just the visuals). -----
  const dustLayer = document.getElementById('dust-layer');
  if (dustLayer && paginated) {
    const MAX_MOTES = 32;
    function spawnMote() {
      const m = document.createElement('div');
      m.className = 'dust-mote';
      const dur = 14 + Math.random() * 24;
      m.style.left = (Math.random() * 100) + 'vw';
      m.style.animationDuration = dur + 's';
      m.style.animationDelay = (Math.random() * 2) + 's';
      m.style.opacity = 0.4 + Math.random() * 0.4;
      const sz = (1.5 + Math.random() * 3) + 'px';
      m.style.width = sz; m.style.height = sz;
      dustLayer.appendChild(m);
      setTimeout(() => m.remove(), (dur + 3) * 1000);
    }
    // Both the startup stagger and the steady-state interval must share ONE
    // gate (children.length < MAX_MOTES) — otherwise, while the staggered
    // batch is still arriving (up to 8s), the interval independently adds its
    // own motes on top and briefly overshoots MAX_MOTES.
    function spawnIfRoom() { if (dustLayer.children.length < MAX_MOTES) spawnMote(); }
    for (let i = 0; i < MAX_MOTES; i++) setTimeout(spawnIfRoom, Math.random() * 8000);
    setInterval(spawnIfRoom, 700);
  }
})();
