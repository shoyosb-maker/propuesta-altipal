/* =========================================================
   CEDI 360 · Panel de operación
   Simulacro de la operación del CEDI sobre el modelo 3D:
   iluminación, portones, cortinas, puerta del frío, pausa de
   la banda de boxes, descargue del andén, alarma y corte de
   energía.

   Los objetos que mueve salen de blender/simulacion.py, con el
   pivote resuelto: los portones cuelgan del dintel, la hoja del
   frío corre sobre su vano y la carga viaja oculta hasta que el
   simulacro la suelta.
   ========================================================= */

import * as THREE from 'three';

const VELOCIDAD = 5.5;

const LUCES = {
  nave: ['M_Alm_Luz'],
  jardin: ['M_Pas_Luz'],
  admin: ['M_Adm_Luz'],
  patio: ['M_Luz_Torre']
};

/* focos reales por zona: son los que hacen visible el encendido y apagado
   sobre el piso, las estanterías y la carga (las luminarias del modelo solo
   brillan; no alumbran) */
const FOCOS = {
  nave: { color: 0xfff0c8, fuerza: 120, dist: 34, decay: 1.6,
    sitios: [[-50, 10.4, 20], [-38, 10.4, 12], [-26, 10.4, 4],
             [-50, 10.4, 4], [-38, 10.4, -4], [-26, 10.4, -12]] },
  anden: { color: 0xdfe6ea, fuerza: 55, dist: 18, decay: 1.7,
    sitios: [[-9.2, 5.4, 18], [-9.2, 5.4, 4]] },
  jardin: { color: 0xfff6da, fuerza: 22, dist: 12, decay: 1.8,
    sitios: [[-69.6, 3.9, 22], [-65.0, 3.9, 10]] },
  admin: { color: 0xfff6da, fuerza: 45, dist: 16, decay: 1.8,
    sitios: [[-32.0, 3.2, -24.5]] }
};

/* el estado de cada interruptor y el objetivo de la animación */
const INICIAL = () => ({
  luces: { nave: true, jardin: true, admin: true, patio: true },
  noche: false,
  portones: [false, false, false],
  cortinas: false,
  frio: false,
  banda: true,
  carga: 0,
  alarma: false,
  corte: false,
  camaras: { muelles: true, interiores: true, perimetro: true }
});

const CANALES = { muelles: [0, 1, 2], interiores: [3, 4, 5, 6, 7, 8, 9],
  perimetro: [10, 11] };

/* resplandor radial del artefacto encendido, sin cargar una imagen */
function texturaHalo() {
  const lado = 128;
  const lienzo = document.createElement('canvas');
  lienzo.width = lienzo.height = lado;
  const ctx = lienzo.getContext('2d');
  const g = ctx.createRadialGradient(lado / 2, lado / 2, 0, lado / 2, lado / 2, lado / 2);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.35, 'rgba(255,255,255,0.42)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, lado, lado);
  return new THREE.CanvasTexture(lienzo);
}

