/* =========================================================
   CEDI 360 · Recorrido 3D de la propuesta
   El modelo arranca en el patio del CEDI y recorre las catorce
   secciones del documento: en cada parada la cámara viaja al
   encuadre de la sección y el despiece adopta su fase.
   ========================================================= */
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { SECCIONES } from './secciones.js';
import { crearPanel } from './panel.js';
import MODELO_B64 from '../modelo.js';

const LIENZO = document.getElementById('visorCanvas');
const HUD = document.getElementById('visorHud');
const BOTON_MENU = document.getElementById('visorMenuBtn');
const RIEL = document.getElementById('visorRail');
const CARGANDO = document.getElementById('visorCargando');
const ESTADO = document.getElementById('visorEstado');
const PROGRESO = document.getElementById('visorProgreso');

let escena, camara, render, controles, mixer, clips = [], modelo;
let tiempoObjetivo = 0, tiempoActual = 0, seccionActual = 0, girando = false;
let menuAbierto = false;
let holo = null;
let cinta = null;
let muro = null;
let pantalla = null;
let panel = null;
let lucesEscena = null;
let camDestino = null, tgtDestino = null;
const FOV_BASE = 38;
// campo horizontal objetivo de las tomas de interior (radianes)
const FOV_INTERIOR = 76 * Math.PI / 180;
const tmpA = new THREE.Vector3();
const tmpB = new THREE.Vector3();

const MENSAJE = 'Arrastra para girar · rueda para acercar · ← → para avanzar';

function b64aBuffer(b64) {
  const limpio = b64.replace(/^data:[^,]+,/, '');
  const texto = atob(limpio);
  const bytes = new Uint8Array(texto.length);
  for (let i = 0; i < texto.length; i += 1) bytes[i] = texto.charCodeAt(i);
  return bytes.buffer;
}

/* el glb viaja comprimido con gzip: se descomprime en el navegador */
async function modeloABuffer() {
  const bytes = new Uint8Array(b64aBuffer(MODELO_B64));
  if (typeof DecompressionStream === 'undefined') return bytes.buffer;
  const flujo = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  return await new Response(flujo).arrayBuffer();
}

/* posición de cámara a partir de un objetivo, distancia, giro y altura */
function posicionCamara(obj, dist, giro, altura) {
  const plano = Math.cos(altura) * dist;
  return new THREE.Vector3(
    obj[0] + Math.cos(giro) * plano,
    obj[1] + Math.sin(altura) * dist,
    obj[2] + Math.sin(giro) * plano
  );
}

function iniciar() {
  const ancho = LIENZO.clientWidth || window.innerWidth;
  const alto = LIENZO.clientHeight || window.innerHeight;

  render = new THREE.WebGLRenderer({ canvas: LIENZO, antialias: true, alpha: false });
  render.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  render.setSize(ancho, alto, false);
  render.toneMapping = THREE.ACESFilmicToneMapping;
  render.toneMappingExposure = 1.05;

  escena = new THREE.Scene();
  escena.background = new THREE.Color(0x0B1116);
  escena.fog = new THREE.Fog(0x0B1116, 90, 260);

  camara = new THREE.PerspectiveCamera(FOV_BASE, ancho / alto, 0.5, 900);
  camara.position.set(46, 40, 46);

  controles = new OrbitControls(camara, render.domElement);
  controles.target.set(2, 4, 4);
  controles.enableDamping = true;
  controles.dampingFactor = 0.07;
  controles.minDistance = 8;
  controles.maxDistance = 180;
  controles.maxPolarAngle = Math.PI * 0.495;
  controles.enablePan = true;
  controles.autoRotateSpeed = 0.55;
  controles.addEventListener('start', () => {
    camDestino = null;
    tgtDestino = null;
  });

  const pmrem = new THREE.PMREMGenerator(render);
  escena.environment = pmrem.fromScene(new RoomEnvironment(), 0.06).texture;

  const hemi = new THREE.HemisphereLight(0xbfd4ea, 0x0a1018, 0.75);
  escena.add(hemi);
  const dir = new THREE.DirectionalLight(0xfff0c8, 1.45);
  dir.position.set(26, 38, 18);
  escena.add(dir);
  const contra = new THREE.DirectionalLight(0x6fa8ff, 0.7);
  contra.position.set(-30, 16, -26);
  escena.add(contra);
  lucesEscena = { hemi, dir, contra };

  const grid = new THREE.GridHelper(220, 110, 0x3d3520, 0x1e2530);
  grid.position.y = 0.002;
  grid.material.opacity = 0.28;
  grid.material.transparent = true;
  escena.add(grid);

  cargarModelo();
  holo = crearHolo();
  cinta = crearCinta();
  enlazarControles();
  enlazarJuego();
  enlazarMenu();
  requestAnimationFrame(bucle);
  window.addEventListener('resize', reajustar);
}

