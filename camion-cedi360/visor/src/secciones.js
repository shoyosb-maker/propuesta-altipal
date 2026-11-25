/* =========================================================
   CEDI 360 · Recorrido completo de la propuesta
   Una sección por capítulo del deck, de "Inicio" a "Próximos".
   Cada una fija el estado del despiece (fase 0-4) y el encuadre
   de cámara: objetivo, distancia, giro y altura en radianes.
   ========================================================= */

export const SECCIONES = [
  {
    n: '01', id: 'inicio', corto: 'Inicio', titulo: 'Un programa, un responsable',
    lead: 'ALTIPAL no necesita otro proveedor que resuelva el equipo que falla: necesita un responsable del conjunto. CEDI 360 ordena energía, red, seguridad electrónica e instalaciones de los centros de distribución.',
    bullets: [
      'Continuidad verificable, no promesas de disponibilidad',
      'Un solo responsable del conjunto, no doce contratos',
      'Empezar pequeño: diagnóstico por sede'
    ],
    metrica: '85 % del territorio nacional · 24 departamentos',
    fase: 0,
    vista: { obj: [8, 3, 2], dist: 74, giro: 1.05, altura: 0.55 }
  },
  {
    n: '02', id: 'contexto', corto: 'Contexto', titulo: 'Sesenta y cinco años construyendo distribución',
    lead: 'De una tienda en Apartadó en 1960 al 85 % del territorio nacional: ese crecimiento tiene una base física y tecnológica que hoy define el nivel de servicio de cuatro unidades de negocio y de más de cincuenta marcas aliadas.',
    bullets: [
      '47.300 m² de fulfillment · 64.000+ posiciones de almacenamiento',
      'La regla de los doce proveedores: nadie ve el conjunto',
      'La MECA vive en el punto de venta'
    ],
    metrica: 'Fuente: páginas públicas de ALTIPAL',
    fase: 0,
    vista: { obj: [-8, 5, -3], dist: 50, giro: 0.30, altura: 0.28 }
  },
  {
    n: '', id: 'recibo', corto: 'Recibo', titulo: 'La plataforma donde se gana o se pierde el día',
    lead: 'Tres muelles de 3,4 m sobre un andén de 7 × 30 m: por aquí entra el 100 % del surtido y sale el despacho de última milla. Es el primer punto donde se cruzan los cuatro ejes, y el más barato de intervenir.',
    bullets: [
      'Andén a 1,25 m con demarcación, carril peatonal y zona de cargue por muelle',
      'Niveladora de borde, tope de atraque y calzas en el camión',
      'LPR de placas, cámara por muelle, intercomunicador IP y luz de muelle',
      'LED de andén y sensor de presencia sobre el control de acceso'
    ],
    metrica: 'Fase 2 · tres muelles · 7 × 30 m',
    fase: 2,
    vista: { obj: [-2, 1, 2], dist: 49, giro: 0.72, altura: 0.44, der: 0.04 }
  },
  {
    n: '', id: 'acopio', corto: 'Acopio', titulo: 'El centro de acopio que sostiene la promesa',
    lead: 'Cuatro unidades de negocio y más de cincuenta marcas aliadas caben en un solo piso operativo. El modelo levanta la nave completa: 50 × 46 m, seis pasillos de estantería selectiva y cada familia del catálogo con su letrero, su cenefa y su pasillo.',
    bullets: [
      '960 posiciones de pallet en 12 estanterías de cuatro niveles',
      'Doce familias: de bebidas y licores a lubricantes Shell',
      'Recibo al sur, despacho al norte y tres muelles al este',
      'Piso demarcado, alta bahía y 12 m de altura libre'
    ],
    metrica: '47.300 m² de fulfillment · 64.000+ posiciones',
    fase: 0,
    vista: { obj: [-37.2, 4.2, 1], dist: 58, giro: -0.79, altura: 0.33 }
  },
  {
    n: '', id: 'estanterias', corto: 'Estanterías', titulo: 'Cada producto en su caja, cada caja en su repisa',
    lead: 'La estantería selectiva se recorre a pie: cuatro niveles por rack, pallet sobre pallet, la caja marcada con la etiqueta de su familia. Es el mismo surtido que ALTIPAL mueve en punto de venta, ordenado para que el picking no dependa de la memoria de nadie.',
    bullets: [
      'Pallet GMA con carga completa, media o suelta por posición',
      'Etiqueta de familia en la cara del pasillo: lectura a 1,5 m',
      'Pasillos de 4,66 m para montacargas de doble alcance',
      'Sensor IoT por módulo: ocupación y temperatura'
    ],
    metrica: 'Cuatro niveles · 2,41 m entre repisas',
    fase: 0,
    vista: { obj: [-43.5, 2.4, -9], dist: 19, giro: 1.57, altura: 0.05 }
  },
  {
    n: '', id: 'jardin', corto: 'Acceso', titulo: 'El acceso de personal, con jardín alrededor',
    lead: 'La nave se entra por una puerta de personal en la fachada occidental, con jardín alrededor y marquesina. Desde ese patio se llega al pasillo acristalado que sirve al cuarto frío y al pabellón eléctrico: los dos quedan fuera del área de almacenamiento, con acceso propio y a la vista.',
    bullets: [
      'Puerta de personal con marquesina sobre un patio verde de 12 × 30 m',
      'Pasillo acristalado de 4 × 30 m entre el jardín y los pabellones técnicos',
      'Frío y energía fuera de la nave, con acceso independiente y visible',
      'La operación técnica no se cruza con el flujo de recibo y despacho'
    ],
    metrica: 'Acceso peatonal · jardín · pasillo técnico',
    fase: 1,
    vista: { obj: [-62.5, 2.65, 14.0], dist: 22.79, giro: 2.015, altura: 0.239, der: 0.05 }
  },
  {
    n: '', id: 'frio', corto: 'Frío', titulo: 'La cadena de frío, en una cámara monitoreada',
    lead: 'Lácteos y refrigerados salen del bloque ambiente: entran a una cámara exenta con panel sanitario, evaporadores redundantes y monitoreo continuo. Temperatura, humedad, apertura de puerta y fuga de refrigerante quedan registradas para la auditoría de la cadena de frío.',
    bullets: [
      'Cámara de 18 × 14 m con panel sanitario, piso de fácil lavado y zócalo sanitario',
      'Tres evaporadores y dos condensadoras en cubierta, con línea de refrigerante vista',
      'Sondas de temperatura y humedad, contacto de puerta, detector de fuga y registrador',
      'Alarma local con baliza sobre la puerta y traza en el cuarto de monitoreo'
    ],
    metrica: 'Fase 1 · 2 °C a 4 °C sostenidos',
    fase: 1,
    vista: { obj: [-79.0, 3.65, 25.0], dist: 15.65, giro: 3.065, altura: -0.026, der: 0.0, interior: true }
  },
  {
    n: '', id: 'energia', corto: 'Energía', titulo: 'Eje C · La energía que casi nadie mide',
    lead: 'Subestación, tablero general, protecciones y puesta a tierra, en un pabellón exento con reja hacia el pasillo. El diagnóstico de cargas y la termografía se hacen aquí, sobre el equipo que ya está instalado, antes de cotizar una sola intervención.',
    bullets: [
      'Pabellón eléctrico de 18 × 12 m, fuera de la nave y con acceso desde el pasillo',
      'Transformador de 500 kVA, tablero general, transferencia y banco de condensadores',
      'UPS para control, frío y monitoreo, con dado de reserva para un segundo equipo',
      'Iluminación LED industrial en bodega, muelles y patios'
    ],
    metrica: 'Consumo kWh/m² y hallazgos críticos cerrados',
    fase: 1,
    vista: { obj: [-91.0, 2.25, 10.0], dist: 12.14, giro: -0.727, altura: 0.124, der: 0.0, interior: true }
  },
  {
    n: '', id: 'redes', corto: 'Redes', titulo: 'Eje B · Sin red no hay WMS, ni despacho, ni monitoreo',
    lead: 'El cuarto técnico es el punto donde se juntan el CCTV, el control de acceso y el WMS. Aquí se ordena el cableado, la fibra, el switching y el respaldo eléctrico de los puntos críticos, con documentación que se pueda entregar a auditoría.',
    bullets: [
      'Cableado estructurado certificado de cobre y fibra para voz, datos, CCTV y acceso',
      'Fibra entre edificios, muelles y casetas, con enlace redundante',
      'Switching, routing, segmentación y calidad de servicio, con UPS para lo crítico',
      'Cuartos técnicos con racks, ventilación, tierra y control de acceso'
    ],
    metrica: 'Disponibilidad de enlace y puntos certificados',
    fase: 1,
    vista: { obj: [-35.1, 6.6, -23.3], dist: 4.08, giro: 0.653, altura: 0.160, der: 0.0, interior: true }
  },
  {
    n: '', id: 'seguridad', corto: 'Seguridad', titulo: 'Centro de seguridad electrónica sobre el piso de carga',
    lead: 'El cuarto de monitoreo mira la operación desde arriba: muro de video de doce señales, grabación redundante y control de acceso en el paso de personal. Cámaras interiores, de muelle y PTZ exteriores, cada una con su prueba en acta.',
    bullets: [
      '24 cámaras IP: domo interior, bala de muelle y PTZ perimetral',
      'Muro de video 4 × 3 con la señal de doce cámaras en vivo, y dos grabadores con respaldo',
      'Control de acceso con torniquete y lector en cada puerta',
      'Área de cobertura dibujada sobre el piso operativo'
    ],
    metrica: 'Fase 1 · estabilización',
    fase: 1,
    vista: { obj: [-20.8, 7.5, -10.8], dist: 6.9, giro: -0.35, altura: -0.04, der: 0.16, interior: true }
  },
  {
    n: '', id: 'automatizacion', corto: 'Automatización', titulo: 'Ocho puntos de automatización sobre el flujo',
    lead: 'La banda troncal entra por el muelle, sube al sorter y reparte a las salidas de despacho. Cada punto está rotulado en el modelo: lector RFID, sorter, AMR, envolvedora, sensores, acceso, videoanalítica e iluminación.',
    bullets: [
      'Banda troncal de recibo y sorter de once salidas',
      'Cinco AMR circulando por los pasillos y el corredor',
      'Pórticos RFID en los tres muelles de carga',
      'Envolvedora de estiba y sensores de ocupación'
    ],
    metrica: 'Fase 2 · modernización por ejes',
    fase: 2,
    vista: { obj: [-18.0, 2.6, -4.0], dist: 28, giro: 1.30, altura: 0.18, der: 0.14 }
  },
  {
    n: '', id: 'admin', corto: 'Comité', titulo: 'Aquí se decide: el comité del programa',
    lead: 'La propuesta no se sostiene en un contrato sino en una rutina: un comité mensual con acta, un tablero de compromisos y un solo responsable del conjunto. Esta es la mesa donde se revisa sede por sede.',
    bullets: [
      'Un solo responsable del conjunto, no doce contratos',
      'Acta mensual con avance por eje, hallazgos y compromisos',
      'Repositorio único de evidencia: informes, actas y certificados',
      'Sala de juntas con pantalla para el reporte de cada sede'
    ],
    metrica: 'Comité mensual · acta y tablero de compromisos',
    fase: 1,
    vista: { obj: [-31.9, 1.45, -21.0], dist: 4.07, giro: 2.712, altura: 0.049, der: 0.06, interior: true }
  },
  {
    n: '03', id: 'reto', corto: 'El reto', titulo: 'Cinco eslabones, una sola promesa',
    lead: 'La continuidad de un CEDI no se rompe por el equipo más visible, sino por el eslabón que nadie mide. Estos tienen que funcionar al mismo tiempo, todos los días, en 24 departamentos.',
    bullets: [
      'Equipos analógicos o DVR/NVR fuera de soporte, sin repuestos',
      'Retención de grabación insuficiente para una investigación',
      'UPS sin mantenimiento ni pruebas de autonomía real',
      'Cuartos técnicos sin temperatura, orden ni documentación'
    ],
    metrica: 'Lo que se cae no es el camión: es la infraestructura',
    fase: 0,
    vista: { obj: [0, 2.6, 6], dist: 22, giro: 1.05, altura: 0.30 }
  },
  {
    n: '04', id: 'concepto', corto: 'Concepto', titulo: 'Un programa, no una suma de contratos',
    lead: 'Medir antes de invertir, priorizar por riesgo y acompañar después de instalar. Tres ideas que cambian la conversación de «mantenimiento» a «continuidad del negocio».',
    bullets: [
      'Seguridad electrónica: CCTV, acceso y alarmas',
      'Redes y conectividad: LAN, WAN, fibra y Wi-Fi',
      'Energía y respaldo: subestación, UPS y planta',
      'Gestión y analítica: inventario, datos e integración con TI'
    ],
    metrica: 'Medir · priorizar · acompañar',
    fase: 0,
    vista: { obj: [0, 2.8, 6], dist: 26, giro: 0.85, altura: 0.38 }
  },
  {
    n: '05', id: 'capacidades', corto: 'Capacidades', titulo: 'Seis de nuestras siete líneas aplican directo',
    lead: 'No proponemos un servicio inventado para la ocasión: proponemos lo que ya hacemos, aplicado a la operación de ALTIPAL. Cada línea cierra con entregable, prueba y acta.',
    bullets: [
      'CCTV, acceso y monitoreo: cada cámara probada en acta',
      'Redes, fibra y NOC con monitoreo desde centro de integración',
      'Potencia, respaldo y eficiencia con certificación RETIE',
      'Software, datos e IA sobre activos reales'
    ],
    metrica: 'Entregable · prueba · acta',
    fase: 1,
    vista: { obj: [0, 3.4, 6], dist: 26, giro: 1.15, altura: 0.42 }
  },
  {
    n: '06', id: 'ejes', corto: 'Ejes', titulo: 'Cuatro ejes, cuatro documentos de detalle',
    lead: 'Cada eje tiene su propia página con alcance, entregables, criterios de aceptación y exclusiones. Aquí sólo se eligen; el detalle vive en cada documento.',
    bullets: [
      'Eje A · CCTV IP, analítica de video y control de acceso',
      'Eje B · cableado estructurado, fibra y enlaces redundantes',
      'Eje C · cuartos técnicos, UPS y respaldo',
      'Eje D · mantenimiento, muelles y adecuaciones'
    ],
    metrica: 'Cuatro documentos de detalle',
    fase: 2,
    vista: { obj: [0, 3.4, 6], dist: 24, giro: 0.95, altura: 0.40 }
  },
  {
    n: '07', id: 'armador', corto: 'Armador', titulo: 'Armemos el alcance del diagnóstico',
    lead: 'Sin precios: esta herramienta sólo ordena qué sedes, qué ejes y con qué criticidad entrarían a la Fase 0, y qué tamaño tiene el levantamiento. El resultado es una referencia para la reunión, no una cotización.',
    bullets: [
      'Qué sedes entran primero',
      'Qué ejes se activan en cada una',
      'Qué criticidad tiene cada frente'
    ],
    metrica: 'Referencia para la reunión, no cotización',
    fase: 2,
    vista: { obj: [0, 1.8, 8], dist: 24, giro: 1.18, altura: 0.24 }
  },
  {
    n: '08', id: 'matriz', corto: 'Matriz', titulo: 'Qué resuelve cada eje y en qué fase',
    lead: 'La matriz ordena el alcance por eje y por fase. Filtra las fases para ver qué se puede activar temprano y qué depende del diagnóstico.',
    bullets: [
      'Alcance por eje',
      'Activación por fase',
      'Dependencias del diagnóstico'
    ],
    metrica: 'Un cruce: eje × fase',
    fase: 2,
    vista: { obj: [0, 3.0, 6], dist: 27, giro: 1.57, altura: 0.20 }
  },
  {
    n: '09', id: 'fases', corto: 'Fases', titulo: 'Cinco fases, cinco decisiones',
    lead: 'El modelo por fases es un documento aparte: aquí queda el mapa, allá el detalle de cada compuerta, los tiempos y qué se entrega.',
    bullets: [
      'Fase 0 · Diagnóstico e índice de madurez',
      'Fase 1 · Estabilización de lo que puede fallar',
      'Fase 2 · Modernización por ejes',
      'Fase 3 · Inteligencia y datos en vivo',
      'Fase 4 · Acompañamiento con SLA'
    ],
    metrica: 'Ninguna fase compromete la siguiente',
    fase: 3,
    vista: { obj: [0, 5.0, 6], dist: 32, giro: 1.05, altura: 0.48 }
  },
  {
    n: '10', id: 'alineacion', corto: 'Alineación', titulo: 'Cada peso responde a una línea de ALTIPAL',
    lead: 'Esta es la matriz que permite defender el programa internamente: no se trata de mantenimiento, se trata de habilitar la estrategia que ALTIPAL ya declaró.',
    bullets: [
      'IA aplicada: analítica de video y mantenimiento predictivo',
      'Multicloud: el CEDI conectado, documentado y con datos en el borde',
      'Redes modernas y ciberseguridad'
    ],
    metrica: 'Infraestructura como habilitador de la estrategia',
    fase: 4,
    vista: { obj: [0, 4.2, 6], dist: 30, giro: 0.80, altura: 0.45 }
  },
  {
    n: '11', id: 'entrega', corto: 'Entrega', titulo: 'Cómo se trabaja, se reporta y se protege',
    lead: 'Un programa de infraestructura se juzga por dos cosas: lo que entrega y lo que no interrumpe. Aquí están las reglas de gobierno, los niveles de servicio y los riesgos con su mitigación.',
    bullets: [
      'Gobierno: comité técnico mensual y tablero único',
      'Intervención segura: permisos, EPP, bloqueo y etiquetado',
      'Documentación: planos as-built, certificaciones e inventario'
    ],
    metrica: 'Ventanas nocturnas para no afectar el despacho',
    fase: 4,
    vista: { obj: [6, 3.5, 12], dist: 38, giro: 0.70, altura: 0.45 }
  },
  {
    n: '12', id: 'comercial', corto: 'Comercial', titulo: 'Sin precios aquí, con reglas claras',
    lead: 'El esquema comercial completo —modalidades, construcción del precio, fronteras y objeciones— está en su propio documento. Lo esencial:',
    bullets: [
      'Diagnóstico con alcance cerrado; se abona al contrato que se derive',
      'Proyecto por sede y por eje con cantidades medidas en sitio',
      'Acuerdo marco anual con precios unitarios y niveles de servicio',
      'Bolsa de horas para correctivos y solicitudes menores'
    ],
    metrica: 'Primero diagnóstico, después cantidades, después precio',
    fase: 4,
    vista: { obj: [2, 4, 6], dist: 44, giro: 0.90, altura: 0.55 }
  },
  {
    n: '13', id: 'experiencia', corto: 'Experiencia', titulo: 'Ya estamos dentro de la conversación',
    lead: 'FUNDASERINCO ha tenido acercamientos técnicos con ALTIPAL en Ibagué y Montería, relacionados con videovigilancia y grabadores DVR/NVR. El programa propone convertir esos requerimientos puntuales en un modelo de acompañamiento.',
    bullets: [
      'Confianza técnica: videovigilancia en dos ciudades',
      'Visión de conjunto: un inventario único y un plan priorizado',
      'Programa marco replicable para las demás sedes'
    ],
    metrica: 'Ibagué · Montería',
    fase: 4,
    vista: { obj: [0, 2.8, 6], dist: 21, giro: 1.30, altura: 0.26 }
  },
  {
    n: '14', id: 'proximos', corto: 'Próximos', titulo: 'Treinta días para pasar al plan',
    lead: 'El programa no empieza con una obra: empieza con una reunión, dos sedes y un documento. Este es el recorrido propuesto para el primer mes.',
    bullets: [
      'Contacto único por sede y por frente',
      'Planos, inventarios y contratos existentes',
      'Autorización de acceso y ventanas de intervención',
      'Esta propuesta completa, sección por sección'
    ],
    metrica: 'Reunión · dos sedes · un documento',
    fase: 0,
    vista: { obj: [4, 3, 2], dist: 54, giro: 1.40, altura: 0.42 }
  }
];

// la numeración del HUD sale del orden del recorrido
SECCIONES.forEach((s, i) => {
  s.n = String(i + 1).padStart(2, '0');
});
