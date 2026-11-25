/* =========================================================
   Movimiento editorial: revelado al entrar en pantalla,
   parallax suave en las fotografías, progreso de lectura y
   barra superior en estado compacto. Sin dependencias.
   ========================================================= */
(function () {
  'use strict';

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var doc = document.documentElement;

  /* ---------- progreso de lectura ---------- */
  var bar = document.querySelector('.progress');
  function paintProgress() {
    if (!bar) return;
    var h = doc;
    var max = h.scrollHeight - h.clientHeight;
    var y = window.pageYOffset || h.scrollTop || 0;
    bar.style.width = (max > 0 ? Math.min(1, y / max) * 100 : 0) + '%';
  }

  /* ---------- barra superior compacta ---------- */
  var topbar = document.querySelector('.topbar');
  function paintTopbar() {
    if (!topbar) return;
    topbar.classList.toggle('is-scrolled', (window.pageYOffset || 0) > 24);
  }

  /* ---------- parallax ---------- */
  var parallaxEls = Array.prototype.slice.call(document.querySelectorAll('img[data-parallax]'));
  function paintParallax() {
    if (!parallaxEls.length || reduce.matches) return;
    var vh = window.innerHeight || doc.clientHeight;
    parallaxEls.forEach(function (img) {
      var frame = img.closest('figure') || img;
      var r = frame.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) return;
      var amount = parseFloat(img.getAttribute('data-parallax')) || 0.1;
      var offset = (r.top + r.height / 2 - vh / 2) * -amount;
      var limit = Math.max(24, r.height * 0.1);
      offset = Math.max(-limit, Math.min(limit, offset));
      img.style.setProperty('--py', offset.toFixed(1) + 'px');
    });
  }

  /* ---------- radar del IMI (si la página lo incluye) ---------- */
  function drawRadar() {
    var svg = document.getElementById('radar');
    if (!svg || svg.childElementCount) return;
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
      for (var k = 0; k < n; k++) {
        var p = pt(k, vals[k]);
        pts.push(p[0].toFixed(1) + ',' + p[1].toFixed(1));
      }
      return pts.join(' ');
    }

    for (var ring = 1; ring <= 5; ring++) {
      html += '<polygon class="ring" points="' + poly([ring, ring, ring, ring, ring, ring]) + '"/>';
    }
    for (var j = 0; j < n; j++) {
      var pe = pt(j, 5);
      html += '<line class="axis" x1="' + cx + '" y1="' + cy + '" x2="' + pe[0].toFixed(1) +
              '" y2="' + pe[1].toFixed(1) + '"/>';
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
      html += '<text class="lbl" x="' + pl[0].toFixed(1) + '" y="' + (pl[1] + 4).toFixed(1) +
              '" font-size="10" text-anchor="' + anchor + '">' + tspans + '</text>';
    }
    html += '<polygon class="target" points="' + poly(target) + '"/>';
    html += '<polygon class="actual" points="' + poly(actual) + '"/>';
    for (var m = 0; m < n; m++) {
      var pa = pt(m, actual[m]);
      html += '<circle class="dot" cx="' + pa[0].toFixed(1) + '" cy="' + pa[1].toFixed(1) + '" r="2.8"/>';
    }
    svg.innerHTML = html;
  }

  /* ---------- migaja viva: el capítulo en curso ---------- */
  var crumb = document.querySelector('.tb-crumb b');
  var chapterEls = document.querySelectorAll('#deck > .chapter');
  if (crumb && chapterEls.length && 'IntersectionObserver' in window) {
    var ioCrumb = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var name = entry.target.getAttribute('data-nav');
        if (name && crumb.textContent !== name) crumb.textContent = name;
      });
    }, { rootMargin: '-45% 0px -45% 0px' });
    Array.prototype.forEach.call(chapterEls, function (ch) { ioCrumb.observe(ch); });
  }

  /* ---------- revelado ---------- */
  var candidates = '.chapter-head,.cover-block,.chapter-body>section,.eje-sec,' +
    '.cover-photo,.band-photo,.eje-photo,.tesis,.kpi-row,.parts,.topics,.eje-facts,' +
    '.scene-inner h1,.scene-inner .sub';

  function setupReveal() {
    var els = Array.prototype.slice.call(document.querySelectorAll(candidates));
    if (!els.length) return;
    if (reduce.matches || !('IntersectionObserver' in window)) return;

    var vh = window.innerHeight || doc.clientHeight;
    var pending = [];

    els.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < vh * 0.92 && r.bottom > 0) {
        el.classList.add('is-in');
      } else {
        el.classList.add('m-out');
        pending.push(el);
      }
    });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    pending.forEach(function (el) { io.observe(el); });
  }

  /* ---------- ciclo de scroll ---------- */
  var ticking = false;
  function frame() {
    paintProgress();
    paintTopbar();
    paintParallax();
    ticking = false;
  }
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(frame);
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', function () {
    onScroll();
    if (!reduce.matches) {
      document.querySelectorAll('img[data-parallax]').forEach(function (img) {
        img.style.removeProperty('--py');
      });
    }
  });
  if (reduce.addEventListener) reduce.addEventListener('change', onScroll);

  setupReveal();
  drawRadar();
  frame();
})();