function cargarModelo() {
  const loader = new GLTFLoader();
  modeloABuffer().then((buffer) => loader.parse(buffer, '', (gltf) => {
    modelo = gltf.scene;
    const paleta = {
      // camion, con la paleta de ALTIPAL
      M_Acero: { color: 0x00274B, emissive: 0x0072B2, fuerza: 0.30, opacidad: 1 },
      M_AmbarSuave: { color: 0x07466E, emissive: 0x0072B2, fuerza: 0.26, opacidad: 1 },
      M_Carga: { color: 0x6E8F3F, emissive: 0x9FC55A, fuerza: 0.26, opacidad: 0.95 },
      M_Vidrio: { color: 0x0C2C4A, emissive: 0x0072B2, fuerza: 0.35, opacidad: 0.55 },
      M_Ambar: { color: 0x8A6C08, emissive: 0xFBC710, fuerza: 1.8, opacidad: 1 },
      M_Cian: { color: 0x14424A, emissive: 0x5CDACE, fuerza: 1.0, opacidad: 1 },
      M_MarcaBlanca: { color: 0xFFFFFF, emissive: 0xF2F5F8, fuerza: 0.55, opacidad: 1 },
      M_MarcaAmbar: { color: 0x8A6C08, emissive: 0xFBC710, fuerza: 1.6, opacidad: 1 },
      M_MarcaCian: { color: 0x14424A, emissive: 0x5CDACE, fuerza: 1.0, opacidad: 1 },
      M_MarcaVerde: { color: 0x3E5423, emissive: 0x9FC55A, fuerza: 0.55, opacidad: 1 },
      M_Tinta: { color: 0x0A1018, emissive: 0x14202E, fuerza: 0.15, opacidad: 1 },
      // entorno
      M_Patio: { color: 0x14181D, emissive: 0x1B2330, fuerza: 0.18, opacidad: 1 },
      M_Via: { color: 0x11151A, emissive: 0x18202B, fuerza: 0.18, opacidad: 1 },
      M_Junta: { color: 0x3A3423, emissive: 0x8A7A20, fuerza: 0.22, opacidad: 1 },
      M_Bordillo: { color: 0x6B5206, emissive: 0xC99B0C, fuerza: 0.55, opacidad: 1 },
      M_Eje_Via: { color: 0x8A6C08, emissive: 0xFBC710, fuerza: 0.85, opacidad: 1 },
      M_Anden_Borde: { color: 0x8A6C08, emissive: 0xFBC710, fuerza: 0.9, opacidad: 1 },
      M_Hormigon: { color: 0x2A323B, emissive: 0x374252, fuerza: 0.22, opacidad: 1 },
      M_Puerta_Nave: { color: 0x0A3556, emissive: 0x0072B2, fuerza: 0.28, opacidad: 1 },
      M_Nave: { color: 0x00274B, emissive: 0x0072B2, fuerza: 0.24, opacidad: 1 },
      M_Cubierta: { color: 0x001C36, emissive: 0x00274B, fuerza: 0.20, opacidad: 1 },
      M_Poste: { color: 0x3A4048, emissive: 0x4A525C, fuerza: 0.20, opacidad: 1 },
      M_Luz_Torre: { color: 0x8A7A50, emissive: 0xFFE9A8, fuerza: 2.0, opacidad: 1 },
      M_Flota_Caja: { color: 0xE6EBF0, emissive: 0xDCE4EC, fuerza: 0.30, opacidad: 1 },
      M_Flota_Cab: { color: 0x0072B2, emissive: 0x0072B2, fuerza: 0.35, opacidad: 1 },
      // centro de acopio ALTIPAL (superficies grandes: emision contenida)
      M_Alm_Losa: { color: 0x101418, emissive: 0x1B2330, fuerza: 0.08, opacidad: 1 },
      M_Alm_Muro: { color: 0x00274B, emissive: 0x0072B2, fuerza: 0.16, opacidad: 1 },
      M_Alm_Banda: { color: 0x073C5E, emissive: 0x0072B2, fuerza: 0.16, opacidad: 1 },
      M_Alm_Estructura: { color: 0x1E242B, emissive: 0x2C3641, fuerza: 0.10, opacidad: 1 },
      M_Alm_Rack: { color: 0x0E3554, emissive: 0x0A5080, fuerza: 0.16, opacidad: 1 },
      M_Alm_Madera: { color: 0x3E3222, emissive: 0x4A3A24, fuerza: 0.06, opacidad: 1 },
      M_Alm_Kraft: { color: 0x4A3E2A, emissive: 0x4E3F26, fuerza: 0.06, opacidad: 1 },
      M_Alm_Piso: { color: 0x8A6C08, emissive: 0xFBC710, fuerza: 0.85, opacidad: 1 },
      M_Alm_Luz: { color: 0xFFF2CC, emissive: 0xFFE9A8, fuerza: 1.8, opacidad: 1 },
      M_Alm_Vidrio: { color: 0x0C2C4A, emissive: 0x0072B2, fuerza: 0.32, opacidad: 0.30 },
      M_Alm_Acero: { color: 0x5A646E, emissive: 0x8C97A3, fuerza: 0.14, opacidad: 1 },
      M_Alm_Pantalla: { color: 0x14424A, emissive: 0x5CDACE, fuerza: 1.6, opacidad: 1 },
      M_Alm_PantallaAlt: { color: 0x123A55, emissive: 0x7FB0FF, fuerza: 1.2, opacidad: 1 },
      M_Alm_Cam: { color: 0x11171E, emissive: 0x1B2530, fuerza: 0.18, opacidad: 1 },
      M_Alm_Lente: { color: 0x14424A, emissive: 0x5CDACE, fuerza: 2.4, opacidad: 1 },
      M_Alm_Cobertura: { color: 0x5CDACE, emissive: 0x5CDACE, fuerza: 0.10, opacidad: 0.10 },
      M_Alm_Banda_Trans: { color: 0x1A1F26, emissive: 0x232C36, fuerza: 0.20, opacidad: 1 },
      M_Alm_Ambar: { color: 0x8A6C08, emissive: 0xFBC710, fuerza: 1.4, opacidad: 1 },
      M_Alm_Texto: { color: 0xFFFFFF, emissive: 0xFFFFFF, fuerza: 1.0, opacidad: 1 },
      M_Alm_TextoAzul: { color: 0x9DC6EC, emissive: 0x7FB0FF, fuerza: 1.0, opacidad: 1 },
      M_Alm_Cenefa: { color: 0x0B2439, emissive: 0x0072B2, fuerza: 0.40, opacidad: 1 },
      // demarcacion de plataforma: mismo prefijo para que no se entinte
      M_Alm_PisoVerde: { color: 0x1E6B3A, emissive: 0x2FA84F, fuerza: 0.55, opacidad: 1 },
      M_Alm_PisoBlanco: { color: 0xE8EDF2, emissive: 0xE8EDF2, fuerza: 0.72, opacidad: 1 },
      // cuarto frio: panel sanitario y equipo de refrigeracion
      M_Frio_Caja: { color: 0xE3EDF3, emissive: 0xD9E9F2, fuerza: 0.18, opacidad: 1 },
      M_Frio_Panel: { color: 0xBFD2DC, emissive: 0x8FB6C8, fuerza: 0.18, opacidad: 1 },
      M_Frio_Cielo: { color: 0x9FB4BF, emissive: 0x6F92A2, fuerza: 0.14, opacidad: 1 },
      M_Frio_Piso: { color: 0x1E3A44, emissive: 0x2E5A66, fuerza: 0.30, opacidad: 1 },
      M_Frio_Zocalo: { color: 0x9AA6B2, emissive: 0x8C97A3, fuerza: 0.28, opacidad: 1 },
      M_Frio_Puerta: { color: 0x1E4C63, emissive: 0x0072B2, fuerza: 0.45, opacidad: 1 },
      M_Frio_Unidad: { color: 0xC9D3DA, emissive: 0xDCE4EA, fuerza: 0.32, opacidad: 1 },
      M_Frio_Rejilla: { color: 0x39424D, emissive: 0x2C3A46, fuerza: 0.20, opacidad: 1 },
      M_Frio_Tubo: { color: 0xB08A3C, emissive: 0x8A6C2A, fuerza: 0.18, opacidad: 1 },
      M_Frio_Sensor: { color: 0x11171E, emissive: 0x1B2530, fuerza: 0.22, opacidad: 1 },
      M_Frio_Lente: { color: 0x14424A, emissive: 0x5CDACE, fuerza: 2.2, opacidad: 1 },
      M_Frio_Led: { color: 0x3E5423, emissive: 0x9FC55A, fuerza: 2.0, opacidad: 1 },
      M_Frio_Alarma: { color: 0x8A6C08, emissive: 0xFBC710, fuerza: 1.9, opacidad: 1 },
      // administracion y sala de juntas
      M_Adm_Muro: { color: 0x3A4E60, emissive: 0x587A94, fuerza: 0.52, opacidad: 1 },
      M_Adm_Panel: { color: 0x4A6478, emissive: 0x6E90A8, fuerza: 0.46, opacidad: 1 },
      M_Adm_Vidrio: { color: 0x0C2C4A, emissive: 0x0072B2, fuerza: 0.14, opacidad: 0.10 },
      M_Adm_Piso: { color: 0x36434F, emissive: 0x4E6068, fuerza: 0.40, opacidad: 1 },
      M_Adm_Mesa: { color: 0x6B4A2E, emissive: 0x4A3420, fuerza: 0.35, opacidad: 1 },
      M_Adm_Silla: { color: 0x1B2530, emissive: 0x2A3946, fuerza: 0.32, opacidad: 1 },
      M_Adm_Mueble: { color: 0x25333E, emissive: 0x3A5060, fuerza: 0.34, opacidad: 1 },
      M_Adm_Luz: { color: 0xFFF6DA, emissive: 0xFFEFC2, fuerza: 2.2, opacidad: 1 },
      M_Adm_TV: { color: 0x0A1018, emissive: 0x14202E, fuerza: 0.12, opacidad: 1 },
      M_Adm_TVMarco: { color: 0x11171E, emissive: 0x1B2530, fuerza: 0.16, opacidad: 1 },
      // subestacion y tableros
      M_Ene_Cabina: { color: 0x5A646E, emissive: 0x6C7885, fuerza: 0.22, opacidad: 1 },
      M_Ene_Tablero: { color: 0x39424D, emissive: 0x46525E, fuerza: 0.22, opacidad: 1 },
      M_Ene_Breaker: { color: 0x11171E, emissive: 0x1B2530, fuerza: 0.18, opacidad: 1 },
      M_Ene_UPS: { color: 0x1E4C63, emissive: 0x0072B2, fuerza: 0.35, opacidad: 1 },
      M_Ene_Aviso: { color: 0x8A6C08, emissive: 0xFBC710, fuerza: 1.7, opacidad: 1 },

      // plataforma, pasillo tecnico y jardin de acceso
      M_Pas_Losa: { color: 0x6E7A86, emissive: 0x84909C, fuerza: 0.24, opacidad: 1 },
      M_Pas_Luz: { color: 0xFFF6DA, emissive: 0xFFEFC2, fuerza: 2.2, opacidad: 1 },
      M_Jar_Pasto: { color: 0x1E6B3A, emissive: 0x2FA84F, fuerza: 0.60, opacidad: 1 },
      M_Jar_Grava: { color: 0x9A9384, emissive: 0x8A8476, fuerza: 0.35, opacidad: 1 },
      M_Jar_Tronco: { color: 0x3E3222, emissive: 0x4A3A24, fuerza: 0.20, opacidad: 1 },
      M_Jar_Follaje: { color: 0x2E7A48, emissive: 0x3E8F58, fuerza: 0.65, opacidad: 1 },
      M_Jar_Seto: { color: 0x33704A, emissive: 0x43855C, fuerza: 0.60, opacidad: 1 },
      M_Jar_Madera: { color: 0x6B4A2E, emissive: 0x4A3420, fuerza: 0.35, opacidad: 1 },

      // simulacion: portones, carga, AMR y balizas del panel de operacion
      M_Sim_Puerta: { color: 0xB8C4CC, emissive: 0x8FA2AE, fuerza: 0.32, opacidad: 1 },
      M_Sim_PuertaFrio: { color: 0x1E4C63, emissive: 0x0072B2, fuerza: 0.38, opacidad: 1 },
      M_Sim_Caja: { color: 0x4A3E2A, emissive: 0x4E3F26, fuerza: 0.10, opacidad: 1 },
      M_Sim_CajaClara: { color: 0xBFCBD4, emissive: 0xA8B8C4, fuerza: 0.22, opacidad: 1 },
      M_Sim_Palet: { color: 0x3E3222, emissive: 0x4A3A24, fuerza: 0.10, opacidad: 1 },
      M_Sim_AMR: { color: 0x11171E, emissive: 0x1B2530, fuerza: 0.22, opacidad: 1 },
      M_Sim_Led: { color: 0x14424A, emissive: 0x5CDACE, fuerza: 2.4, opacidad: 1 },
      M_Sim_Alarma: { color: 0x3A0F0C, emissive: 0xD2463C, fuerza: 1.8, opacidad: 1 },
      M_Sim_Acero: { color: 0x5A646E, emissive: 0x8C97A3, fuerza: 0.18, opacidad: 1 },
      // sala tecnica de redes
      M_Red_Rack: { color: 0x11171E, emissive: 0x1B2530, fuerza: 0.20, opacidad: 1 },
      M_Red_Patch: { color: 0xC9A227, emissive: 0xA8871E, fuerza: 0.35, opacidad: 1 },
      M_Red_Switch: { color: 0x1E4C63, emissive: 0x0072B2, fuerza: 0.40, opacidad: 1 },
      M_Red_Led: { color: 0x14424A, emissive: 0x5CDACE, fuerza: 2.4, opacidad: 1 },
      M_Red_UPS: { color: 0x2A3B4A, emissive: 0x3C5468, fuerza: 0.26, opacidad: 1 },
      // plataforma de descargue: vehiculos y senalizacion de muelle
      M_Mue_Caja: { color: 0xDDE4EA, emissive: 0xDCE4EC, fuerza: 0.24, opacidad: 1 },
      M_Mue_Chasis: { color: 0x14181D, emissive: 0x1B2330, fuerza: 0.18, opacidad: 1 },
      M_Mue_Llanta: { color: 0x0A0E13, emissive: 0x121820, fuerza: 0.10, opacidad: 1 },
      M_Mue_Panel: { color: 0x0B2439, emissive: 0x0072B2, fuerza: 0.35, opacidad: 1 },
      M_Mue_Rojo: { color: 0x3A0F0C, emissive: 0xD2463C, fuerza: 1.6, opacidad: 1 },
      M_Mue_VerdeLuz: { color: 0x2C5A18, emissive: 0x8FE04A, fuerza: 2.6, opacidad: 1 },
      M_Mue_Naranja: { color: 0x7A3E0C, emissive: 0xF08A24, fuerza: 1.0, opacidad: 1 },
      // vehiculos importados de Sketchfab: la textura manda como color y emision
      M_Mue_Truck: { color: 0xFFFFFF, emissive: 0xFFFFFF, fuerza: 0.22, opacidad: 1 },
      M_Mue_Fork: { color: 0x5A646E, emissive: 0x8C97A3, fuerza: 0.35, opacidad: 1 },
      // cabina del tractor (MAN TGX): el glb la exporta con sufijo .001
      Material: { color: 0x00274B, emissive: 0x0072B2, fuerza: 0.30, opacidad: 1 },
      Back_Trailor: { color: 0x07466E, emissive: 0x0072B2, fuerza: 0.26, opacidad: 1 },
      dark: { color: 0x12171D, emissive: 0x1B2530, fuerza: 0.22, opacidad: 1 },
      Darker_Most: { color: 0x0D1117, emissive: 0x161E28, fuerza: 0.22, opacidad: 1 },
      Grey: { color: 0x4A525C, emissive: 0x4A525C, fuerza: 0.26, opacidad: 1 },
      Metalic: { color: 0x8C97A3, emissive: 0x8C97A3, fuerza: 0.30, opacidad: 1 },
      Glass: { color: 0x0C2C4A, emissive: 0x0072B2, fuerza: 0.32, opacidad: 0.55 },
      Tyre_sidewalls: { color: 0x0A0A0C, emissive: 0x0A0A0C, fuerza: 0.10, opacidad: 1 },
      Tyre_tread: { color: 0x080809, emissive: 0x080809, fuerza: 0.10, opacidad: 1 },
      Rims: { color: 0x8C97A3, emissive: 0x8C97A3, fuerza: 0.32, opacidad: 1 },
      Hubs: { color: 0x5A636D, emissive: 0x5A636D, fuerza: 0.26, opacidad: 1 },
      White_Light: { color: 0xFFFFFF, emissive: 0xF2F5F8, fuerza: 1.2, opacidad: 1 },
      Yellow_Loght_Black: { color: 0x8A6C08, emissive: 0xFBC710, fuerza: 1.6, opacidad: 1 }
    };

    // furgonetas de reparto: se pintan por prefijo M_Fur_
    const furgoneta = {
      carroceria: { color: 0xE8EEF5, emissive: 0xFFFFFF, fuerza: 0.40, opacidad: 1 },
      vidrio: { color: 0x0C2C4A, emissive: 0x0072B2, fuerza: 0.32, opacidad: 0.55 },
      llanta: { color: 0x0A1018, emissive: 0x14202E, fuerza: 0.15, opacidad: 1 },
      moldura: { color: 0x2B313A, emissive: 0x3A4652, fuerza: 0.25, opacidad: 1 },
      rin: { color: 0x8C97A3, emissive: 0x9AA6B2, fuerza: 0.35, opacidad: 1 }
    };

    // etiquetas y cenefas por familia de producto
    const familia = {
      BEBIDAS: 0x52A6E0,
      CERVEZAS: 0xC98A2E,
      ALIMENTOS: 0xE0BC5E,
      LACTEOS: 0xE4EAF0,
      SNACKS: 0xD96A45,
      ASEO: 0x4FC0C0,
      CUIDADO: 0x9FC55A,
      SALUD: 0x6FA6D6,
      TABACO: 0xA88A62,
      LUBRICANTES: 0xF2C21A,
      ILUMINACION: 0x7A93C8,
      EMPAQUES: 0xA9AEB5
    };

    modelo.traverse((obj) => {
      if (!obj.isMesh) return;
      const nombre = (obj.material && obj.material.name) || '';
      const material = obj.material;
      if (!material) return;

      // cenefas y etiquetas de familia: color pleno, sin aristas.
      // las cenefas son rotulos: una sola cara, o la copia de atras se ve en
      // espejo encima y no se lee; las etiquetas de caja si van a dos caras
      if (nombre.indexOf('M_Alm_Fam_') === 0 || nombre.indexOf('M_Alm_Lab_') === 0) {
        const clave = nombre.split('_')[3].split('.')[0];
        material.side = nombre.indexOf('M_Alm_Fam_') === 0
          ? THREE.FrontSide
          : THREE.DoubleSide;
        material.color.setHex(0x081220);
        material.emissive.setHex(familia[clave] || 0xDCE9FF);
        material.emissiveIntensity = 1.1;
        material.metalness = 0;
        material.roughness = 0.8;
        return;
      }

      // rotulos de texto: una sola cara (hay una copia por lado del letrero)
      if (nombre.indexOf('M_Alm_Texto') === 0) {
        material.side = THREE.FrontSide;
        material.metalness = 0;
        material.roughness = 0.6;
        return;
      }

      // modelos de Sketchfab: la textura del glb se usa tambien de emision,
      // o el vehiculo queda como una silueta negra entre tanto material emisivo
      if (nombre.indexOf('M_Mue_Truck') === 0 || nombre.indexOf('M_Mue_Fork') === 0) {
        if (material.map) {
          material.emissiveMap = material.map;
          material.needsUpdate = true;
        }
      }

      // areas de cobertura de CCTV: velo aditivo, sin escribir profundidad
      if (nombre.indexOf('M_Alm_Cobertura') === 0) {
        material.side = THREE.DoubleSide;
        material.transparent = true;
        material.opacity = 0.10;
        material.depthWrite = false;
        material.blending = THREE.AdditiveBlending;
        material.color.setHex(0x5CDACE);
        material.emissive.setHex(0x5CDACE);
        material.emissiveIntensity = 0.6;
        return;
      }

      // los logos son texturas con alfa: se recortan, no se repintan
      if (nombre.indexOf('M_Logo') === 0) {
        material.side = THREE.DoubleSide;
        material.transparent = true;
        material.alphaTest = 0.4;
        material.depthWrite = true;
        material.metalness = 0;
        material.roughness = 0.7;
        material.color.setHex(0xFFFFFF);
        material.emissive.setHex(0xFFFFFF);
        material.emissiveIntensity = 0.45;
        obj.renderOrder = 1;
        return;
      }

      const base = nombre.replace(/\.\d+$/, '');
      const p = paleta[nombre] || paleta[base]
        || (nombre.indexOf('M_Fur_') === 0
          ? furgoneta[nombre.slice(6).split('.')[0]]
          : null)
        || { color: 0x0E1620, emissive: 0x1B2A38, fuerza: 0.25, opacidad: 1 };
      material.side = THREE.DoubleSide;
      material.envMapIntensity = 0.35;
      material.metalness = 0.18;
      material.roughness = 0.78;
      material.color.setHex(p.color);
      material.emissive.setHex(p.emissive);
      material.emissiveIntensity = p.fuerza;
      if (p.opacidad < 1) {
        material.transparent = true;
        material.opacity = p.opacidad;
      }
      // las furgonetas y los montacargas son piezas de fondo: sin aristas
      if (nombre.indexOf('M_Fur_') === 0 || nombre.indexOf('M_Mue_Fork') === 0) return;
      // del centro de acopio solo se entinta la estructura: las cajas y la
      // carga son miles de aristas y saturan la lectura a escala de nave
      const acopio = nombre.indexOf('M_Alm_') === 0;
      if (acopio
        && nombre.indexOf('M_Alm_Rack') !== 0
        && nombre.indexOf('M_Alm_Estructura') !== 0
        && nombre.indexOf('M_Alm_Muro') !== 0) return;
      const aristas = new THREE.LineSegments(
        new THREE.EdgesGeometry(obj.geometry, 28),
        new THREE.LineBasicMaterial({
          color: 0xF2C21A, transparent: true,
          opacity: acopio ? 0.20 : 0.42, depthWrite: false
        })
      );
      aristas.renderOrder = 2;
      obj.add(aristas);
    });
    escena.add(modelo);
    muro = crearMuroVideo();
    pantalla = crearPantallaAdmin();
    panel = crearPanel({ escena, modelo, luces: lucesEscena, muro });

    mixer = new THREE.AnimationMixer(modelo);
    clips = gltf.animations || [];
    clips.forEach((clip) => {
      const accion = mixer.clipAction(clip);
      accion.play();
      accion.setEffectiveWeight(1);
    });

    if (CARGANDO) CARGANDO.classList.add('oculto');
    if (ESTADO) ESTADO.textContent = MENSAJE;

    ir(seccionInicial(), true);
    window.addEventListener('hashchange', () => {
      const i = seccionDelHash();
      if (i !== null) ir(i);
    });
  }, (error) => {
    console.error(error);
    if (ESTADO) ESTADO.textContent = 'No se pudo cargar el modelo';
  })).catch((error) => {
    console.error(error);
    if (ESTADO) ESTADO.textContent = 'No se pudo descomprimir el modelo';
  });
}

