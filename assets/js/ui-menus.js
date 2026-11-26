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
