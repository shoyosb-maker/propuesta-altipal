/* =========================================================
   CEDI 360 · menús: resplandor que sigue al cursor
   Escribe --ui-mx / --ui-my en la superficie que está bajo el
   puntero y ui-menus.css los usa como centro del degradado.
   Si el script no corre, el CSS cae en una posición por
   defecto y la interfaz se ve igual.
   ========================================================= */
(function () {
  if (window.matchMedia && window.matchMedia('(hover:none)').matches) return;

  var SEL = '.topbar,.deck-dots,.deck-arrows,.doc-nav,.rec-rail,.rec-hud,.rec-menu-btn,.sim-panel';

  function mover(e) {
    var r = this.getBoundingClientRect();
    if (!r.width || !r.height) return;
    this.style.setProperty('--ui-mx', (((e.clientX - r.left) / r.width) * 100).toFixed(2) + '%');
    this.style.setProperty('--ui-my', (((e.clientY - r.top) / r.height) * 100).toFixed(2) + '%');
  }

  function salir() {
    this.style.removeProperty('--ui-mx');
    this.style.removeProperty('--ui-my');
  }

  function registrar() {
    var lista = document.querySelectorAll(SEL);
    for (var i = 0; i < lista.length; i++) {
      var el = lista[i];
      if (el.dataset.uiLuz) continue;
      el.dataset.uiLuz = '1';
      el.addEventListener('pointermove', mover, { passive: true });
      el.addEventListener('pointerleave', salir, { passive: true });
    }
  }

  function arrancar() {
    registrar();
    // el panel de operación y el menú del recorrido se crean después del glb
    if (window.MutationObserver) {
      var pendiente = 0;
      new MutationObserver(function () {
        clearTimeout(pendiente);
        pendiente = setTimeout(registrar, 120);
      }).observe(document.body, { childList: true, subtree: true });
    }
    window.addEventListener('load', registrar);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', arrancar);
  } else {
    arrancar();
  }
})();

/* =========================================================
   CEDI 360 · modo día / modo noche
   Escribe data-tema en <html>, lo recuerda en localStorage y
   pinta el interruptor en la barra superior de las páginas de
   papel. El recorrido 3D ya es noche por diseño: allí no va.
   ========================================================= */
(function () {
  var CLAVE = 'cedi:tema';
  var raiz = document.documentElement;
  var boton = null;
  var ICONOS =
    '<svg class="ico-sol" viewBox="0 0 24 24" aria-hidden="true">' +
    '<circle cx="12" cy="12" r="4.2"/>' +
    '<path d="M12 2.6v2.2M12 19.2v2.2M2.6 12h2.2M19.2 12h2.2M5.4 5.4l1.6 1.6M17 17l1.6 1.6M18.6 5.4L17 7M7 17l-1.6 1.6"/>' +
    '</svg>' +
    '<svg class="ico-luna" viewBox="0 0 24 24" aria-hidden="true">' +
    '<path d="M20.2 14.6A8.6 8.6 0 0 1 9.4 3.8a8.6 8.6 0 1 0 10.8 10.8z"/></svg>';

  function leer() {
    try { return localStorage.getItem(CLAVE) === 'noche' ? 'noche' : 'dia'; }
    catch (e) { return 'dia'; }
  }
  function guardar(tema) {
    try { localStorage.setItem(CLAVE, tema); } catch (e) {}
  }
  function pintar(tema) {
    var noche = tema === 'noche';
    raiz.setAttribute('data-tema', tema);
    if (boton) {
      var rotulo = noche ? 'Cambiar a modo día' : 'Cambiar a modo noche';
      boton.setAttribute('aria-pressed', noche ? 'true' : 'false');
      boton.setAttribute('title', rotulo);
      boton.setAttribute('aria-label', rotulo);
    }
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', noche ? '#0B1116' : '#F2F0E9');
  }
  function alternar() {
    var tema = raiz.getAttribute('data-tema') === 'noche' ? 'dia' : 'noche';
    pintar(tema);
    guardar(tema);
  }
  function crear() {
    var cont = document.querySelector('.tb-right');
    if (!cont || document.getElementById('temaBtn')) return;
    boton = document.createElement('button');
    boton.type = 'button';
    boton.id = 'temaBtn';
    boton.className = 'btn btn-ghost btn-tema';
    boton.innerHTML = ICONOS;
    boton.addEventListener('click', alternar);
    cont.insertBefore(boton, cont.firstChild);
    pintar(raiz.getAttribute('data-tema') || leer());
  }

  if (document.body && document.body.classList.contains('recorrido-page')) return;
  pintar(raiz.getAttribute('data-tema') || leer());
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', crear);
  } else {
    crear();
  }
})();