/* ---------- capa de datos sobre el techo (fase 3) ----------
   El holograma acompania al camion: ubicar_camion.py lo corre a x = 8, el
   mismo valor de HOLO_CENTRO_X (en three.js la x de Blender no cambia). */
const CIAN = 0x7FB0FF;
const HOLO_ALTO = 9.3;
const HOLO_CENTRO_X = 8.0;
const HOLO_CENTRO_Z = 8.9;
const HOLO_LARGO = 13.0;
const HOLO_ANCHO = 5.2;

function rotulo(texto, anchoMundo) {
  const ancho = 512;
  const alto = 96;
  const lienzo = document.createElement('canvas');
  lienzo.width = ancho * 2;
  lienzo.height = alto * 2;
  const ctx = lienzo.getContext('2d');
  ctx.scale(2, 2);
  ctx.fillStyle = 'rgba(8,17,28,0.8)';
  ctx.fillRect(0, 0, ancho, alto);
  ctx.strokeStyle = 'rgba(127,176,255,0.9)';
  ctx.lineWidth = 3;
  ctx.strokeRect(1.5, 1.5, ancho - 3, alto - 3);
  ctx.fillStyle = '#DCE9FF';
  ctx.font = '600 30px ui-monospace, SFMono-Regular, Consolas, monospace';
  ctx.textBaseline = 'middle';
  ctx.fillText(texto, 24, alto / 2 + 1);
  const tex = new THREE.CanvasTexture(lienzo);
  tex.anisotropy = 4;
  const spr = new THREE.Sprite(new THREE.SpriteMaterial({
    map: tex, transparent: true, depthWrite: false, depthTest: false,
    blending: THREE.AdditiveBlending, opacity: 0
  }));
  spr.scale.set(anchoMundo, anchoMundo * (alto / ancho), 1);
  return spr;
}

