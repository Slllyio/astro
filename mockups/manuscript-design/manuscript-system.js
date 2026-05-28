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
      btnMute.textContent = muted ? '🔇 muted' : '🔊 sound';
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
    currentPage = 0;
    render();
  };
  window.goToManuscriptPage = function (idx) {
    if (idx < 0 || idx >= totalPages) return;
    currentPage = idx;
    render();
  };

  if (btnNext) btnNext.addEventListener('click', next);
  if (btnPrev) btnPrev.addEventListener('click', prev);
  const zonePrev = document.getElementById('zone-prev');
  const zoneNext = document.getElementById('zone-next');
  if (zoneNext) zoneNext.addEventListener('click', next);
  if (zonePrev) zonePrev.addEventListener('click', prev);

  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight' || e.key === ' ') {
      e.preventDefault(); next();
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
      e.preventDefault(); prev();
    } else if (e.key === 'Home') { currentPage = 0; render(); }
    else if (e.key === 'End')    { currentPage = totalPages - 1; render(); }
  });

  render();

  // ----- Dust motes -----
  const dustLayer = document.getElementById('dust-layer');
  if (dustLayer) {
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
    for (let i = 0; i < MAX_MOTES; i++) setTimeout(spawnMote, Math.random() * 8000);
    setInterval(() => {
      if (dustLayer.children.length < MAX_MOTES) spawnMote();
    }, 700);
  }
})();
