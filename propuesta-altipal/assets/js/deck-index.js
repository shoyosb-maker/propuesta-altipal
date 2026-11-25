/* =========================================================
   Deck de capítulos con tope real.
   - El scroll recorre sólo el capítulo actual: al llegar a su
     borde se detiene, no pasa al siguiente.
   - El cambio de capítulo es exclusivo de las flechas y los
     puntos del deck.
   ========================================================= */
(function () {
  'use strict';

  var chapters = Array.prototype.slice.call(document.querySelectorAll('#deck > .chapter'));
  if (chapters.length < 2) return;

  var dotsBox = document.getElementById('deckDots');
  var prevBtn = document.getElementById('deckPrev');
  var nextBtn = document.getElementById('deckNext');
  var counter = document.getElementById('deckCount');
  var topbar = document.querySelector('.topbar');
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var STORE = 'cedi:capitulo';

  var cur = 0;
  var moving = false;
  var moveTimer = 0;

  var existing = dotsBox ? Array.prototype.slice.call(dotsBox.querySelectorAll('a')) : [];
  var dots = chapters.map(function (ch, i) {
    var a = existing[i];
    if (!a) {
      a = document.createElement('a');
      a.href = '#' + ch.id;
      a.setAttribute('data-nav', ch.getAttribute('data-nav') || '');
      var li = document.createElement('li');
      li.appendChild(a);
      if (dotsBox) dotsBox.appendChild(li);
    }
    a.setAttribute('aria-label', 'Capítulo ' + (ch.getAttribute('data-num') || i + 1) + ': ' + (ch.getAttribute('data-nav') || ''));
    a.addEventListener('click', function (ev) { ev.preventDefault(); goTo(i); });
    return a;
  });

  function topOf(el) { return el.getBoundingClientRect().top + window.pageYOffset; }

  /* límites del capítulo: [inicio, último scroll posible] */
  function bounds(i) {
    var el = chapters[i];
    var top = topOf(el);
    var bottom = top + el.offsetHeight - window.innerHeight;
    if (bottom < top) bottom = top;
    return [top, bottom];
  }

  function nearestIndex() {
    var y = window.pageYOffset + (topbar ? topbar.offsetHeight : 0) + 12;
    var best = 0;
    for (var i = 0; i < chapters.length; i++) {
      if (topOf(chapters[i]) <= y) best = i;
    }
    return best;
  }

  function paint() {
    dots.forEach(function (d, i) {
      d.classList.toggle('on', i === cur);
      if (i === cur) d.setAttribute('aria-current', 'true'); else d.removeAttribute('aria-current');
    });
    if (counter) counter.textContent = (chapters[cur].getAttribute('data-num') || (cur + 1)) + ' / ' + chapters.length;
    if (prevBtn) prevBtn.disabled = cur === 0;
    if (nextBtn) nextBtn.disabled = cur === chapters.length - 1;
    try { sessionStorage.setItem(STORE, chapters[cur].id); } catch (err) {}
  }

  function clampToChapter() {
    if (moving) return;
    var b = bounds(cur);
    var y = window.pageYOffset;
    if (y > b[1] + 1) window.scrollTo(0, b[1]);
    else if (y < b[0] - 1) window.scrollTo(0, b[0]);
  }

  function goTo(i) {
    if (i < 0 || i >= chapters.length) return;
    cur = i;
    moving = true;
    window.clearTimeout(moveTimer);
    window.scrollTo({ top: bounds(i)[0], behavior: reduced.matches ? 'auto' : 'smooth' });
    if (history.replaceState) history.replaceState(null, '', '#' + chapters[i].id);
    paint();
    moveTimer = window.setTimeout(function () {
      moving = false;
      clampToChapter();
    }, reduced.matches ? 80 : 700);
  }

  function step(dir) {
    if (dir > 0) { if (cur < chapters.length - 1) goTo(cur + 1); }
    else if (cur > 0) goTo(cur - 1);
  }

  if (prevBtn) prevBtn.addEventListener('click', function () { step(-1); });
  if (nextBtn) nextBtn.addEventListener('click', function () { step(1); });

  /* teclado: mueve el scroll dentro del capítulo, nunca lo cambia */
  window.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') e.preventDefault();
  });

  var ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      clampToChapter();
      ticking = false;
    });
  }, { passive: true });

  window.addEventListener('resize', function () {
    clampToChapter();
    var b = bounds(cur);
    if (window.pageYOffset < b[0] - 1) window.scrollTo(0, b[0]);
  });

  /* revelados */
  var revs = Array.prototype.slice.call(document.querySelectorAll('.reveal'));
  if ('IntersectionObserver' in window && !reduced.matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: .05 });
    revs.forEach(function (el) { io.observe(el); });
  } else {
    revs.forEach(function (el) { el.classList.add('in'); });
  }

  /* capítulo inicial: hash, o el último visitado al volver de un eje */
  function boot() {
    var hash = (location.hash || '').replace('#', '');
    var target = 0;
    if (hash) {
      chapters.forEach(function (ch, i) { if (ch.id === hash) target = i; });
    } else {
      try {
        var last = sessionStorage.getItem(STORE);
        if (last) chapters.forEach(function (ch, i) { if (ch.id === last) target = i; });
      } catch (err) {}
    }
    cur = target;
    paint();
    var b = bounds(target);
    var y = window.pageYOffset;
    if (y < b[0] - 1 || y > b[1] + 1) window.scrollTo(0, b[0]);
    document.documentElement.classList.add('deck-ready');
  }

  boot();

  window.addEventListener('hashchange', function () {
    var hash = (location.hash || '').replace('#', '');
    chapters.forEach(function (ch, i) {
      if (ch.id === hash && i !== cur) goTo(i);
    });
  });
})();