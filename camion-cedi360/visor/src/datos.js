/* =========================================================
   CEDI 360 · Capa de datos
   Puntos 1 y 2 de «De los datos al valor empresarial».

   La operación no se toca: encima de lo que ya registra la planta
   se lee. Cada instrumento se ancla al sitio del modelo donde
   nace su dato y muestra el tránsito dato -> información -> decisión.
   El punto 3 vive en la ficha del asistente gerencial: preguntas en
   lenguaje natural respondidas sobre una cifra verificable.
   ========================================================= */

import * as THREE from 'three';

const ZONAS = ['Patio y muelles', 'Cadena de frío', 'Energía',
  'Acceso y rutas', 'Nave', 'Anexo administrativo'];

const INSTRUMENTOS = [
  {
    id: 'tracking', corto: 'Tracking', zona: ZONAS[0],
    titulo: 'Tracking inteligente de vehículos', sitio: 'Patio de maniobras',
    p: [-2.0, 4.4, 8.0], secciones: ['recibo', 'contexto'],
    dato: 'Posición, hora de llegada y tiempo en patio de cada unidad.',
    valor: 'Retrasos, desviaciones de ruta y novedades operativas, a la vista.',
    decision: 'Priorizar el muelle y avisar a la tienda antes de que se rompa la ventana.'
  },
  {
    id: 'entregas', corto: 'Entregas', zona: ZONAS[0],
    titulo: 'Monitor de entregas hard discount', sitio: 'Muelle 02 · andén',
    p: [-9.2, 5.6, 11.0], secciones: ['recibo'],
    dato: 'Ventana horaria comprometida y sello de llegada por tienda.',
    valor: 'Cumplimiento de horarios y ventanas de entrega, tienda por tienda.',
    decision: 'Reordenar el despacho del día siguiente con la tienda que más se atrasa.'
  },
  {
    id: 'thermoking', corto: 'Thermo King', zona: ZONAS[0],
    titulo: 'Analizador de Thermo King', sitio: 'Muelle 03 · unidad refrigerada',
    p: [-9.2, 4.2, 17.5], secciones: ['recibo', 'automatizacion'],
    dato: 'Ciclos de funcionamiento, tiempos de parada y alarmas del equipo.',
    valor: 'Comportamientos anómalos del equipo de refrigeración, sin adivinar.',
    decision: 'Mandar inspección al equipo antes de que falle en ruta.'
  },
  {
    id: 'frio', corto: 'Cadena de frío', zona: ZONAS[1],
    titulo: 'Monitor de cadena de frío', sitio: 'Cámara de frío',
    p: [-79.0, 4.2, 22.0], secciones: ['frio'],
    dato: 'Temperatura, humedad, apertura de puerta y detector de fuga.',
    valor: 'Desviaciones de temperatura y riesgo de deterioro de la mercancía.',
    decision: 'Retener o liberar el lote con la traza a la vista.'
  },
  {
    id: 'logging', corto: 'Data logging', zona: ZONAS[1],
    titulo: 'Data logging inteligente', sitio: 'Cámara de frío · registrador',
    p: [-76.0, 3.4, 27.5], secciones: ['frio'],
    dato: 'Históricos, promedio, máximas, mínimas y tiempos fuera de rango.',
    valor: 'El histórico completo de la cámara, listo para la auditoría.',
    decision: 'Sostener el punto de ajuste o corregirlo con evidencia.'
  },
  {
    id: 'mantenimiento', corto: 'Mantenimiento', zona: ZONAS[2],
    titulo: 'Asistente de mantenimiento', sitio: 'Pabellón eléctrico',
    p: [-91.0, 3.4, 12.0], secciones: ['energia', 'redes'],
    dato: 'Horas de servicio, eventos del tablero y termografía por periodo.',
    valor: 'Patrones que ameritan inspección técnica o mantenimiento preventivo.',
    decision: 'Programar la parada técnica en la ventana de menor carga.'
  },
  {
    id: 'rutas', corto: 'Rutas', zona: ZONAS[3],
    titulo: 'Analizador de rutas', sitio: 'Acceso oeste · jardín',
    p: [-62.5, 4.2, 14.0], secciones: ['jardin', 'paso'],
    dato: 'Recorridos, tiempos de espera y consumo por viaje.',
    valor: 'Oportunidades de optimización de recorridos, tiempos y costos.',
    decision: 'Rediseñar el recorrido antes de sumar un vehículo.'
  },
  {
    id: 'cedi', corto: 'Gestor CEDI', zona: ZONAS[4],
    titulo: 'Gestor de centros de distribución', sitio: 'Nave de acopio',
    p: [-37.2, 7.6, 1.0], secciones: ['acopio', 'estanterias', 'automatizacion'],
    dato: 'Espera, cargue, descargue y disponibilidad de vehículos por muelle.',
    valor: 'La ocupación real del centro de distribución en el turno.',
    decision: 'Reasignar muelle, turno y personal con la cifra a la vista.'
  },
  {
    id: 'informes', corto: 'Informes', zona: ZONAS[5],
    titulo: 'Generador automático de informes', sitio: 'Anexo administrativo',
    p: [-30.0, 3.6, -26.0], secciones: ['admin'],
    dato: 'Los registros de los demás instrumentos, ya consolidados.',
    valor: 'Informes automáticos que reducen el trabajo administrativo.',
    decision: 'Llegar al comité con el informe listo y no con la consolidación pendiente.'
  },
  {
    id: 'ia', corto: 'Asistente IA', zona: ZONAS[5],
    titulo: 'Asistente gerencial con IA', sitio: 'Sala de juntas',
    p: [-27.0, 2.8, -28.5], secciones: ['admin'], consulta: true,
    dato: 'Los indicadores de la capa, consultados en lenguaje natural.',
    valor: 'Respuestas explicadas sobre la operación, sin hojas de cálculo de por medio.',
    decision: 'Decidir en la reunión con el dato y su explicación en pantalla.'
  }
];