function crearHolo() {
  const grupo = new THREE.Group();
  const materiales = [];

  const velo = new THREE.Mesh(
    new THREE.PlaneGeometry(HOLO_ANCHO, HOLO_LARGO, 1, 1),
    new THREE.MeshBasicMaterial({
      color: CIAN, transparent: true, opacity: 0, side: THREE.DoubleSide,
      depthWrite: false, blending: THREE.AdditiveBlending
    })
  );
  velo.rotation.x = -Math.PI / 2;
  velo.position.set(0, HOLO_ALTO, HOLO_CENTRO_Z);
  grupo.add(velo);
  materiales.push({ mat: velo.material, tope: 0.07 });

  const rejilla = new THREE.GridHelper(HOLO_LARGO, 13, CIAN, CIAN);
  rejilla.position.set(0, HOLO_ALTO + 0.02, HOLO_CENTRO_Z);
  rejilla.material.transparent = true;
  rejilla.material.opacity = 0;
  rejilla.material.depthWrite = false;
  grupo.add(rejilla);
  materiales.push({ mat: rejilla.material, tope: 0.32 });

  [[-1.25, 0.4], [1.25, 0.4], [-1.25, 11.6], [1.25, 11.6]].forEach(([x, z]) => {
    const geo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(x, 2.55, z),
      new THREE.Vector3(x, HOLO_ALTO, z)
    ]);
    const linea = new THREE.Line(geo, new THREE.LineDashedMaterial({
      color: CIAN, dashSize: 0.32, gapSize: 0.26, transparent: true,
      opacity: 0, depthWrite: false
    }));
    linea.computeLineDistances();
    grupo.add(linea);
    materiales.push({ mat: linea.material, tope: 0.7 });
  });

  [
    ['42 NODOS DE SENSOR', -4.7, 10.2, 1.2],
    ['128 PRECINTOS ACTIVOS', 4.7, 10.2, 6.2],
    ['TERMICO BPM / INVIMA', 4.7, 8.5, 10.6],
    ['WMS · TMS · IA DE RUTA', -4.7, 8.5, 5.8]
  ].forEach(([t, x, y, z]) => {
    const spr = rotulo(t, 4.6);
    spr.position.set(x, y, z);
    grupo.add(spr);
    materiales.push({ mat: spr.material, tope: 1, sprite: true });
  });

  grupo.visible = false;
  grupo.position.x = HOLO_CENTRO_X;
  escena.add(grupo);
  return { grupo, materiales };
}

/* ---------- cinta transportadora en marcha (fase 2) ----------
   El modelo exporta la banda, el sorter y los AMR fundidos en una sola malla,
   asi que el movimiento se resuelve con piezas nuevas en three.js: paquetes
   que recorren la banda troncal y bandejas que salen por el sorter. Aparecen
   con la capa de automatizacion (misma fase que los puntos A1-A8). */
const CINTA_TRONCAL = { x: -16.6, y: 2.28, z0: 25.0, z1: -8.4, n: 9, paso: 0.055 };
const CINTA_SORTER = { y: 2.44, z: -11.95, x0: -46.4, x1: -21.2, n: 6, paso: 0.07 };

function crearCinta() {
  const grupo = new THREE.Group();
  const material = new THREE.MeshStandardMaterial({
    color: 0x4A3E2A, emissive: 0x9FC55A, emissiveIntensity: 0.30,
    roughness: 0.82, metalness: 0.05
  });
  const caja = new THREE.BoxGeometry(0.52, 0.42, 0.50);
  const bandeja = new THREE.BoxGeometry(0.62, 0.10, 0.84);
  const piezas = [];
  for (let i = 0; i < CINTA_TRONCAL.n; i++) {
    const m = new THREE.Mesh(caja, material);
    m.position.set(CINTA_TRONCAL.x, CINTA_TRONCAL.y, CINTA_TRONCAL.z0);
    grupo.add(m);
    piezas.push({ obj: m, t: i / CINTA_TRONCAL.n, tipo: 0 });
  }
  for (let i = 0; i < CINTA_SORTER.n; i++) {
    const m = new THREE.Mesh(bandeja, material);
    m.position.set(CINTA_SORTER.x0, CINTA_SORTER.y, CINTA_SORTER.z);
    grupo.add(m);
    piezas.push({ obj: m, t: i / CINTA_SORTER.n, tipo: 1 });
  }
  grupo.visible = false;
  escena.add(grupo);
  return { grupo, piezas };
}

function animarCinta(pAuto, dt) {
  if (!cinta) return;
  cinta.grupo.visible = pAuto > 0.05;
  if (!cinta.grupo.visible) return;
  cinta.piezas.forEach((p) => {
    const paso = p.tipo === 0 ? CINTA_TRONCAL.paso : CINTA_SORTER.paso;
    p.t = (p.t + dt * paso) % 1;
    if (p.tipo === 0) {
      const c = CINTA_TRONCAL;
      p.obj.position.z = c.z0 + (c.z1 - c.z0) * p.t;
    } else {
      const s = CINTA_SORTER;
      p.obj.position.x = s.x0 + (s.x1 - s.x0) * p.t;
    }
  });
}

/* ---------- muro de video del centro de seguridad (fase 1) ----------
   Cada pantalla del muro (CEDI_VideoWall_i_j) muestra la senal de una camara
   virtual puesta en su sitio del modelo. Se rinde una camara por vez a una
   textura pequena: el muro se refresca como un CCTV real y cuesta un solo
   render extra cada dos cuadros. La cortinilla con el nombre y la hora va
   como hija de la camara, en la capa 1, para que quede "quemada" en la senal
   y no aparezca nunca en la vista principal. */
