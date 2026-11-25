/* =========================================================
   Armador de alcance (sin precios) y filtros de la matriz.
   ========================================================= */
(function () {
  'use strict';

  /* ---------------- armador ---------------- */
  var form = document.getElementById('armadorForm');
  var out = document.getElementById('armadorOut');
  if (form && out) {
    var NOMBRE = {
      A: 'Seguridad electrónica e inteligencia aplicada',
      B: 'Infraestructura tecnológica y telecomunicaciones',
      C: 'Ingeniería, energía y mantenimiento',
      D: 'Facility management y servicios complementarios'
    };
    var ENTREGA = {
      A: 'Arquitectura de referencia de CCTV y matriz de acceso por rol',
      B: 'Diseño lógico y físico de red con planos as-built',
      C: 'Estudio de cargas, informe termográfico y plan de mantenimiento',
      D: 'Mesa de servicio única con SLA y reporte mensual por sede'
    };
    var VENTANA = {
      'sin-afectar': 'trabajo por ventanas autorizadas, sin cerrar el despacho',
      'nocturna': 'intervención nocturna, con permiso de trabajo y plan de contingencia',
      'fin-semana': 'intervención en fin de semana, con acompañamiento de operación'
    };

    function checked(name) {
      return Array.prototype.slice.call(form.querySelectorAll('input[name="' + name + '"]:checked')).map(function (i) { return i.value; });
    }

    function render() {
      var sedes = parseInt((checked('sedes')[0] || '2'), 10);
      var ejes = checked('eje');
      var crit = checked('crit')[0] || 'continuidad';
      var ventana = checked('ventana')[0] || 'sin-afectar';

      if (!ejes.length) {
        out.innerHTML = '<p class="small" style="margin:0">Elige al menos un eje para armar el alcance.</p>';
        return;
      }

      var semanas = 4 + Math.max(0, sedes - 2) + Math.max(0, ejes.length - 1);
      var visitas = sedes;
      var fases = ['Fase 0 · Diagnóstico'];
      if (crit === 'continuidad' || ejes.indexOf('A') > -1 || ejes.indexOf('B') > -1) fases.push('Fase 1 · Estabilización');
      if (ejes.length >= 2) fases.push('Fase 2 · Modernización');
      if (ejes.indexOf('A') > -1 || ejes.indexOf('B') > -1) fases.push('Fase 3 · Inteligencia');
      if (ejes.indexOf('D') > -1) fases.push('Fase 4 · Acompañamiento');

      var html = '';
      html += '<p class="armador-big">' + semanas + ' semanas de Fase 0</p>';
      html += '<p class="small" style="margin:2px 0 0">' + (ejes.length === 1 ? 'un eje' : ejes.length + ' ejes') + ' en ' + sedes + ' sedes · ' + visitas + ' visitas técnicas</p>';

      html += '<h4>Ejes incluidos</h4><ul>';
      ejes.forEach(function (e) { html += '<li><strong>Eje ' + e + '.</strong> ' + NOMBRE[e] + '</li>'; });
      html += '</ul>';

      html += '<h4>Entregables que salen de la Fase 0</h4><ul>';
      ejes.forEach(function (e) { html += '<li>' + ENTREGA[e] + '</li>'; });
      html += '<li>Informe de diagnóstico por sede e IMI por dimensión</li>';
      html += '<li>Plan maestro priorizado y alcance por fase (base para cotizar)</li>';
      html += '</ul>';

      html += '<h4>Fases sugeridas</h4><ul>';
      fases.forEach(function (f) { html += '<li>' + f + '</li>'; });
      html += '</ul>';

      html += '<h4>Condición de ejecución</h4><p class="small" style="margin:0">' + VENTANA[ventana] + '.</p>';
      html += '<p class="small" style="margin:10px 0 0">Cálculo de referencia: 4 semanas base + 1 por sede adicional + 1 por eje adicional.</p>';

      out.innerHTML = html;
    }

    form.addEventListener('change', render);
    form.addEventListener('input', render);
    render();

    var copy = document.getElementById('armadorCopy');
    if (copy) {
      copy.addEventListener('click', function () {
        var txt = (out.innerText || out.textContent || '').trim();
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(txt).then(function () {
            copy.textContent = 'Resumen copiado';
            window.setTimeout(function () { copy.textContent = 'Copiar resumen'; }, 1800);
          });
        }
      });
    }
  }

  /* ---------------- matriz ---------------- */
  var matriz = document.getElementById('matriz');
  if (matriz) {
    var botones = Array.prototype.slice.call(matriz.querySelectorAll('.matriz-filter button'));
    botones.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var fase = btn.getAttribute('data-fase');
        var on = btn.classList.toggle('on');
        btn.setAttribute('aria-pressed', on ? 'true' : 'false');
        Array.prototype.slice.call(matriz.querySelectorAll('[data-fase="' + fase + '"]')).forEach(function (cell) {
          if (cell === btn) return;
          cell.classList.toggle('off', !on);
        });
      });
      btn.setAttribute('aria-pressed', 'true');
    });
  }
})();