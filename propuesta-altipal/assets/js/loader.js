/* Pantalla de carga: se retira cuando el documento está listo. */
(function () {
  'use strict';
  var loader = document.getElementById('pageLoader');
  if (!loader) return;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var MIN_MS = 700, MAX_MS = 6000, FADE_MS = 600;
  var t0 = Date.now();
  var done = false;

  function finish() {
    if (done) return;
    done = true;
    var wait = reduced.matches ? 0 : Math.max(0, MIN_MS - (Date.now() - t0));
    window.setTimeout(function () {
      loader.classList.add('done');
      window.setTimeout(function () { loader.style.display = 'none'; }, FADE_MS);
      document.documentElement.classList.add('is-ready');
    }, wait);
  }

  if (document.readyState === 'complete') finish();
  else window.addEventListener('load', finish);
  window.setTimeout(finish, MAX_MS);
})();