const CCTV = [
  { nombre: 'MUELLE 01', grupo: 'muelles', pos: [-10.2, 4.5, 19.0], tgt: [-2.5, 1.6, 14.0], fov: 60 },
  { nombre: 'MUELLE 02', grupo: 'muelles', pos: [-10.2, 4.5, 11.0], tgt: [-2.5, 1.6, 5.0], fov: 60 },
  { nombre: 'MUELLE 03', grupo: 'muelles', pos: [-10.2, 4.5, 3.0], tgt: [-2.5, 1.6, -2.0], fov: 60 },
  { nombre: 'PASILLO 1', grupo: 'interiores', pos: [-49.3, 10.7, 11.0], tgt: [-49.3, 2.4, -14.0], fov: 62 },
  { nombre: 'PASILLO 3', grupo: 'interiores', pos: [-37.7, 10.7, 11.0], tgt: [-37.7, 2.4, -14.0], fov: 62 },
  { nombre: 'CORREDOR', grupo: 'interiores', pos: [-23.0, 8.8, 20.3], tgt: [-50.0, 2.4, 20.3], fov: 58 },
  { nombre: 'BANDA TRONCAL', grupo: 'interiores', pos: [-16.6, 8.0, 24.0], tgt: [-16.6, 2.0, -3.0], fov: 62 },
  { nombre: 'SORTER', grupo: 'interiores', pos: [-43.0, 9.6, 18.0], tgt: [-29.0, 1.8, 11.9], fov: 58 },
  { nombre: 'CONTROL DE ACCESO', grupo: 'interiores', pos: [-16.6, 2.6, 25.0], tgt: [-20.4, 1.4, 21.6], fov: 62 },
  { nombre: 'SALA DE MONITOREO', grupo: 'interiores', pos: [-13.9, 7.5, -8.1], tgt: [-19.6, 5.6, -12.6], fov: 60 },
  { nombre: 'PATIO NORTE', grupo: 'perimetro', pos: [12.0, 7.6, 20.0], tgt: [-2.0, 2.0, 10.0], fov: 55 },
  { nombre: 'PATIO SUR', grupo: 'perimetro', pos: [13.0, 7.4, -9.0], tgt: [-2.0, 2.0, 1.0], fov: 55 }
];

const frustula = new THREE.Frustum();
const matrizVista = new THREE.Matrix4();
const cajaMuro = new THREE.Box3();
const esferaMuro = new THREE.Sphere(new THREE.Vector3(), 3.0);

function crearMuroVideo() {
  const pantallas = [];
  modelo.traverse((obj) => {
    if (obj.isMesh && obj.name.indexOf('CEDI_VideoWall') === 0) pantallas.push(obj);
  });
  if (!pantallas.length) return null;
  pantallas.sort((a, b) => (a.name < b.name ? -1 : 1));

  const senales = CCTV.map((sitio) => {
    const lienzo = document.createElement('canvas');
    lienzo.width = 480;
    lienzo.height = 60;
    const ctx = lienzo.getContext('2d');
    const tex = new THREE.CanvasTexture(lienzo);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.minFilter = THREE.LinearFilter;
    const osd = new THREE.Mesh(
      new THREE.PlaneGeometry(1.62, 0.2025),
      new THREE.MeshBasicMaterial({
        map: tex, transparent: true, toneMapped: false,
        depthTest: false, depthWrite: false
      })
    );
    osd.position.set(0, -0.41, -1.0);
    osd.layers.set(1);
    osd.renderOrder = 999;

    const cam = new THREE.PerspectiveCamera(sitio.fov, 16 / 9, 0.25, 300);
    cam.position.fromArray(sitio.pos);
    cam.lookAt(tmpA.fromArray(sitio.tgt));
    cam.layers.enable(1);
    cam.add(osd);
    escena.add(cam);

    const rt = new THREE.WebGLRenderTarget(384, 216, { colorSpace: THREE.SRGBColorSpace });
    const mat = new THREE.MeshBasicMaterial({
      map: rt.texture, toneMapped: false, color: new THREE.Color(1.22, 1.22, 1.22)
    });
    return { nombre: sitio.nombre, cam, ctx, tex, rt, mat };
  });

  // las pantallas van en el orden del muro: arriba a la izquierda primero
  pantallas.forEach((pantalla, i) => {
    const senal = senales[i % senales.length];
    senal.pantalla = pantalla;
    pantalla.material = senal.mat;
  });

  const estado = {
    senales, pantallas, siguiente: 0, cuadro: 0, espera: 0, enCuadro: false,
    activa: senales.map(() => true),
    sinSenal: crearSinSenal()
  };
  estado.alternar = (indices, activo) => {
    indices.forEach((i) => {
      const senal = estado.senales[i];
      if (!senal) return;
      estado.activa[i] = activo;
      if (senal.pantalla) senal.pantalla.material = activo ? senal.mat : estado.sinSenal;
    });
  };
  estado.todasActivas = () => estado.activa.every(Boolean);
  estado.activas = () => estado.activa.filter(Boolean).length;
  return estado;
}

/* cartel de "sin senal" que reemplaza la imagen de una camara apagada */
function crearSinSenal() {
  const lienzo = document.createElement('canvas');
  lienzo.width = 384;
  lienzo.height = 216;
  const ctx = lienzo.getContext('2d');
  ctx.fillStyle = '#08121A';
  ctx.fillRect(0, 0, 384, 216);
  ctx.strokeStyle = '#F2C21A';
  ctx.lineWidth = 2;
  ctx.strokeRect(6, 6, 372, 204);
  ctx.fillStyle = '#F2C21A';
  ctx.font = 'bold 34px Consolas, monospace';
  ctx.textAlign = 'center';
  ctx.fillText('SIN SEÑAL', 192, 104);
  ctx.fillStyle = '#69727D';
  ctx.font = '15px Consolas, monospace';
  ctx.fillText('CAMARA FUERA DE SERVICIO', 192, 140);
  ctx.fillText('PANEL DE OPERACION', 192, 164);
  const tex = new THREE.CanvasTexture(lienzo);
  tex.colorSpace = THREE.SRGBColorSpace;
  return new THREE.MeshBasicMaterial({ map: tex, toneMapped: false });
}

/* ---------- pantalla de la sala de juntas ----------
   El panel ADM_Pantalla sale del glb con su capa UV; aqui se le pinta encima
   el tablero del comite, que cambia con la fase de la seccion activa. */
const FASES_COMITE = ['Diagnóstico', 'Estabilización', 'Modernización',
  'Inteligencia', 'Acompañamiento'];

function crearPantallaAdmin() {
  const obj = modelo.getObjectByName('ADM_Pantalla');
  if (!obj) return null;
  const lienzo = document.createElement('canvas');
  lienzo.width = 1024;
  lienzo.height = 576;
  const ctx = lienzo.getContext('2d');
  const tex = new THREE.CanvasTexture(lienzo);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  obj.material = new THREE.MeshBasicMaterial({ map: tex, toneMapped: false });

  const pintar = (fase) => {
    const f = Math.max(0, Math.min(4, Math.round(fase || 0)));
    const grad = ctx.createLinearGradient(0, 0, 1024, 576);
    grad.addColorStop(0, '#061019');
    grad.addColorStop(1, '#0B2740');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 1024, 576);
    ctx.strokeStyle = 'rgba(92,218,206,0.10)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= 1024; x += 64) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 576); ctx.stroke();
    }
    for (let y = 0; y <= 576; y += 64) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(1024, y); ctx.stroke();
    }
    ctx.fillStyle = '#FBC710';
    ctx.fillRect(56, 54, 8, 66);
    ctx.fillStyle = '#E8EDF2';
    ctx.font = '600 40px Consolas, monospace';
    ctx.fillText('Comité del programa', 88, 94);
    ctx.fillStyle = '#5CDACE';
    ctx.font = '500 22px Consolas, monospace';
    ctx.fillText('CEDI 360 · seguimiento por sede', 88, 130);
    ctx.fillStyle = '#9FC55A';
    ctx.font = '600 21px Consolas, monospace';
    ctx.textAlign = 'right';
    ctx.fillText('FASE ' + f + ' · ' + FASES_COMITE[f].toUpperCase(), 968, 94);
    ctx.textAlign = 'left';
    ['1. Avance por eje', '2. Hallazgos y compromisos', '3. Evidencia y actas']
      .forEach((t, i) => {
        ctx.fillStyle = 'rgba(127,176,255,0.14)';
        ctx.fillRect(88, 206 + i * 84, 848, 62);
        ctx.fillStyle = '#DCE9FF';
        ctx.font = '400 26px Consolas, monospace';
        ctx.fillText(t, 112, 246 + i * 84);
      });
    ctx.fillStyle = '#69727D';
    ctx.font = '400 18px Consolas, monospace';
    ctx.fillText('FUNDASERINCO · Ingeniería, tecnología e IA', 88, 528);
    tex.needsUpdate = true;
  };
  pintar(0);
  return { pintar };
}