/* preguntas del documento, con la cifra que las respalda: el modelo
   explica, el cálculo lo haría el servicio */
const CONSULTAS = [
  {
    q: '¿Cuáles vehículos presentaron desviaciones de temperatura en las últimas 24 horas?',
    filas: [['TRK-118 · muelle 02', '+6,4 °C · 47 min'], ['TRK-204 · muelle 03', '−1,8 °C · 22 min'],
      ['Unidades monitoreadas', '14']],
    texto: 'Dos de catorce unidades salieron del rango de 2 a 4 °C y las dos lo hicieron en la misma ventana de cargue: el patrón apunta al tiempo de puerta abierta, no al equipo.'
  },
  {
    q: '¿Qué equipos de refrigeración presentan ciclos diferentes a los habituales?',
    filas: [['Condensadora 02 · cuarto frío', '9 arranques/h'], ['Promedio de 30 días', '3,4 arranques/h'],
      ['Evaporador 01 · cuarto frío', '3,1 arranques/h']],
    texto: 'La condensadora 02 casi triplica sus arranques: revisar carga de refrigerante y sello de puerta antes de que el compresor lo pague.'
  },
  {
    q: '¿Cuáles tiendas tuvieron mayores retrasos en las entregas esta semana?',
    filas: [['Tienda 118', '46 min de retraso'], ['Tienda 204', '38 min'], ['Tienda 077', '21 min'],
      ['Promedio de la ruta', '12 min']],
    texto: 'Las tres tiendas comparten la misma franja de llegada; mover media hora la ventana de la 118 descarga la ruta completa.'
  },
  {
    q: '¿Qué rutas presentan mayores tiempos de espera y costos operacionales?',
    filas: [['Ruta Norte', '74 min de espera en muelle'], ['Ruta Occidente', '51 min'],
      ['Ruta Sur', '18 min']],
    texto: 'La espera de la Ruta Norte es el costo escondido más grande de la semana: se concentra entre las 06:00 y las 08:00.'
  },
  {
    q: 'Genera un informe ejecutivo del comportamiento de la cadena de frío del último mes.',
    filas: [['Horas monitoreadas', '720'], ['Horas fuera de rango', '4,3'],
      ['Eventos de puerta abierta', '38'], ['Desviaciones críticas', '2']],
    texto: 'El mes cierra con 0,6 % de horas fuera de rango, concentradas en dos eventos de cargue; el resto del tiempo la cámara sostuvo el punto de ajuste.'
  }
];

function parrafo(clase, etiqueta, texto) {
  const p = document.createElement('p');
  p.className = clase;
  if (etiqueta) {
    const b = document.createElement('b');
    b.textContent = etiqueta;
    p.appendChild(b);
  }
  const t = document.createElement('span');
  t.textContent = texto;
  p.appendChild(t);
  return p;
}