export function crearPanel(ctx) {
  const { escena, modelo, luces, muro } = ctx;
  const estado = INICIAL();
  const paso = { porton: [0, 0, 0], frio: 0, cortina: 0 };

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
  const banda = porPrefijo('SIM_Banda_Caja_');
  const balizas = porPrefijo('SIM_Baliza_');

  /* posiciones de partida, para volver siempre al mismo sitio */
  const base = new Map();
  [puertaFrio].concat(banda, cajas, palets).forEach((o) => {
    if (o) base.set(o, { x: o.position.x, y: o.position.y, z: o.position.z, ry: o.rotation.y });
  });
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

  /* la carga y las balizas arrancan escondidas; la banda de boxes
     trabaja desde el primer segundo. Los AMR no entran al visor: la
     única pieza en movimiento de este sistema es la banda con sus cajas */
  cajas.concat(palets, balizas).forEach((o) => { o.visible = false; });
  banda.forEach((o) => { o.visible = true; });
  porPrefijo('SIM_AMR_').forEach((o) => { o.visible = false; });
  balizas.forEach((o) => o.scale.setScalar(1.9));

  /* focos por zona: el encendido se ve en el piso y en las estanterías.
     Cada foco lleva un cono aditivo (el haz de la luminaria) y un halo
     (el resplandor del artefacto): al apagar la zona desaparecen los dos */
  const HALO = texturaHalo();
  const focos = [];
  Object.keys(FOCOS).forEach((zona) => {
    const def = FOCOS[zona];
    def.sitios.forEach((p) => {
      const luz = new THREE.PointLight(def.color, def.fuerza, def.dist, def.decay);
      luz.position.set(p[0], p[1], p[2]);
      escena.add(luz);

      const alto = Math.max(4, p[1] - 1.0);
      const ancho = zona === 'nave' ? 2.9 : 2.0;
      const cono = new THREE.Mesh(
        new THREE.ConeGeometry(ancho, alto, 16, 1, true),
        new THREE.MeshBasicMaterial({
          color: def.color, transparent: true, opacity: 0.16,
          blending: THREE.AdditiveBlending, depthWrite: false,
          side: THREE.DoubleSide
        })
      );
      cono.position.set(p[0], p[1] - alto / 2, p[2]);
      cono.renderOrder = 3;
      escena.add(cono);

      const halo = new THREE.Sprite(new THREE.SpriteMaterial({
        map: HALO, color: def.color, transparent: true, opacity: 0.5,
        blending: THREE.AdditiveBlending, depthWrite: false
      }));
      halo.position.set(p[0], p[1] - 0.35, p[2]);
      halo.scale.setScalar(zona === 'nave' ? 5.6 : 4.0);
      halo.renderOrder = 4;
      escena.add(halo);

      focos.push({ zona, luz, cono, halo, base: def.fuerza, tope: 0.16 });
    });
  });
  if (puertaFrio) puertaFrio.position.z = baseDe(puertaFrio).z;
  portones.forEach((o) => { o.scale.y = 1; });

  /* ----------------------------- luces */
  function aplicarLuces(dt) {
    Object.keys(LUCES).forEach((clave) => {
      const encendida = estado.luces[clave] && !estado.corte;
      LUCES[clave].forEach((nombre) => {
        const m = materiales.get(nombre);
        if (!m) return;
        const objetivo = encendida ? brilloBase.get(m) * 2.2 : 0.02;
        m.emissiveIntensity += (objetivo - m.emissiveIntensity) * Math.min(1, dt * VELOCIDAD);
      });
    });

    focos.forEach((f) => {
      const encendida = estado.luces[f.zona] && !estado.corte;
      const objetivo = encendida ? f.base : 0;
      f.luz.intensity += (objetivo - f.luz.intensity) * Math.min(1, dt * VELOCIDAD);
      const opacidad = f.base > 0 ? f.tope * (f.luz.intensity / f.base) : 0;
      f.cono.material.opacity = opacidad;
      f.cono.visible = opacidad > 0.004;
      f.halo.material.opacity = opacidad * 2.1;
      f.halo.visible = opacidad > 0.004;
    });

    const noche = estado.noche || estado.corte;
    const k = Math.min(1, dt * 2.2);
    if (luces) {
      if (luces.hemi) luces.hemi.intensity += ((noche ? 0.18 : ambienteBase.hemi) - luces.hemi.intensity) * k;
      if (luces.dir) luces.dir.intensity += ((noche ? 0.20 : ambienteBase.dir) - luces.dir.intensity) * k;
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
  /* la banda solo recibe pausa y continuación: es la única pieza que se mueve */
  function aplicarBanda(dt) {
    reloj += dt;
    const enMarcha = estado.banda && !estado.corte;
    if (!enMarcha) return;
    banda.forEach((o, i) => {
      const b = baseDe(o);
      const recorrido = 30;
      const t = ((reloj * 1.6 + i * 4.3) % recorrido) / recorrido;
      o.position.z = b.z + 15 - t * recorrido;
    });
  }

  /* ----------------------------- carga y descargue del andén */
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
      { id: 'banda', texto: 'Banda de boxes', tipo: 'simple', clave: 'banda' }
    ] },
    { titulo: 'Seguridad electrónica', items: [
      { id: 'cam-muelles', texto: 'Cámaras de muelle', tipo: 'cam', clave: 'muelles' },
      { id: 'cam-interiores', texto: 'Cámaras interiores', tipo: 'cam', clave: 'interiores' },
      { id: 'cam-perimetro', texto: 'Cámaras de perímetro', tipo: 'cam', clave: 'perimetro' },
      { id: 'cam-nvr', texto: 'Grabación (NVR)', tipo: 'nvr' }
    ] },
    { titulo: 'Simulacro', items: [
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
    } else if (item.tipo === 'cam') {
      const clave = item.clave;
      const on = !estado.camaras[clave];
      estado.camaras[clave] = on;
      if (muro) muro.alternar(CANALES[clave], on);
      const cuantas = CANALES[clave].length;
      aviso(on
        ? cuantas + ' cámaras de ' + (clave === 'muelles' ? 'muelle' : clave) + ' en servicio'
        : cuantas + ' cámaras de ' + (clave === 'muelles' ? 'muelle' : clave)
          + ' fuera de servicio · evento en acta', on ? 'ok' : 'alerta');
    } else if (item.tipo === 'nvr') {
      const todas = estado.camaras.muelles && estado.camaras.interiores
        && estado.camaras.perimetro;
      const on = !todas;
      estado.camaras = { muelles: on, interiores: on, perimetro: on };
      if (muro) muro.alternar([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], on);
      aviso(on ? 'Grabación en marcha · 12 canales' : 'Grabación detenida · muro sin señal',
        on ? 'ok' : 'alerta');
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
      } else if (clave === 'banda') {
        aviso(estado.banda
          ? 'Banda de boxes en marcha'
          : 'Banda de boxes en pausa · los paquetes quedan detenidos', 'ok');
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
      else if (id === 'cam-muelles') encendido = estado.camaras.muelles;
      else if (id === 'cam-interiores') encendido = estado.camaras.interiores;
      else if (id === 'cam-perimetro') encendido = estado.camaras.perimetro;
      else if (id === 'cam-nvr') {
        encendido = estado.camaras.muelles && estado.camaras.interiores
          && estado.camaras.perimetro;
        b.textContent = encendido ? 'Grabación (12/12)' : 'Grabación detenida';
      }
      else if (id === 'banda') {
        b.textContent = estado.banda
          ? 'Banda de boxes · en marcha'
          : 'Banda de boxes · en pausa';
        encendido = estado.banda;
      }
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
    bandaActiva: () => estado.banda && !estado.corte,
    tick(dt) {
      const relojAlarma = performance.now() / 1000;
      aplicarLuces(dt);
      aplicarAlarma(dt, relojAlarma);
      aplicarPuertas(dt);
      aplicarBanda(dt);
      aplicarCarga(dt);
    },
    estado
  };
}