function pintarSenal(senal) {  const { ctx, tex } = senal;
  const ancho = 480;
  const alto = 60;
  ctx.clearRect(0, 0, ancho, alto);
  ctx.fillStyle = 'rgba(6, 12, 16, 0.6)';
  ctx.fillRect(0, alto - 27, ancho, 27);
  ctx.font = 'bold 19px Consolas, monospace';
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';
  ctx.fillStyle = '#E8EDF2';
  ctx.fillText(senal.nombre, 12, alto - 13);
  const ahora = new Date();
  const hora = [ahora.getHours(), ahora.getMinutes(), ahora.getSeconds()]
    .map((n) => String(n).padStart(2, '0')).join(':');
  ctx.textAlign = 'right';
  ctx.font = 'bold 17px Consolas, monospace';
  ctx.fillStyle = '#9FC55A';
  ctx.fillText(hora, ancho - 34, alto - 13);
  ctx.fillStyle = '#E4572E';
  ctx.beginPath();
  ctx.arc(ancho - 20, alto - 12, 5, 0, Math.PI * 2);
  ctx.fill();
  ctx.textAlign = 'left';
  tex.needsUpdate = true;
}

function animarMuroVideo(p5, dt) {
  if (!muro) return;
  if (p5 <= 0.9) return;

  // fuera de cuadro no se refresca nada: el muro solo consume cuando se ve
  muro.espera -= dt;
  if (muro.espera <= 0) {
    muro.espera = 0.4;
    // la geometria va horneada: el centro sale de la caja, no de la posicion
    cajaMuro.setFromObject(muro.pantallas[Math.floor(muro.pantallas.length / 2)]);
    cajaMuro.getCenter(esferaMuro.center);
    camara.updateMatrixWorld();
    matrizVista.copy(camara.matrixWorld).invert();
    frustula.setFromProjectionMatrix(
      matrizVista.premultiply(camara.projectionMatrix)
    );
    muro.enCuadro = frustula.intersectsSphere(esferaMuro);
  }
  if (!muro.enCuadro) return;

  muro.cuadro++;
  // se salta las camaras apagadas: su pantalla queda con el cartel de sin senal
  const total = muro.senales.length;
  let senal = null;
  let intento = 0;
  while (intento < total) {
    const i = muro.siguiente % total;
    muro.siguiente = (i + 1) % total;
    intento++;
    if (muro.activa[i]) { senal = muro.senales[i]; break; }
  }
  if (!senal) return;

  pintarSenal(senal);
  // el holograma de la propuesta no sale en un CCTV de planta y la pantalla
  // que se esta rindiendo no puede estar en su propio cuadro (bucle de textura)
  const holoVisible = holo && holo.grupo.visible;
  if (holoVisible) holo.grupo.visible = false;
  if (senal.pantalla) senal.pantalla.visible = false;
  render.setRenderTarget(senal.rt);
  render.render(escena, senal.cam);
  render.setRenderTarget(null);
  if (senal.pantalla) senal.pantalla.visible = true;
  if (holoVisible) holo.grupo.visible = true;
}

function animarHolo(p3, reloj) {  if (!holo) return;
  holo.grupo.visible = p3 > 0.02;
  if (!holo.grupo.visible) return;
  const pulso = 0.86 + 0.14 * Math.sin(reloj * 2.2);
  holo.materiales.forEach(({ mat, tope, sprite }) => {
    mat.opacity = tope * p3 * (sprite ? pulso : 1);
  });
  holo.grupo.position.y = Math.sin(reloj * 0.9) * 0.12 * p3;
}

/* ---------- navegación entre secciones ---------- */
function duracion() {
  return clips.length ? Math.max.apply(null, clips.map((c) => c.duration)) : 5;
}

function seccionDelHash() {
  const texto = location.hash || '';
  const porId = /#([a-z]+)$/.exec(texto);
  if (porId) {
    const i = SECCIONES.findIndex((s) => s.id === porId[1]);
    if (i >= 0) return i;
  }
  const porNumero = /#seccion-(\d+)/.exec(texto);
  if (porNumero) return Math.max(0, Math.min(SECCIONES.length - 1, Number(porNumero[1])));
  return null;
}

function seccionInicial() {
  const delHash = seccionDelHash();
  if (delHash !== null) return delHash;
  try {
    const guardada = sessionStorage.getItem('cedi:seccion');
    if (guardada !== null && guardada !== '') {
      return Math.max(0, Math.min(SECCIONES.length - 1, Number(guardada) || 0));
    }
  } catch (err) {}
  return 0;
}

function ir(indice, directo) {
  if (modoJuego) salirJuego(false);
  const total = SECCIONES.length - 1;
  seccionActual = Math.max(0, Math.min(total, indice));
  const sec = SECCIONES[seccionActual];

  // el clip repite en bucle: justo en la duración exacta volvería al inicio
  tiempoObjetivo = Math.min((duracion() / 4) * sec.fase, duracion() - 0.02);
  if (directo) tiempoActual = tiempoObjetivo;

  const v = sec.vista;
  // en vertical el campo horizontal se estrecha: fuera se aleja la cámara para que
  // el encuadre no quede recortado; dentro de un cuarto alejarla saldría del recinto,
  // así que se abre el campo vertical conservando el encuadre horizontal de escritorio
  const proporcion = camara.aspect || 1.6;
  const interior = !!v.interior;
  const distancia = proporcion < 1.6 && !interior
    ? v.dist * Math.min(1.9, Math.pow(1.6 / proporcion, 0.7))
    : v.dist;
  // los interiores se miran como con un gran angular: se conserva un campo
  // horizontal amplio en cualquier proporción sin mover la cámara del cuarto
  const fovDeseado = interior
    ? Math.min(78, Math.max(FOV_BASE, 2 * Math.atan(Math.tan(FOV_INTERIOR / 2) / proporcion) * 180 / Math.PI))
    : FOV_BASE;
  if (Math.abs(camara.fov - fovDeseado) > 0.01) {
    camara.fov = fovDeseado;
    camara.updateProjectionMatrix();
  }
  // las tomas de interiores necesitan acercarse más de lo que permite el orbital de exteriores
  controles.minDistance = Math.max(1.2, Math.min(8, distancia * 0.6));
  camDestino = posicionCamara(v.obj, distancia, v.giro, v.altura);
  tgtDestino = new THREE.Vector3(v.obj[0], v.obj[1], v.obj[2]);
  // en pantallas anchas el panel tapa la izquierda: se corre la composición
  const ancho = LIENZO.clientWidth || window.innerWidth;
  if (ancho >= 1000) {
    const vista = new THREE.Vector3().subVectors(tgtDestino, camDestino).normalize();
    const derecha = new THREE.Vector3().crossVectors(vista, new THREE.Vector3(0, 1, 0)).normalize();
    const altoVisible = 2 * v.dist * Math.tan((camara.fov * Math.PI / 180) / 2);
    const corrimiento = altoVisible * camara.aspect * (v.der === undefined ? 0.15 : v.der);
    camDestino.addScaledVector(derecha, -corrimiento);
    tgtDestino.addScaledVector(derecha, -corrimiento);
  }
  if (directo) {
    camara.position.copy(camDestino);
    controles.target.copy(tgtDestino);
    controles.update();
    camDestino = null;
    tgtDestino = null;
  }

  pintarHud(seccionActual);
  if (pantalla) pantalla.pintar(sec.fase);
  pintarRiel();
  if (PROGRESO) PROGRESO.style.width = ((seccionActual + 1) / SECCIONES.length * 100) + '%';
  if (history.replaceState) history.replaceState(null, '', '#' + sec.id);
  try { sessionStorage.setItem('cedi:seccion', String(seccionActual)); } catch (err) {}
}

function pintarHud(i) {
  const s = SECCIONES[i];
  const ultima = i === SECCIONES.length - 1;

  let indice = '';
  SECCIONES.forEach((sec, k) => {
    const actual = k === i;
    indice +=
      '<button type="button" class="rec-idx' + (actual ? ' on' : '') + '" data-ir="' + k + '"' +
      ' title="' + sec.corto + '"' +
      (actual ? ' aria-current="true"' : '') +
      ' aria-label="Ir a la parada ' + sec.n + ': ' + sec.titulo + '">' +
      '<b>' + sec.n + '</b></button>';
  });

  HUD.innerHTML =
    '<div class="rec-hud-bar">' +
      '<span class="rn">' + s.n + ' de ' + SECCIONES.length + ' · ' + s.id + '</span>' +
      '<button type="button" class="rec-hud-close" id="visorHudClose" aria-label="Cerrar el menú">' +
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>' +
      '</button>' +
    '</div>' +
    '<div class="rec-index">' +
      '<p class="rec-index-t">Ir a una parada</p>' +
      '<div class="rec-index-grid">' + indice + '</div>' +
    '</div>' +
    '<h1>' + s.titulo + '</h1>' +
    '<div class="rec-hud-body">' +
      '<p>' + s.lead + '</p>' +
      '<ul>' + s.bullets.map((b) => '<li>' + b + '</li>').join('') + '</ul>' +
      '<span class="rm">' + s.metrica + '</span>' +
    '</div>' +
    '<button type="button" class="rec-continuar" id="visorContinuar">' +
    (ultima ? 'Volver al inicio' : 'Continuar · ' + SECCIONES[i + 1].titulo) +
    '</button>';

  if (BOTON_MENU) {
    const num = BOTON_MENU.querySelector('.rmb-num');
    const txt = BOTON_MENU.querySelector('.rmb-txt');
    if (num) num.textContent = s.n;
    if (txt) txt.textContent = s.corto || s.titulo;
    BOTON_MENU.setAttribute('aria-label', 'Menú del recorrido · parada ' + s.n + ': ' + s.titulo);
  }
}