function pintarRespuesta(caja, consulta) {
  caja.textContent = '';
  const cifras = document.createElement('dl');
  cifras.className = 'dato-cifras';
  consulta.filas.forEach((fila) => {
    const dt = document.createElement('dt');
    dt.textContent = fila[0];
    const dd = document.createElement('dd');
    dd.textContent = fila[1];
    cifras.append(dt, dd);
  });
  const explica = document.createElement('p');
  explica.className = 'dato-explica';
  explica.textContent = consulta.texto;
  caja.append(cifras, explica);
}

function crearConsulta() {
  const caja = document.createElement('div');
  caja.className = 'dato-consulta';
  const titulo = document.createElement('h5');
  titulo.textContent = 'Preguntar en lenguaje natural';
  const chips = document.createElement('div');
  chips.className = 'dato-chips';
  const respuesta = document.createElement('div');
  respuesta.className = 'dato-respuesta';
  respuesta.setAttribute('aria-live', 'polite');

  CONSULTAS.forEach((consulta) => {
    const boton = document.createElement('button');
    boton.type = 'button';
    boton.className = 'dato-chip';
    boton.textContent = consulta.q;
    boton.addEventListener('click', () => {
      chips.querySelectorAll('.dato-chip').forEach((o) => o.classList.remove('on'));
      boton.classList.add('on');
      pintarRespuesta(respuesta, consulta);
    });
    chips.appendChild(boton);
  });

  const pie = document.createElement('p');
  pie.className = 'dato-pie';
  pie.textContent = 'Demostración con datos de ejemplo: las cifras las calcula el sistema '
    + 'y el modelo solo las explica. Con la API conectada, la tabla la llena el servicio.';

  caja.append(titulo, chips, respuesta, pie);
  return caja;
}

function crearFicha(contenedor, item) {
  const sitio = document.createElement('p');
  sitio.className = 'dato-sitio';
  sitio.textContent = item.sitio;
  contenedor.appendChild(sitio);
  contenedor.appendChild(parrafo('dato-par', 'Dato', item.dato));
  contenedor.appendChild(parrafo('dato-par', 'Entrega', item.valor));
  contenedor.appendChild(parrafo('dato-par', 'Decisión', item.decision));
  if (item.consulta) contenedor.appendChild(crearConsulta());
}

