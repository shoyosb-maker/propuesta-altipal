/* =========================================================
   CEDI 360 · Recorrido del despiece
   Cinco láminas del camión despiezado con panel de contenido,
   puntos activos y navegación por teclado, riel y gestos.
   ========================================================= */
(function () {
  'use strict';

  var FASES = [
    {
      n: '00',
      titulo: 'En tránsito',
      lead: 'Lo que ve el cliente: la unidad cerrada y rotulada que llega a tiempo. Aquí todavía no se ve nada de lo que la sostiene.',
      bullets: [
        'Contenedor ISO 40\' HC con la promesa de ALTIPAL en el lateral',
        'Chasis portacontenedores de tres ejes y 12,35 m de bastidor',
        'La cadena completa, todavía invisible'
      ],
      metrica: '12.192 m de largo · 2.896 m de alto · 20 estibas',
      spots: [
        { x: 47, y: 40, t: 'Lema de ALTIPAL' },
        { x: 71, y: 54, t: 'Cabina tractora' }
      ]
    },
    {
      n: '01',
      titulo: 'Estabilización',
      lead: 'El techo se separa y la carga aparece: lo primero no es comprar, es asegurar. Se cierra lo que puede fallar esta semana.',
      bullets: [
        'Enlace redundante y UPS para la telemetría del contenedor',
        'Cierre de puntos ciegos en muelles y compuertas',
        'Respaldo probado y documentado por sede'
      ],
      metrica: 'Riesgo inmediato cerrado · semanas 4 a 16',
      spots: [
        { x: 52, y: 26, t: 'Techo separado' },
        { x: 47, y: 45, t: 'Carga asegurada' }
      ]
    },
    {
      n: '02',
      titulo: 'Modernización',
      lead: 'Paredes y puertas se abren: aparece el interior. Aquí se cambia lo que está fuera de soporte y se normaliza lo que ya existe.',
      bullets: [
        'CCTV IP con retención definida por ALTIPAL',
        'Cableado certificado, fibra y cuartos técnicos normalizados',
        'Iluminación LED y tableros bajo norma RETIE'
      ],
      metrica: 'Cuatro ejes A–D · inventario georreferenciado',
      spots: [
        { x: 50, y: 47, t: 'Estibas y sensores' },
        { x: 63, y: 41, t: 'Puertas abiertas 135°' }
      ]
    },
    {
      n: '03',
      titulo: 'Inteligencia',
      lead: 'Sobre el techo aparece la capa de datos: lo que antes era mantenimiento ahora es información para decidir.',
      bullets: [
        'Analítica de video y detección de eventos',
        'Telemetría térmica BPM / INVIMA en vivo',
        'WMS, TMS y tableros ejecutivos integrados'
      ],
      metrica: '42 nodos de sensores · 128 precintos activos',
      spots: [
        { x: 32, y: 20, t: 'Analítica de video' },
        { x: 68, y: 22, t: 'Telemetría BPM' }
      ]
    },
    {
      n: '04',
      titulo: 'Acompañamiento',
      lead: 'La cabina se separa y la unidad queda lista para operar. El programa deja de ser un proyecto y pasa a ser un servicio con SLA.',
      bullets: [
        'Mesa de servicio única y comité mensual',
        'SLA por sede con reporte de cumplimiento',
        'Hoja de vida de activos viva y auditable'
      ],
      metrica: '18 meses marco · renovación anual',
      spots: [
        { x: 74, y: 52, t: 'Cabina separada' },
        { x: 38, y: 53, t: 'Chasis y red' }
      ]
    }
  ];

  var stage = document.getElementById('recStage');
  var spotsBox = document.getElementById('recSpots');
  var rail = document.getElementById('recRail');
  var hud = document.getElementById('recHud');
  var progress = document.getElementById('recProgress');
  var prevBtn = document.getElementById('recPrev');
  var nextBtn = document.getElementById('recNext');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var actual = 0;

  /* las láminas ya vienen en el HTML para que el navegador las precargue */
  var plates = Array.prototype.slice.call(stage.querySelectorAll('.rec-plate'));

  /* ---------- construir el riel y los puntos ---------- */
  FASES.forEach(function (fase, i) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'rec-step' + (i === 0 ? ' on' : '');
    btn.innerHTML = '<b>' + fase.n + '</b><span>' + fase.titulo + '</span>';
    btn.setAttribute('aria-label', 'Fase ' + fase.n + ': ' + fase.titulo);
    btn.addEventListener('click', function () { ir(i); });
    rail.insertBefore(btn, rail.querySelector('.rec-arrows'));
  });

  var steps = Array.prototype.slice.call(rail.querySelectorAll('.rec-step'));

  function pintarSpots(i) {
    spotsBox.innerHTML = '';
    FASES[i].spots.forEach(function (spot) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'rec-spot';
      b.style.left = spot.x + '%';
      b.style.top = spot.y + '%';
      b.innerHTML = '<i></i><span>' + spot.t + '</span>';
      b.setAttribute('aria-label', spot.t);
      spotsBox.appendChild(b);
    });
    requestAnimationFrame(function () {
      Array.prototype.forEach.call(spotsBox.children, function (el) { el.classList.add('on'); });
    });
  }

  function pintarHud(i) {
    var f = FASES[i];
    hud.innerHTML =
      '<span class="rn">' + f.n + ' · ' + f.titulo + '</span>' +
      '<h1>' + f.titulo + '</h1>' +
      '<p>' + f.lead + '</p>' +
      '<ul>' + f.bullets.map(function (b) { return '<li>' + b + '</li>'; }).join('') + '</ul>' +
      '<span class="rm">' + f.metrica + '</span>';
  }

  function ir(i, sinScroll) {
    if (i < 0 || i >= FASES.length) return;
    actual = i;
    plates.forEach(function (p, k) { p.classList.toggle('on', k === i); });
    steps.forEach(function (s, k) {
      s.classList.toggle('on', k === i);
      if (k === i) s.setAttribute('aria-current', 'true');
      else s.removeAttribute('aria-current');
    });
    pintarHud(i);
    pintarSpots(i);
    progress.style.width = ((i + 1) / FASES.length * 100) + '%';
    prevBtn.disabled = i === 0;
    nextBtn.disabled = i === FASES.length - 1;
    if (history.replaceState) history.replaceState(null, '', '#fase-' + i);
    if (!sinScroll) {
      try { sessionStorage.setItem('cedi:recorrido', String(i)); } catch (err) {}
    }
  }

  /* ---------- controles ---------- */
  prevBtn.addEventListener('click', function () { ir(actual - 1); });
  nextBtn.addEventListener('click', function () { ir(actual + 1); });

  document.addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var tag = (document.activeElement && document.activeElement.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
      ir(actual + 1); e.preventDefault();
    }
    if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      ir(actual - 1); e.preventDefault();
    }
    if (e.key === 'Home') { ir(0); e.preventDefault(); }
    if (e.key === 'End') { ir(FASES.length - 1); e.preventDefault(); }
  });

  /* rueda del mouse con freno para no saltar varias fases de golpe */
  var wheelLock = 0;
  window.addEventListener('wheel', function (e) {
    if (Math.abs(e.deltaY) < 24) return;
    var ahora = Date.now();
    if (ahora - wheelLock < 700) return;
    wheelLock = ahora;
    ir(actual + (e.deltaY > 0 ? 1 : -1));
  }, { passive: true });

  /* gestos horizontales */
  var sx = 0, sy = 0, tracking = false;
  document.addEventListener('touchstart', function (e) {
    if (e.touches.length !== 1) { tracking = false; return; }
    sx = e.touches[0].clientX;
    sy = e.touches[0].clientY;
    tracking = true;
  }, { passive: true });
  document.addEventListener('touchend', function (e) {
    if (!tracking) return;
    tracking = false;
    var t = e.changedTouches[0];
    var dx = t.clientX - sx, dy = t.clientY - sy;
    if (Math.abs(dx) > 70 && Math.abs(dy) < 60) ir(actual + (dx < 0 ? 1 : -1));
  }, { passive: true });

  /* ---------- pantalla completa ---------- */
  var full = document.getElementById('recFull');
  if (full) {
    full.addEventListener('click', function () {
      var doc = document;
      var el = doc.documentElement;
      if (doc.fullscreenElement) {
        if (doc.exitFullscreen) doc.exitFullscreen();
      } else if (el.requestFullscreen) {
        el.requestFullscreen();
      }
    });
    document.addEventListener('fullscreenchange', function () {
      full.textContent = document.fullscreenElement ? 'Salir' : 'Pantalla completa';
    });
  }

  /* ---------- arranque ---------- */
  function inicio() {
    var hash = (location.hash || '').replace('#fase-', '');
    var idx = parseInt(hash, 10);
    if (isNaN(idx)) {
      try {
        var guardado = parseInt(sessionStorage.getItem('cedi:recorrido'), 10);
        idx = isNaN(guardado) ? 0 : guardado;
      } catch (err) { idx = 0; }
    }
    document.querySelectorAll('.rec-plate img').forEach(function (img) {
      img.setAttribute('loading', 'eager');
    });
    ir(idx || 0, true);
  }

  if (document.readyState === 'complete') inicio();
  else window.addEventListener('load', inicio);
})();