/* el texto y el índice viven en un panel que sale del botón de la esquina */
function abrirMenu(estado) {
  menuAbierto = !!estado;
  HUD.hidden = !menuAbierto;
  if (menuAbierto) HUD.scrollTop = 0;
  if (!BOTON_MENU) return;
  BOTON_MENU.classList.toggle('abierto', menuAbierto);
  BOTON_MENU.setAttribute('aria-expanded', menuAbierto ? 'true' : 'false');
}

function enlazarMenu() {
  if (BOTON_MENU) BOTON_MENU.addEventListener('click', () => abrirMenu(!menuAbierto));

  HUD.addEventListener('click', (e) => {
    const destino = e.target.closest ? e.target.closest('[data-ir]') : null;
    if (destino) {
      ir(Number(destino.getAttribute('data-ir')));
      HUD.scrollTop = 0;
      if (window.matchMedia('(max-width:900px)').matches) abrirMenu(false);
      return;
    }
    if (e.target.id === 'visorHudClose') abrirMenu(false);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menuAbierto) abrirMenu(false);
  });

  // tocar el modelo cierra el menú para dejar ver la escena
  LIENZO.addEventListener('pointerdown', () => {
    if (menuAbierto) abrirMenu(false);
  });

  abrirMenu(false);
}

function pintarRiel() {
  Array.prototype.forEach.call(RIEL.querySelectorAll('.rec-step'), (btn, i) => {
    btn.classList.toggle('on', i === seccionActual);
    if (i === seccionActual) {
      btn.setAttribute('aria-current', 'true');
      if (btn.scrollIntoView) btn.scrollIntoView({ block: 'nearest', inline: 'center' });
    } else {
      btn.removeAttribute('aria-current');
    }
  });
  const prev = document.getElementById('visorPrev');
  const next = document.getElementById('visorNext');
  if (prev) prev.disabled = seccionActual === 0;
  if (next) next.disabled = seccionActual === SECCIONES.length - 1;
}

function construirRiel() {
  SECCIONES.forEach((s, i) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'rec-step' + (i === 0 ? ' on' : '');
    btn.innerHTML = '<b>' + s.n + '</b><span>' + (s.corto || s.titulo) + '</span>';
    btn.setAttribute('aria-label', 'Sección ' + s.n + ': ' + s.titulo);
    btn.addEventListener('click', () => ir(i));
    RIEL.insertBefore(btn, RIEL.querySelector('.rec-arrows'));
  });
}

function avanzar() {
  if (seccionActual >= SECCIONES.length - 1) ir(0);
  else ir(seccionActual + 1);
}

function enlazarControles() {
  construirRiel();

  const prev = document.getElementById('visorPrev');
  const next = document.getElementById('visorNext');
  if (prev) prev.addEventListener('click', () => ir(seccionActual - 1));
  if (next) next.addEventListener('click', () => ir(seccionActual + 1));

  if (HUD) {
    HUD.addEventListener('click', (e) => {
      if (e.target && e.target.id === 'visorContinuar') avanzar();
    });
  }

  const orbita = document.getElementById('visorOrbita');
  if (orbita) {
    orbita.addEventListener('click', () => {
      if (modoJuego) salirJuego(false);
      girando = !girando;
      controles.autoRotate = girando;
      orbita.classList.toggle('on', girando);
      orbita.textContent = girando ? 'Detener giro' : 'Girar solo';
    });
  }

  const reset = document.getElementById('visorReset');
  if (reset) reset.addEventListener('click', () => ir(0));

  document.addEventListener('keydown', (e) => {
    if (modoJuego) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const tag = (document.activeElement && document.activeElement.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ' || e.key === 'Enter') {
      avanzar(); e.preventDefault();
    }
    if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      ir(seccionActual - 1); e.preventDefault();
    }
    if (e.key === 'Home') { ir(0); e.preventDefault(); }
    if (e.key === 'End') { ir(SECCIONES.length - 1); e.preventDefault(); }
  });
}

/* ---------- modo juego: recorrido a pie con teclado y joystick ----------
   Con el modo apagado, la cámara viaja entre las paradas del documento y el
   ratón orbita alrededor del objetivo. Encendido, la cámara se libera: se
   camina con WASD o flechas, se mira arrastrando y, en el celular, aparece un
   joystick donde se apoya el pulgar izquierdo y se mira arrastrando a la
   derecha, como en un juego en primera persona. */
const VEL_CAMINAR = 9.0;
const VEL_VERTICAL = 6.5;
const RADIO_JOY = 56;
const LIMITE = { x0: -98, x1: 34, y0: 0.7, y1: 62, z0: -31, z1: 40 };
const TECLAS_JUEGO = {
  KeyW: 1, KeyA: 1, KeyS: 1, KeyD: 1, KeyQ: 1, KeyE: 1, KeyC: 1, KeyR: 1,
  ArrowUp: 1, ArrowDown: 1, ArrowLeft: 1, ArrowRight: 1,
  Space: 1, ShiftLeft: 1, ShiftRight: 1, ControlLeft: 1, ControlRight: 1
};
const TACTIL = ('ontouchstart' in window) || (navigator.maxTouchPoints || 0) > 0;
const MENSAJE_JUEGO = TACTIL
  ? 'Joystick a la izquierda · arrastra a la derecha para mirar · ▲▼ sube y baja'
  : 'WASD o flechas para caminar · arrastra para mirar · Espacio o E suben · Shift o Q bajan · Esc sale';

const JOY = document.getElementById('visorJoy');
const PAD = document.getElementById('visorPad');
const BTN_JUEGO = document.getElementById('visorJuego');

let modoJuego = false;
let yaw = 0;
let pitch = 0;
let padSubir = false;
let padBajar = false;
const teclas = Object.create(null);
const joy = { id: null, x0: 0, y0: 0, dx: 0, dy: 0 };
const mirando = { id: null, x: 0, y: 0 };
const relojJuego = new THREE.Clock();

function direccionMirada() {
  const cos = Math.cos(pitch);
  return new THREE.Vector3(Math.sin(yaw) * cos, Math.sin(pitch), Math.cos(yaw) * cos);
}

function apuntar() {
  camara.lookAt(tmpA.copy(camara.position).add(direccionMirada()));
  controles.target.copy(camara.position).addScaledVector(direccionMirada(), 14);
}

function entrarJuego() {
  if (!camara || !controles || modoJuego) return;
  modoJuego = true;
  camDestino = null;
  tgtDestino = null;
  girando = false;
  controles.autoRotate = false;
  controles.enabled = false;

  const dir = new THREE.Vector3();
  camara.getWorldDirection(dir);
  yaw = Math.atan2(dir.x, dir.z);
  pitch = Math.asin(Math.max(-1, Math.min(1, dir.y)));
  camara.position.y = Math.max(LIMITE.y0, Math.min(LIMITE.y1, camara.position.y));

  document.body.classList.add('jugando');
  if (TACTIL) document.body.classList.add('tactil');
  LIENZO.classList.add('juego');
  const orbita = document.getElementById('visorOrbita');
  if (orbita) {
    orbita.classList.remove('on');
    orbita.textContent = 'Girar solo';
  }
  if (BTN_JUEGO) {
    BTN_JUEGO.textContent = 'Salir del recorrido a pie';
    BTN_JUEGO.classList.add('on');
    BTN_JUEGO.setAttribute('aria-pressed', 'true');
  }
  if (ESTADO) ESTADO.textContent = MENSAJE_JUEGO;
  relojJuego.getDelta();
  setTimeout(reajustar, 30);
}

function salirJuego(volver) {
  if (!modoJuego) return;
  modoJuego = false;
  joy.id = null;
  joy.dx = 0;
  joy.dy = 0;
  mirando.id = null;
  padSubir = false;
  padBajar = false;
  Object.keys(teclas).forEach((k) => { teclas[k] = false; });
  if (JOY) JOY.classList.remove('activo');
  LIENZO.classList.remove('juego');
  document.body.classList.remove('jugando');
  if (BTN_JUEGO) {
    BTN_JUEGO.textContent = 'Recorrer a pie';
    BTN_JUEGO.classList.remove('on');
    BTN_JUEGO.setAttribute('aria-pressed', 'false');
  }
  if (ESTADO) ESTADO.textContent = MENSAJE;
  controles.enabled = true;
  if (volver) {
    ir(seccionActual, true);
  } else {
    apuntar();
    controles.update();
    camDestino = null;
    tgtDestino = null;
  }
  setTimeout(reajustar, 30);
}

