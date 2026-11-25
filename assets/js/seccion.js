/* =========================================================
   Recorrido lineal: cada tema es su propia página y el avance
   se hace con la barra inferior, los puntos de la izquierda,
   las flechas laterales o ← → del teclado.
   ========================================================= */
(function () {
  'use strict';

  /* ---------- progreso de lectura ---------- */
  var bar = document.querySelector('.progress');
  function onScroll() {
    if (!bar) return;
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var y = h.scrollTop || document.body.scrollTop || 0;
    bar.style.width = (max > 0 ? Math.min(1, y / max) * 100 : 0) + '%';
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);

  /* ---------- acordeones: uno abierto a la vez ---------- */
  var accs = Array.prototype.slice.call(document.querySelectorAll('.acc'));
  function setAcc(acc, open) {
    var body = acc.querySelector('.acc-body');
    acc.classList.toggle('open', open);
    acc.querySelector('.acc-head').setAttribute('aria-expanded', open ? 'true' : 'false');
    body.style.maxHeight = open ? body.scrollHeight + 'px' : '0px';
  }
  accs.forEach(function (acc) {
    setAcc(acc, acc.classList.contains('open'));
    acc.querySelector('.acc-head').addEventListener('click', function () {
      var open = !acc.classList.contains('open');
      if (open) accs.forEach(function (other) { if (other !== acc) setAcc(other, false); });
      setAcc(acc, open);
    });
  });
  window.addEventListener('resize', function () {
    accs.forEach(function (acc) {
      if (acc.classList.contains('open')) {
        var body = acc.querySelector('.acc-body');
        body.style.maxHeight = body.scrollHeight + 'px';
      }
    });
  });

  /* abrir y enfocar el eje enlazado desde la portada (#eje-a ... #eje-d) */
  function openFromHash() {
    var h = (location.hash || '').replace('#', '');
    if (!h) return;
    var el = document.getElementById(h);
    if (!el || !el.classList.contains('acc')) return;
    accs.forEach(function (other) { setAcc(other, other === el); });
    var y = el.getBoundingClientRect().top + window.pageYOffset - 92;
    window.scrollTo(0, Math.max(0, y));
  }
  window.addEventListener('load', openFromHash);
  window.addEventListener('hashchange', openFromHash);
  openFromHash();

  /* ---------- fases ---------- */
  var phaseButtons = Array.prototype.slice.call(document.querySelectorAll('.ph'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('.phase-panel'));
  function showPhase(p) {
    phaseButtons.forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-phase') === p); });
    panels.forEach(function (panel) { panel.classList.toggle('active', panel.getAttribute('data-panel') === p); });
  }
  phaseButtons.forEach(function (btn) {
    btn.addEventListener('click', function () { showPhase(btn.getAttribute('data-phase')); });
  });

  /* ---------- radar IMI ---------- */
  function drawRadar() {
    var svg = document.getElementById('radar');
    if (!svg) return;
    var cx = 190, cy = 186, R = 116;
    var dims = ['Seguridad electrónica', 'Redes y conectividad', 'Energía y respaldo',
                'Instalaciones', 'Gestión y mantenimiento', 'Analítica e integración'];
    var actual = [2.4, 2.2, 2.0, 2.9, 1.9, 1.6];
    var target = [4.4, 4.5, 4.5, 4.2, 4.5, 4.0];
    var n = dims.length;
    var html = '';

    function pt(i, v) {
      var ang = (-Math.PI / 2) + (i * 2 * Math.PI / n);
      var r = R * v / 5;
      return [cx + Math.cos(ang) * r, cy + Math.sin(ang) * r];
    }
    function poly(vals) {
      var pts = [];
      for (var i = 0; i < n; i++) {
        var p = pt(i, vals[i]);
        pts.push(p[0].toFixed(1) + ',' + p[1].toFixed(1));
      }
      return pts.join(' ');
    }

    for (var ring = 1; ring <= 5; ring++) {
      var pts = [];
      for (var i2 = 0; i2 < n; i2++) {
        var p2 = pt(i2, ring);
        pts.push(p2[0].toFixed(1) + ',' + p2[1].toFixed(1));
      }
      html += '<polygon points="' + pts.join(' ') + '" fill="none" stroke="rgba(127,176,255,' +
              (ring === 5 ? '.34' : '.16') + ')" stroke-width="1"/>';
    }
    for (var j = 0; j < n; j++) {
      var pe = pt(j, 5);
      html += '<line x1="' + cx + '" y1="' + cy + '" x2="' + pe[0].toFixed(1) + '" y2="' +
              pe[1].toFixed(1) + '" stroke="rgba(127,176,255,.16)" stroke-width="1"/>';
      var pl = pt(j, 6.15);
      var anchor = Math.abs(pl[0] - cx) < 12 ? 'middle' : (pl[0] > cx ? 'start' : 'end');
      var words = dims[j].split(' ');
      var lines = [];
      if (dims[j].length > 14) {
        var mid = Math.ceil(words.length / 2);
        lines.push(words.slice(0, mid).join(' '));
        lines.push(words.slice(mid).join(' '));
      } else {
        lines.push(dims[j]);
      }
      var tspans = lines.map(function (line, k) {
        return '<tspan x="' + pl[0].toFixed(1) + '" dy="' + (k === 0 ? 0 : 12) + '">' + line + '</tspan>';
      }).join('');
      html += '<text x="' + pl[0].toFixed(1) + '" y="' + (pl[1] + 4).toFixed(1) +
              '" font-size="10" fill="#9FB6CC" text-anchor="' + anchor +
              '" font-family="JetBrains Mono, monospace">' + tspans + '</text>';
    }
    html += '<polygon points="' + poly(target) + '" fill="rgba(251,199,16,.12)" stroke="#FBC710" stroke-width="2" stroke-dasharray="5 4"/>';
    html += '<polygon points="' + poly(actual) + '" fill="rgba(127,176,255,.2)" stroke="#7FB0FF" stroke-width="2"/>';
    for (var k = 0; k < n; k++) {
      var pa = pt(k, actual[k]);
      html += '<circle cx="' + pa[0].toFixed(1) + '" cy="' + pa[1].toFixed(1) + '" r="2.8" fill="#7FB0FF"/>';
    }
    svg.innerHTML = html;
  }
  drawRadar();

  /* ---------- revelado sutil ---------- */
  var revealEls = Array.prototype.slice.call(document.querySelectorAll('.reveal'));
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: .07 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- pasar sección por sección ---------- */
  var next = document.querySelector('.deck-next[href], .pg.next[href]');
  var prev = document.querySelector('.deck-prev[href], .pg.prev[href]');

  function go(link) {
    if (link && link.getAttribute('href')) window.location.href = link.getAttribute('href');
  }

  document.addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var tag = (document.activeElement && document.activeElement.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
    if (e.key === 'ArrowRight') { go(next); e.preventDefault(); }
    if (e.key === 'ArrowLeft') { go(prev); e.preventDefault(); }
  });

  /* gestos horizontales en móvil, sólo si el gesto es claramente horizontal */
  var sx = 0, sy = 0, tracking = false;
  document.addEventListener('touchstart', function (e) {
    if (e.touches.length !== 1) { tracking = false; return; }
    sx = e.touches[0].clientX; sy = e.touches[0].clientY; tracking = true;
  }, { passive: true });
  document.addEventListener('touchend', function (e) {
    if (!tracking) return;
    tracking = false;
    var t = e.changedTouches[0];
    var dx = t.clientX - sx, dy = t.clientY - sy;
    if (Math.abs(dx) > 90 && Math.abs(dy) < 55) {
      if (dx < 0) go(next); else go(prev);
    }
  }, { passive: true });

  /* ---------- volver al capítulo anterior ---------- */
  var backs = Array.prototype.slice.call(document.querySelectorAll('[data-back]'));
  backs.forEach(function (a) {
    a.addEventListener('click', function (ev) {
      var ref = document.referrer || '';
      if (ref && history.length > 1) {
        ev.preventDefault();
        history.back();
      }
    });
  });

  /* imprimir la sección actual con todo desplegado */
  var openBeforePrint = [];
  var printBtn = document.getElementById('printBtn');
  if (printBtn) printBtn.addEventListener('click', function () { window.print(); });
  window.addEventListener('beforeprint', function () {
    openBeforePrint = accs.map(function (acc) { return acc.classList.contains('open'); });
    accs.forEach(function (acc) {
      acc.classList.add('open');
      acc.querySelector('.acc-body').style.maxHeight = 'none';
      acc.querySelector('.acc-head').setAttribute('aria-expanded', 'true');
    });
    revealEls.forEach(function (el) { el.classList.add('in'); });
  });
  window.addEventListener('afterprint', function () {
    accs.forEach(function (acc, i) {
      var body = acc.querySelector('.acc-body');
      if (openBeforePrint[i]) {
        body.style.maxHeight = body.scrollHeight + 'px';
      } else {
        acc.classList.remove('open');
        acc.querySelector('.acc-head').setAttribute('aria-expanded', 'false');
        body.style.maxHeight = '0px';
      }
    });
  });

  /* precarga de la siguiente sección para que el avance sea inmediato */
  if (next) {
    var pre = document.createElement('link');
    pre.rel = 'prefetch';
    pre.href = next.getAttribute('href');
    document.head.appendChild(pre);
  }

  onScroll();
})();