export function crearCapaDatos(ctx) {
  const { camara, render } = ctx;
  const lienzo = render.domElement;
  const anfitrion = document.getElementById('rec') || document.body;
  const BOTON = document.getElementById('visorDatos');

  const capa = document.createElement('div');
  capa.className = 'dato-capa';
  capa.hidden = true;
  anfitrion.appendChild(capa);

  const panel = document.createElement('section');
  panel.className = 'datos-panel';
  panel.id = 'datosPanel';
  panel.hidden = true;

  const cabecera = document.createElement('header');
  cabecera.className = 'datos-cab';
  const nombre = document.createElement('b');
  nombre.textContent = 'Capa de datos';
  const lema = document.createElement('span');
  lema.textContent = 'Lo que la operación ya registra, leído en su sitio';
  const cerrar = document.createElement('button');
  cerrar.type = 'button';
  cerrar.className = 'datos-x';
  cerrar.setAttribute('aria-label', 'Cerrar la capa de datos');
  cerrar.textContent = '×';
  cabecera.append(nombre, lema, cerrar);
  panel.appendChild(cabecera);

  const cuerpo = document.createElement('div');
  cuerpo.className = 'datos-cuerpo';
  const lead = document.createElement('p');
  lead.className = 'datos-lead';
  lead.textContent = 'La operación sigue siendo de la ingeniería y de sus especialistas: '
    + 'aquí no se reemplaza ningún sistema de control. Encima de lo que ya existe se '
    + 'agrega una capa que lee el registro y lo vuelve decisión.';
  cuerpo.appendChild(lead);

  const botones = new Map();
  const fichas = new Map();
  const pines = new Map();

  ZONAS.forEach((zona) => {
    const titulo = document.createElement('h4');
    titulo.textContent = zona;
    cuerpo.appendChild(titulo);
    INSTRUMENTOS.filter((item) => item.zona === zona).forEach((item) => {
      const boton = document.createElement('button');
      boton.type = 'button';
      boton.className = 'dato-btn';
      boton.setAttribute('aria-expanded', 'false');
      boton.setAttribute('aria-controls', 'dato-' + item.id);
      const marca = document.createElement('i');
      const texto = document.createElement('span');
      texto.textContent = item.titulo;
      boton.append(marca, texto);
      boton.addEventListener('click', () => abrirFicha(item.id, fichas.get(item.id).hidden));

      const ficha = document.createElement('div');
      ficha.className = 'dato-ficha';
      ficha.id = 'dato-' + item.id;
      ficha.hidden = true;
      crearFicha(ficha, item);

      cuerpo.append(boton, ficha);
      botones.set(item.id, boton);
      fichas.set(item.id, ficha);
    });
  });

  panel.appendChild(cuerpo);
  anfitrion.appendChild(panel);

  INSTRUMENTOS.forEach((item) => {
    const pin = document.createElement('button');
    pin.type = 'button';
    pin.className = 'dato-pin';
    pin.setAttribute('aria-label', item.titulo + ' · ' + item.sitio);
    const marca = document.createElement('i');
    const texto = document.createElement('span');
    texto.textContent = item.corto;
    pin.append(marca, texto);
    pin.addEventListener('click', () => { mostrar(true); abrirFicha(item.id, true); });
    capa.appendChild(pin);
    pines.set(item.id, pin);
  });

  function abrirFicha(id, abrir) {
    const ficha = fichas.get(id);
    const boton = botones.get(id);
    if (!ficha || !boton) return;
    ficha.hidden = !abrir;
    boton.setAttribute('aria-expanded', abrir ? 'true' : 'false');
    boton.classList.toggle('abierto', abrir);
    if (abrir) {
      const alto = boton.offsetTop - cuerpo.offsetTop - 10;
      cuerpo.scrollTo({ top: Math.max(0, alto), behavior: 'smooth' });
    }
  }

  function mostrar(valor) {
    const encendida = valor === undefined ? capa.hidden : !!valor;
    capa.hidden = !encendida;
    panel.hidden = !encendida;
    if (BOTON) {
      BOTON.setAttribute('aria-pressed', encendida ? 'true' : 'false');
      BOTON.classList.toggle('activo', encendida);
    }
    if (encendida) ubicar();
  }

  if (BOTON) BOTON.addEventListener('click', () => mostrar());
  cerrar.addEventListener('click', () => mostrar(false));

  /* los pines son DOM sobre el lienzo: se proyecta el anclaje de cada
     instrumento y se coloca; fuera de cuadro se apagan, no se borran */
  const punto = new THREE.Vector3();
  const ancla = new THREE.Vector3();
  function ubicar() {
    if (capa.hidden) return;
    const caja = lienzo.getBoundingClientRect();
    if (!caja.width || !caja.height) return;
    const marco = anfitrion.getBoundingClientRect();
    INSTRUMENTOS.forEach((item) => {
      const pin = pines.get(item.id);
      ancla.set(item.p[0], item.p[1], item.p[2]);
      punto.copy(ancla).project(camara);
      const x = caja.left - marco.left + (punto.x * 0.5 + 0.5) * caja.width;
      const y = caja.top - marco.top + (-punto.y * 0.5 + 0.5) * caja.height;
      const enCuadro = punto.z > -1 && punto.z < 1
        && x > caja.left - marco.left - 30 && x < caja.left - marco.left + caja.width + 30
        && y > caja.top - marco.top - 16 && y < caja.top - marco.top + caja.height + 16;
      /* los instrumentos lejanos se atenúan: en una toma de interior no
         compiten con el que pertenece a la zona que se está mirando */
      const distancia = camara.position.distanceTo(ancla);
      pin.style.opacity = distancia > 85 ? '0.26' : distancia > 45 ? '0.55' : '1';
      pin.classList.toggle('fuera', !enCuadro);
      if (enCuadro) {
        pin.style.transform = 'translate(-50%,-50%) translate('
          + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)';
      }
    });
  }

  function seccion(id) {
    INSTRUMENTOS.forEach((item) => {
      const aqui = item.secciones.indexOf(id) >= 0;
      const boton = botones.get(item.id);
      const pin = pines.get(item.id);
      if (boton) boton.classList.toggle('aqui', aqui);
      if (pin) pin.classList.toggle('aqui', aqui);
    });
  }

  seccion('inicio');

  return { mostrar, seccion, tick: ubicar, abrir: () => mostrar(true) };
}