function alternarJuego() {
  if (modoJuego) salirJuego(true);
  else entrarJuego();
}

function coordenadaLocal(evento) {
  const caja = LIENZO.getBoundingClientRect();
  return { x: evento.clientX - caja.left, y: evento.clientY - caja.top, ancho: caja.width };
}

function alBajarPuntero(evento) {
  if (!modoJuego) return;
  if (evento.button !== undefined && evento.button > 0) return;
  const punto = coordenadaLocal(evento);
  const usaJoystick = evento.pointerType !== 'mouse'
    && punto.x < punto.ancho * 0.45
    && joy.id === null;
  if (usaJoystick) {
    joy.id = evento.pointerId;
    joy.x0 = evento.clientX;
    joy.y0 = evento.clientY;
    joy.dx = 0;
    joy.dy = 0;
    if (JOY) {
      JOY.style.left = punto.x + 'px';
      JOY.style.top = punto.y + 'px';
      JOY.classList.add('activo');
      const perilla = JOY.firstElementChild;
      if (perilla) perilla.style.transform = 'translate(-50%,-50%)';
    }
  } else if (mirando.id === null) {
    mirando.id = evento.pointerId;
    mirando.x = evento.clientX;
    mirando.y = evento.clientY;
  }
  if (LIENZO.setPointerCapture) {
    try { LIENZO.setPointerCapture(evento.pointerId); } catch (err) {}
  }
  evento.preventDefault();
}

function alMoverPuntero(evento) {
  if (!modoJuego) return;
  if (evento.pointerId === joy.id) {
    let dx = evento.clientX - joy.x0;
    let dy = evento.clientY - joy.y0;
    const largo = Math.hypot(dx, dy);
    if (largo > RADIO_JOY) {
      dx = (dx / largo) * RADIO_JOY;
      dy = (dy / largo) * RADIO_JOY;
    }
    joy.dx = dx;
    joy.dy = dy;
    const perilla = JOY && JOY.firstElementChild;
    if (perilla) {
      perilla.style.transform = 'translate(calc(-50% + ' + dx + 'px), calc(-50% + ' + dy + 'px))';
    }
    evento.preventDefault();
    return;
  }
  if (evento.pointerId === mirando.id) {
    yaw -= (evento.clientX - mirando.x) * 0.0042;
    pitch -= (evento.clientY - mirando.y) * 0.0034;
    pitch = Math.max(-1.35, Math.min(1.35, pitch));
    mirando.x = evento.clientX;
    mirando.y = evento.clientY;
    evento.preventDefault();
  }
}

function alSoltarPuntero(evento) {
  if (evento.pointerId === joy.id) {
    joy.id = null;
    joy.dx = 0;
    joy.dy = 0;
    if (JOY) JOY.classList.remove('activo');
  }
  if (evento.pointerId === mirando.id) mirando.id = null;
  if (LIENZO.releasePointerCapture && LIENZO.hasPointerCapture
    && LIENZO.hasPointerCapture(evento.pointerId)) {
    try { LIENZO.releasePointerCapture(evento.pointerId); } catch (err) {}
  }
}

function soltarTodo() {
  Object.keys(teclas).forEach((k) => { teclas[k] = false; });
  joy.id = null;
  joy.dx = 0;
  joy.dy = 0;
  mirando.id = null;
  padSubir = false;
  padBajar = false;
  if (JOY) JOY.classList.remove('activo');
}

function actualizarJuego(dt) {
  let adelante = 0;
  let lateral = 0;
  let vertical = 0;

  if (teclas.KeyW || teclas.ArrowUp) adelante += 1;
  if (teclas.KeyS || teclas.ArrowDown) adelante -= 1;
  if (teclas.KeyD || teclas.ArrowRight) lateral += 1;
  if (teclas.KeyA || teclas.ArrowLeft) lateral -= 1;
  // vertical: Espacio y E suben, Shift y las demas bajan
  if (teclas.Space || teclas.KeyE || teclas.KeyR) vertical += 1;
  if (teclas.ShiftLeft || teclas.ShiftRight
    || teclas.KeyQ || teclas.KeyC
    || teclas.ControlLeft || teclas.ControlRight) vertical -= 1;
  if (padSubir) vertical += 1;
  if (padBajar) vertical -= 1;

  if (joy.id !== null) {
    adelante -= joy.dy / RADIO_JOY;
    lateral += joy.dx / RADIO_JOY;
  }

  const modulo = Math.hypot(adelante, lateral);
  if (modulo > 1) {
    adelante /= modulo;
    lateral /= modulo;
  }

  const seno = Math.sin(yaw);
  const coseno = Math.cos(yaw);

  // derecha de la camara = forward x up; con yaw 0 (mirando a +z) es -x
  camara.position.x += (seno * adelante - coseno * lateral) * VEL_CAMINAR * dt;
  camara.position.z += (coseno * adelante + seno * lateral) * VEL_CAMINAR * dt;
  camara.position.y += vertical * VEL_VERTICAL * dt;
  camara.position.x = Math.max(LIMITE.x0, Math.min(LIMITE.x1, camara.position.x));
  camara.position.y = Math.max(LIMITE.y0, Math.min(LIMITE.y1, camara.position.y));
  camara.position.z = Math.max(LIMITE.z0, Math.min(LIMITE.z1, camara.position.z));

  apuntar();
}

function enlazarJuego() {
  if (BTN_JUEGO) BTN_JUEGO.addEventListener('click', alternarJuego);
  if (TACTIL) document.body.classList.add('tactil');

  LIENZO.addEventListener('pointerdown', alBajarPuntero);
  LIENZO.addEventListener('pointermove', alMoverPuntero);
  LIENZO.addEventListener('pointerup', alSoltarPuntero);
  LIENZO.addEventListener('pointercancel', alSoltarPuntero);
  LIENZO.addEventListener('contextmenu', (e) => {
    if (modoJuego) e.preventDefault();
  });

  document.addEventListener('keydown', (e) => {
    if (!modoJuego) return;
    if (e.key === 'Escape') {
      salirJuego(true);
      return;
    }
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (TECLAS_JUEGO[e.code]) {
      teclas[e.code] = true;
      e.preventDefault();
    }
  });
  document.addEventListener('keyup', (e) => {
    if (teclas[e.code]) {
      teclas[e.code] = false;
      if (modoJuego) e.preventDefault();
    }
  });
  window.addEventListener('blur', soltarTodo);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) soltarTodo();
  });

  if (PAD) {
    Array.prototype.forEach.call(PAD.querySelectorAll('button'), (boton) => {
      const eje = boton.getAttribute('data-eje');
      const poner = (valor) => {
        if (eje === 'subir') padSubir = valor;
        else padBajar = valor;
      };
      boton.addEventListener('pointerdown', (e) => {
        poner(true);
        try { boton.setPointerCapture(e.pointerId); } catch (err) {}
        e.preventDefault();
      });
      boton.addEventListener('pointerup', () => poner(false));
      boton.addEventListener('pointercancel', () => poner(false));
      boton.addEventListener('pointerleave', () => poner(false));
    });
  }
}

function reajustar() {
  const ancho = LIENZO.clientWidth || window.innerWidth;
  const alto = LIENZO.clientHeight || window.innerHeight;
  const proporcionAnterior = camara.aspect;
  camara.aspect = ancho / alto;
  camara.updateProjectionMatrix();
  render.setSize(ancho, alto, false);
  // al girar el móvil cambia la proporción: se rehace el encuadre actual
  if (!modoJuego && Math.abs(camara.aspect - proporcionAnterior) > 0.2) ir(seccionActual);
}

function bucle() {
  requestAnimationFrame(bucle);
  const dt = 1 / 60;
  const real = Math.min(relojJuego.getDelta(), 0.05);

  tiempoActual += (tiempoObjetivo - tiempoActual) * Math.min(1, dt * 4.5);
  if (mixer) mixer.setTime(tiempoActual);

  if (modoJuego) {
    actualizarJuego(real);
  } else if (camDestino && tgtDestino) {
    const paso = Math.min(1, dt * 2.4);
    camara.position.lerp(tmpA.copy(camDestino), paso);
    controles.target.lerp(tmpB.copy(tgtDestino), paso);
    if (camara.position.distanceTo(camDestino) < 0.08) {
      camara.position.copy(camDestino);
      controles.target.copy(tgtDestino);
      camDestino = null;
      tgtDestino = null;
    }
  }

  const avance = clips.length ? (tiempoActual / duracion()) * 4 : 0;
  animarHolo(Math.max(0, Math.min(1, avance - 2)), performance.now() / 1000);
  animarCinta(Math.max(0, Math.min(1, avance - 1.5)), real);
  animarMuroVideo(Math.min(1, avance), real);
  if (panel) panel.tick(real);

  if (!modoJuego) controles.update();
  render.render(escena, camara);
}

if (document.readyState === 'complete') iniciar();
else window.addEventListener('load', iniciar);
