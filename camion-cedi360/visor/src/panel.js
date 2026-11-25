/* =========================================================
   CEDI 360 · Panel de operación
   Simulacro de la operación del CEDI sobre el modelo 3D:
   iluminación, portones, cortinas, puerta del frío, AMR y
   banda, llegada de furgoneta con cargue y descargue, alarma
   y corte de energía.

   Los objetos que mueve salen de blender/simulacion.py, con el
   pivote resuelto: los portones cuelgan del dintel, la hoja del
   frío corre sobre su vano y la carga viaja oculta hasta que el
   simulacro la suelta.
   ========================================================= */

const VELOCIDAD = 5.5;

const LUCES = {
  nave: ['M_Alm_Luz'],
  jardin: ['M_Pas_Luz'],
  admin: ['M_Adm_Luz'],
  patio: ['M_Luz_Torre']
};

/* el estado de cada interruptor y el objetivo de la animación */
const INICIAL = () => ({
  luces: { nave: true, jardin: true, admin: true, patio: true },
  noche: false,
  portones: [false, false, false],
  cortinas: false,
  frio: false,
  sistemas: false,
  furgoneta: false,
  carga: 0,
  alarma: false,
  corte: false
});

export function crearPanel(ctx) {
  const { escena, modelo, luces } = ctx;
  const estado = INICIAL();
  const paso = { porton: [0, 0, 0], frio: 0, cortina: 0, furgoneta: 0 };

  /* ----------------------------- referencias del modelo */
  const porNombre = (n) => modelo.getObjectByName(n) || null;
  const porPrefijo = (p) => {
    const salida = [];
    modelo.traverse((o) => {
      if (o.name && o.name.indexOf(p) === 0) salida.push(o);
    });
    return salida.sort((a, b) => (a.name < b.name ? -1 : 1));
  };

  const portones = [0, 1, 2]
    .map((i) => porNombre('SIM_Puerta_Muelle_' + i))
    .filter(Boolean);
  const puertaFrio = porNombre('SIM_Puerta_Frio');
  const cortinas = porPrefijo('Muelle_Tira_');
  const cajas = porPrefijo('SIM_Caja_');
  const palets = porPrefijo('SIM_Palet_');
  const amr = porPrefijo('SIM_AMR_');
  const banda = porPrefijo('SIM_Banda_Caja_');
  const balizas = porPrefijo('SIM_Baliza_');
  const furgoneta = porNombre('FUR_Unidad_0');

  /* posiciones de partida, para volver siempre al mismo sitio */
  const base = new Map();
  [puertaFrio, furgoneta].concat(amr, banda, cajas, palets).forEach((o) => {
    if (o) base.set(o, { x: o.position.x, y: o.position.y, z: o.position.z, ry: o.rotation.y });
  });
  if (furgoneta) {
    base.set('furgoneta', {
      x: furgoneta.position.x, y: furgoneta.position.y, z: furgoneta.position.z,
      ry: furgoneta.rotation.y
    });
  }
  const baseDe = (o) => base.get(o) || { x: 0, y: 0, z: 0, ry: 0 };

  /* ----------------------------- materiales de luz */
  const materiales = new Map();
  modelo.traverse((o) => {
    if (!o.material) return;
    const n = (o.material.name || '').replace(/\.\d+$/, '');
    if (!materiales.has(n)) materiales.set(n, o.material);
  });
  const brilloBase = new Map();
  materiales.forEach((m) => brilloBase.set(m, m.emissiveIntensity));
  const alarmaMat = materiales.get('M_Sim_Alarma');

  const ambienteBase = {
    hemi: luces && luces.hemi ? luces.hemi.intensity : 0.75,
    dir: luces && luces.dir ? luces.dir.intensity : 1.45,
    contra: luces && luces.contra ? luces.contra.intensity : 0.7,
    fondo: escena.background ? escena.background.clone() : null
  };

  /* las piezas de simulacro arrancan escondidas */
  cajas.concat(palets, amr, banda, balizas).forEach((o) => { o.visible = false; });
  balizas.forEach((o) => o.scale.setScalar(1.9));
  if (puertaFrio) puertaFrio.position.z = baseDe(puertaFrio).z;
  portones.forEach((o) => { o.scale.y = 1; });

  /* ----------------------------- luces */
  function aplicarLuces(dt) {
    Object.keys(LUCES).forEach((clave) => {
      const encendida = estado.luces[clave] && !estado.corte;
      LUCES[clave].forEach((nombre) => {
        const m = materiales.get(nombre);
        if (!m) return;
        const objetivo = encendida ? brilloBase.get(m) : 0.03;
        m.emissiveIntensity += (objetivo - m.emissiveIntensity) * Math.min(1, dt * VELOCIDAD);
      });
    });

    const noche = estado.noche || estado.corte;
    const k = Math.min(1, dt * 2.2);
    if (luces) {
      if (luces.hemi) luces.hemi.intensity += ((noche ? 0.22 : ambienteBase.hemi) - luces.hemi.intensity) * k;
      if (luces.dir) luces.dir.intensity += ((noche ? 0.24 : ambienteBase.dir) - luces.dir.intensity) * k;
      if (luces.contra) luces.contra.intensity += ((noche ? 0.14 : ambienteBase.contra) - luces.contra.intensity) * k;
    }
    if (ambienteBase.fondo && escena.background && escena.background.setHex) {
      const destino = noche ? 0x05080C : ambienteBase.fondo.getHex();
      escena.background.setHex(destino);
    }
  }

  /* ----------------------------- alarma */
  let pulso = 0;
  function aplicarAlarma(dt, reloj) {
    pulso += dt;
    balizas.forEach((o) => { o.visible = estado.alarma; });
    if (alarmaMat) {
      const base0 = brilloBase.get(alarmaMat) || 1.6;
      alarmaMat.emissiveIntensity = estado.alarma
        ? 0.4 + Math.abs(Math.sin(reloj * 3.4)) * (base0 + 1.6)
        : base0;
    }
    if (estado.alarma && estado.luces.nave && !estado.corte) {
      // con la alarma encendida la nave parpadea en la traza de video
      const m = materiales.get('M_Alm_Lente');
      if (m) m.emissiveIntensity = 1.2 + Math.abs(Math.sin(reloj * 3.4)) * 2.2;
    }
  }

  /* ----------------------------- puertas y sistemas */
  function aplicarPuertas(dt) {
    portones.forEach((o, i) => {
      const objetivo = estado.portones[i] ? 1 : 0;
      paso.porton[i] += (objetivo - paso.porton[i]) * Math.min(1, dt * 2.6);
      o.scale.y = 1 - 0.94 * paso.porton[i];
      o.visible = paso.porton[i] < 0.995;
    });

    if (puertaFrio) {
      const objetivo = estado.frio ? 1 : 0;
      paso.frio += (objetivo - paso.frio) * Math.min(1, dt * 2.4);
      puertaFrio.position.z = baseDe(puertaFrio).z - 2.30 * paso.frio;
    }

    const objetivoCortina = estado.cortinas ? 1 : 0;
    paso.cortina += (objetivoCortina - paso.cortina) * Math.min(1, dt * 2.6);
    cortinas.forEach((o, i) => {
      const signo = i % 2 ? 1 : -1;
      o.rotation.y = signo * 0.62 * paso.cortina;
    });
  }

  let reloj = 0;
  function aplicarSistemas(dt) {
    reloj += dt;
    const activo = estado.sistemas && !estado.corte;
    amr.forEach((o, i) => {
      o.visible = estado.sistemas;
      if (!activo) return;
      const b = baseDe(o);
      const fase = reloj * 0.42 + i * Math.PI;
      o.position.z = b.z + Math.sin(fase) * 9.5;
      o.position.x = b.x + Math.cos(fase * 0.5) * 0.18;
    });
    banda.forEach((o, i) => {
      o.visible = estado.sistemas;
      if (!activo) return;
      const b = baseDe(o);
      const recorrido = 30;
      const t = ((reloj * 1.6 + i * 4.3) % recorrido) / recorrido;
      o.position.z = b.z + 15 - t * recorrido;
    });
  }

  /* ----------------------------- furgoneta, carga y descargue */
  const DESTINO = { x: -3.20, y: 0.0, z: 16.40, ry: -Math.PI / 2 };

  function aplicarFurgoneta(dt) {
    if (!furgoneta) return;
    const b = baseDe('furgoneta');
    const objetivo = estado.furgoneta ? 1 : 0;
    paso.furgoneta += (objetivo - paso.furgoneta) * Math.min(1, dt * 0.55);
    const t = paso.furgoneta;
    furgoneta.position.x = b.x + (DESTINO.x - b.x) * t;
    furgoneta.position.y = b.y + (DESTINO.y - b.y) * t;
    furgoneta.position.z = b.z + (DESTINO.z - b.z) * t;
    let giro = DESTINO.ry - b.ry;
    while (giro > Math.PI) giro -= Math.PI * 2;
    while (giro < -Math.PI) giro += Math.PI * 2;
    furgoneta.rotation.y = b.ry + giro * t;
  }

  function aplicarCarga(dt) {
    const total = cajas.length;
    cajas.forEach((o, i) => {
      const dentro = i < estado.carga;
      o.visible = dentro || o.userData.cayendo === true;
      if (dentro) {
        palets.forEach((p) => { p.visible = true; });
      }
    });
    palets.forEach((p) => { p.visible = estado.carga > 0; });
  }

  /* ----------------------------- interfaz */
  const CAJA = document.createElement('section');
  CAJA.className = 'sim-panel';
  CAJA.id = 'simPanel';
  CAJA.hidden = true;

  const filas = [
    { titulo: 'Iluminación', items: [
      { id: 'luz-nave', texto: 'Nave y andén', tipo: 'luz', clave: 'nave' },
      { id: 'luz-jardin', texto: 'Jardín y pasillo', tipo: 'luz', clave: 'jardin' },
      { id: 'luz-admin', texto: 'Anexo administrativo', tipo: 'luz', clave: 'admin' },
      { id: 'luz-patio', texto: 'Patio y torres', tipo: 'luz', clave: 'patio' },
      { id: 'noche', texto: 'Ambiente nocturno', tipo: 'simple', clave: 'noche' }
    ] },
    { titulo: 'Puertas y accesos', items: [
      { id: 'p0', texto: 'Portón muelle 01', tipo: 'porton', indice: 0 },
      { id: 'p1', texto: 'Portón muelle 02', tipo: 'porton', indice: 1 },
      { id: 'p2', texto: 'Portón muelle 03', tipo: 'porton', indice: 2 },
      { id: 'cortinas', texto: 'Cortinas de tiras', tipo: 'simple', clave: 'cortinas' },
      { id: 'frio', texto: 'Puerta corredera del frío', tipo: 'simple', clave: 'frio' }
    ] },
    { titulo: 'Sistemas', items: [
      { id: 'sistemas', texto: 'Banda troncal y AMR', tipo: 'simple', clave: 'sistemas' }
    ] },
    { titulo: 'Simulacro', items: [
      { id: 'furgo', texto: 'Llega la furgoneta', tipo: 'simple', clave: 'furgoneta' },
      { id: 'cargar', texto: 'Descargar paquetes', tipo: 'carga', delta: 4 },
      { id: 'vaciar', texto: 'Retirar la carga', tipo: 'carga', delta: -4 },
      { id: 'alarma', texto: 'Alarma de intrusión', tipo: 'simple', clave: 'alarma' },
      { id: 'corte', texto: 'Corte de energía', tipo: 'simple', clave: 'corte' },
      { id: 'reset', texto: 'Restablecer el turno', tipo: 'reset' }
    ] }
  ];

  const botones = new Map();
  const AVISO = document.createElement('p');
  AVISO.className = 'sim-aviso';
  AVISO.setAttribute('aria-live', 'polite');

  const cabecera = document.createElement('header');
  cabecera.className = 'sim-cab';
  cabecera.innerHTML = '<b>Panel de operación</b><span>Simulacro en vivo del CEDI</span>';
  const cerrar = document.createElement('button');
  cerrar.type = 'button';
  cerrar.className = 'sim-x';
  cerrar.setAttribute('aria-label', 'Cerrar el panel');
  cerrar.textContent = '×';
  cabecera.appendChild(cerrar);
  CAJA.appendChild(cabecera);

  const cuerpo = document.createElement('div');
  cuerpo.className = 'sim-cuerpo';
  filas.forEach((fila) => {
    const h = document.createElement('h4');
    h.textContent = fila.titulo;
    cuerpo.appendChild(h);
    const lista = document.createElement('div');
    lista.className = 'sim-lista';
    fila.items.forEach((item) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'sim-btn';
      b.id = 'sim-' + item.id;
      b.textContent = item.texto;
      b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', () => accionar(item));
      lista.appendChild(b);
      botones.set(item.id, b);
    });
    cuerpo.appendChild(lista);
  });
  CAJA.appendChild(cuerpo);
  CAJA.appendChild(AVISO);

  const anfitrion = document.getElementById('rec') || document.body;
  anfitrion.appendChild(CAJA);

  const BOTON = document.getElementById('visorPanel');
  const abrir = (valor) => {
    CAJA.hidden = !valor;
    if (BOTON) BOTON.setAttribute('aria-pressed', valor ? 'true' : 'false');
    if (BOTON) BOTON.classList.toggle('activo', !!valor);
  };
  if (BOTON) BOTON.addEventListener('click', () => abrir(CAJA.hidden));
  cerrar.addEventListener('click', () => abrir(false));

  /* ----------------------------- acciones */
  function aviso(texto, tipo) {
    AVISO.textContent = texto || '';
    AVISO.className = 'sim-aviso' + (tipo ? ' ' + tipo : '');
    AVISO.hidden = !texto;
  }

  function accionar(item) {
    if (item.tipo === 'luz') {
      estado.luces[item.clave] = !estado.luces[item.clave];
      if (estado.luces[item.clave]) estado.corte = false;
    } else if (item.tipo === 'porton') {
      estado.portones[item.indice] = !estado.portones[item.indice];
      aviso(estado.portones[item.indice]
        ? 'Muelle 0' + (item.indice + 1) + ' habilitado para cargue'
        : 'Muelle 0' + (item.indice + 1) + ' cerrado y asegurado', 'ok');
    } else if (item.tipo === 'carga') {
      estado.carga = Math.max(0, Math.min(cajas.length, estado.carga + item.delta));
      aviso(estado.carga === 0
        ? 'Andén despejado'
        : estado.carga + ' de ' + cajas.length + ' paquetes en el andén', 'ok');
    } else if (item.tipo === 'reset') {
      Object.assign(estado, INICIAL());
      aviso('Turno restablecido', 'ok');
    } else {
      const clave = item.clave;
      estado[clave] = !estado[clave];
      if (clave === 'corte' && estado.corte) {
        estado.luces = { nave: false, jardin: false, admin: false, patio: false };
        aviso('Falla de red · UPS y planta asumen la carga crítica', 'alerta');
      } else if (clave === 'corte') {
        estado.luces = { nave: true, jardin: true, admin: true, patio: true };
        aviso('Red restablecida · cargas de nuevo en servicio', 'ok');
      } else if (clave === 'alarma') {
        aviso(estado.alarma
          ? 'ALARMA · intrusión en muelle 02 · CCTV grabando'
          : 'Alarma restablecida · evento cerrado en acta', estado.alarma ? 'alerta' : 'ok');
      } else if (clave === 'furgoneta') {
        aviso(estado.furgoneta
          ? 'Furgoneta en el andén · descargue autorizado'
          : 'Furgoneta retirada · patio liberado', 'ok');
      } else if (clave === 'sistemas') {
        aviso(estado.sistemas
          ? 'Banda troncal y AMR en operación'
          : 'Banda troncal detenida', 'ok');
      } else if (clave === 'frio') {
        aviso(estado.frio ? 'Cámara abierta · temperatura en vigilancia' : 'Cámara cerrada', 'ok');
      } else if (clave === 'noche') {
        aviso(estado.noche ? 'Escena nocturna · solo luces de operación' : 'Escena diurna', '');
      } else if (clave === 'cortinas') {
        aviso(estado.cortinas ? 'Cortinas abiertas' : 'Cortinas cerradas', '');
      }
    }
    pintar();
  }

  function pintar() {
    botones.forEach((b, id) => {
      let encendido = false;
      if (id === 'luz-nave') encendido = estado.luces.nave;
      else if (id === 'luz-jardin') encendido = estado.luces.jardin;
      else if (id === 'luz-admin') encendido = estado.luces.admin;
      else if (id === 'luz-patio') encendido = estado.luces.patio;
      else if (id === 'p0') encendido = estado.portones[0];
      else if (id === 'p1') encendido = estado.portones[1];
      else if (id === 'p2') encendido = estado.portones[2];
      else if (id === 'cargar' || id === 'vaciar') {
        b.textContent = id === 'cargar' ? 'Descargar paquetes' : 'Retirar la carga';
        encendido = false;
      } else {
        const clave = id;
        if (clave in estado && typeof estado[clave] === 'boolean') encendido = estado[clave];
      }
      b.setAttribute('aria-pressed', encendido ? 'true' : 'false');
      b.classList.toggle('activo', !!encendido);
    });
    if (botones.has('cargar')) {
      botones.get('cargar').textContent = 'Descargar (' + estado.carga + '/' + cajas.length + ')';
    }
  }

  pintar();

  return {
    abrir: (v) => abrir(v === undefined ? true : v),
    tick(dt) {
      const relojAlarma = performance.now() / 1000;
      aplicarLuces(dt);
      aplicarAlarma(dt, relojAlarma);
      aplicarPuertas(dt);
      aplicarSistemas(dt);
      aplicarFurgoneta(dt);
      aplicarCarga(dt);
    },
    estado
  };
}
