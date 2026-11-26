# Propuesta ALTIPAL 2026 · CEDI 360

Propuesta comercial interactiva de FUNDASERINCO para ALTIPAL: el documento de
la propuesta y un recorrido 3D por el CEDI (centro de distribución), con las
áreas del programa —centro de acopio, plataforma de descargue, cámara de frío,
subestación, sala técnica, centro de seguridad electrónica y sala de juntas—
en el sitio donde aplica cada eje.

El capítulo 13 (Experiencia) enlaza cuatro desarrollos propios publicados como
prueba de la línea de software: MotoBot (chatbot agéntico), SentinelOps
(seguimiento y SLA), Invernadero de café (gemelo digital con telemetría) y
Metro Cuadrado (panel operativo). Cada tarjeta abre su demo en una pestaña
nueva. La API de MotoBot se activa solo en la prueba de la reunión técnica o al
implementar el agente; el resto del tiempo el demo responde con guiones.

## Qué hay aquí

| Ruta | Contenido |
| --- | --- |
| `index.html` | la propuesta en HTML (se abre con doble clic) |
| `recorrido3d.html` | recorrido 3D de 25 paradas por la planta |
| `recorrido.html` | visor de láminas del despiece del tractocamión |
| `assets/js/visor3d.js` | visor three.js con el modelo dentro (bundle IIFE) |
| `assets/css/ui-menus.css` | capa de menús 2026: barra, navegación, riel y panel |
| `assets/js/ui-menus.js` | resplandor de vidrio que sigue al puntero |
| `camion-cedi360/blender/` | fuentes del modelo: escena, almacén, muelle, áreas de programa, láminas |
| `camion-cedi360/visor/src/` | fuentes del visor (`main.js`, `secciones.js`, `panel.js`, `datos.js`) |
| `camion-cedi360/estado.txt` | bitácora técnica y decisiones del proyecto |
| `camion-cedi360/plan-datos-al-valor.txt` | plan de los puntos 1 a 3 de «De los datos al valor empresarial» |
| `camion-cedi360/render/` | láminas renderizadas de la planta |
| `Propuesta CEDI 360 - ALTIPAL 2026.pdf` | propuesta en PDF |

## Publicación en GitHub Pages

El sitio se publica desde la **raíz de la rama `main`**, por eso `index.html`
vive en la raíz del repositorio: GitHub Pages busca `index.html` en la raíz y,
si no lo encuentra, muestra este README. La dirección pública es
<https://shoyosb-maker.github.io/propuesta-altipal/>.

## Recorrido 3D

Se navega con el riel inferior, las flechas del teclado o el botón de la
parada. La rueda del mouse no cambia de parada: sobre el lienzo acerca o aleja
el modelo y fuera de él hace scroll normal.
El botón de la esquina —abajo a la izquierda en escritorio, una barra bajo el
lienzo en el celular— abre el panel de la parada actual hacia arriba: trae el
texto y el índice `01`–`25`, y tocar un número salta a esa parte del recorrido.
El panel arranca cerrado para dejar el modelo despejado y se cierra con la ×,
con `Esc` o tocando el modelo.
El botón **Recorrer a pie** activa el modo juego: `W` adelante, `S` atrás,
`A` izquierda, `D` derecha, `Shift` agacharse y la barra espaciadora subir;
en el celular aparece un joystick y el arrastre de la mirada.

## Reparto de áreas del CEDI

La nave de 50 × 46 m queda para almacenamiento: recibo al sur, despacho al
norte y tres muelles al este. El frío y la energía salieron de la nave y viven
en dos pabellones exentos al oeste, sobre una plataforma común a la cota del
piso (1,25 m):

| Área | Medidas | Dónde |
| --- | --- | --- |
| Cuarto frío | 18 × 14 m | pabellón exento, x −96 a −78 / y −30 a −16 |
| Subestación | 18 × 12 m | pabellón exento, x −96 a −78 / y −12 a 0 |
| Pasillo técnico | 4 × 30 m | acristalado, x −78 a −74 / y −30 a 0 |
| Jardín de acceso | 12 × 30 m | entre el pasillo y la fachada oeste de la nave |
| Acceso de personal | puerta de 3 m con marquesina | fachada oeste, y −16 |
| Anexo administrativo | 12 × 8 m + piso 2 | al norte, con ventanales en planta baja |
| Escalera del anexo | 13 peldaños, separada 2 m de la fachada | sube al piso 2 por una pasarela al rellano |

El jardín lleva caminos de grava, árboles, bancas, materas y luminarias, y es
el que conecta la puerta de personal con el pasillo que sirve a los dos
pabellones. Las áreas se definen en `camion-cedi360/blender/programa.py`
(`FRIO`, `ENE`, `PASILLO`, `JARDIN`, `PLATAFORMA`).

El recorrido a pie encadena los cuatro espacios sin salir al patio de
maniobras, y todos los vanos son huecos reales en el muro:

| Paso | Dónde | Medidas |
| --- | --- | --- |
| Puerta de personal de la nave | muro oeste, y −17,5 a −14,5 | 3,0 × 2,7 m |
| Paso al anexo | banda norte, x −38,3 a −35,3 | 3,0 × 2,7 m |
| Jardín del anexo | franja entre la nave y el anexo | 32 × 5 m |
| Puerta del anexo | muro sur del anexo, alineada con el paso | 1,0 × 2,1 m |

El logo de FUNDASERINCO va en grande sobre dos paredes del almacén (muro oeste
interior, 11 m, y banda norte, 12 m), en la fachada este sobre el andén
(7,5 m) y pintado en el suelo del patio de maniobras (24 m, corrido a lo largo
del patio —norte-sur— en la franja libre entre el tractocamión y las dos
furgonetas, en `assets/img/brand/fundaserinco-blanco.png`); los de pared se arman en
`camion-cedi360/blender/marca_altipal.py` con la textura
`assets/marca/fundaserinco-blanco.png`.

## Bandas transportadoras

La banda troncal viene del modelo; el corredor central llegó sin banda, así que
el visor la completa en three.js con la misma sección: tablero, rieles, patas y
rodillos. Las dos líneas recorren el mismo tramo (z 26 a −8,6, los extremos
reales del tablero del modelo) y comparten un solo reloj, de modo que los
paquetes de ambas arrancan y terminan a la vez y ninguno se sale de la cinta ni
cruza un muro. El interruptor «Banda de boxes» pausa ese reloj: no mueve nada
más de la escena.

## Panel de operación (simulacro)

El recorrido 3D trae un panel —botón **Panel de operación** en la barra del
lienzo— que mueve el modelo en vivo para mostrar cómo se opera el CEDI:

| Grupo | Qué hace |
| --- | --- |
| Iluminación | Enciende y apaga nave y andén, jardín y pasillo, anexo y patio; el ambiente nocturno baja la luz de escena |
| Puertas y accesos | Abre y cierra los tres portones seccionales, las cortinas de tiras y la puerta corredera del frío |
| Sistemas | Un solo interruptor sobre las dos líneas de banda: pausa y continuación |
| Seguridad electrónica | Prende y apaga las cámaras de muelle, interiores y perímetro por grupos, y la grabación (NVR); al apagarlas, los monitores del cuarto de control pasan a «SIN SEÑAL» |
| Simulacro | Descarga y retira paquetes en el andén, alarma de intrusión, corte de energía y restablecer el turno |

Las piezas que el panel mueve salen de `camion-cedi360/blender/simulacion.py`
(colección `T93_SIM`), con el pivote resuelto: los portones cuelgan del dintel
(se recogen escalando en Z), la hoja del frío corre sobre su vano y la carga
viaja oculta hasta que el simulacro la suelta. De la banda solo se mueve ella
con sus cajas: los AMR y el sorter quedan fuera del visor. La lógica vive en
`camion-cedi360/visor/src/panel.js` y se engancha al
bucle del visor desde `main.js`.

## Capa de datos (puntos 1 a 3 de «De los datos al valor empresarial»)

El botón «Capa de datos» del recorrido enciende una lectura sobre la planta: la
operación no se toca y encima de ella aparece, anclado a cada zona, el
instrumento que lee lo que esa zona ya registra. No son «modalidades de
negocio»: son instrumentos de una misma capa, y cada ficha muestra el tránsito
dato → información → decisión. La ficha del asistente gerencial lleva las
preguntas del documento y las responde sobre una cifra verificable, con el
modelo solo explicando.

- `camion-cedi360/visor/src/datos.js`: anclajes, fichas y consultas.
- `camion-cedi360/plan-datos-al-valor.txt`: el plan completo de los puntos 1 a
  3, lo que queda fuera de alcance y las ideas pendientes del punto 3.

El encendido de luces no se queda en el material de las luminarias: cada zona
tiene focos reales (`PointLight`), un cono aditivo que dibuja el haz y un halo
en el artefacto, para que el cambio se lea sobre el piso, las estanterías y la
carga incluso con el ambiente diurno. El muro de video del cuarto de control,
en cambio, cambia de señal al instante: cada cámara está atada a su monitor y
al apagarla el visor pinta el cartel de «SIN SEÑAL».

## Sistema de menús (capa 2026)

`assets/css/ui-menus.css` es la última hoja de las cinco páginas y solo cambia
la piel de los menús: barra superior, navegación de capítulos, barra de los
documentos de detalle, riel del recorrido, menú desplegable del recorrido 3D y
panel de operación. No toca el marcado ni la estructura.

- **Dos acabados del mismo sistema**: «papel» (deck, documentos y propuesta) y
  «noche» (`body.recorrido-page`: recorrido y recorrido 3D).
- **Superficies de vidrio**: `backdrop-filter` con saturación, filete de un
  píxel, sombra en tres capas y brillo interior de un píxel en el borde alto.
- **Islas flotantes**: la barra superior deja de ser una franja y pasa a ser una
  cápsula separada del borde que se cierra al hacer scroll (`.is-scrolled`).
- **Control segmentado**: las acciones de la barra viven dentro de una pista
  común; al pasar el ratón cada una recibe su propia cápsula blanca.
- **Puntos de capítulo**: la columna no tiene caja propia —sin borde, sin sombra
  y sin fondo— y se mantiene invisible hasta que el puntero entra en ella o el
  foco llega con el teclado; entonces aparece con un velo translúcido. En móvil
  y tablet (≤900 px) queda siempre visible, porque ahí no hay hover que la
  descubra. El capítulo actual se estira en una píldora con su número.
- **Navegación mínima en el teléfono** (≤760 px): quedan solo los puntos y el
  texto pequeño del contador (`01 / 14`), como en el escritorio. Las flechas se
  retiran —tapaban el texto— y el contador pierde cápsula, borde y fondo: es
  mono pequeño al pie de la columna, con un halo del color de la barra para
  ganar sobre fotos.
- **Sin caja en táctil**: en pantallas sin puntero (o ≤900 px) la columna de
  puntos se queda visible pero nunca dibuja el velo translúcido, ni al tocar ni
  al enfocar un punto.
- **Un solo ambiente, de noche**: el sitio va siempre con la paleta oscura
  (`data-tema="noche"` fijado en el `<head>` de las tres páginas de papel y
  reforzado en `ui-menus.js` por si el HTML llega cacheado). El interruptor
  día/noche se retiró; los tokens del tema claro siguen en `ui-menus.css` por si
  se quiere volver a encender.
- **Fondo de las secciones**: la foto de la caja ALTIPAL vive en dos capas
  fijas —`body::before` con `blur(38px)` y `body::after` con el velo— así que
  acompaña el scroll sin repetirse en cada capítulo, y el contenido queda
  encima porque `body>*` ya lleva `z-index:1`. Al imprimir las dos capas se
  apagan y el papel vuelve a blanco.
- **Ficha del programa (portada)**: tarjeta negra con marco prismático —oro,
  violeta y cian— montado con dos capas de `background` (`padding-box` /
  `border-box`), brillo de vitrina en `::after`, título en degradado con corona,
  chip con la referencia `CDI-360-2026-ALT` y filas de datos con etiqueta mono
  y valor en blanco. La caja ALTIPAL del render (`altipal-caja.webp`, recortada
  con el fondo fundido en alfa) ocupa la esquina alta. Con ratón la tarjeta se
  inclina hacia el borde donde está el puntero —`ui-menus.js` escribe `--fx` y
  `--fy`— y una estela de luz la cruza **una sola vez** por cada entrada del
  puntero (animación CSS atada a `:hover`, así se reinicia al volver a entrar).
  Es la misma tarjeta en modo día y en modo noche; al imprimir vuelve a caja
  clara sin adornos.
- **Telón de capítulo**: al cambiar de sección con los puntos o las flechas, la
  foto de la caja ALTIPAL ocupa la pantalla ~1 s (240 ms de entrada, 520 de
  espera y 320 de salida) con una línea de progreso dorada. La navegación se
  ejecuta con el telón puesto, así que al levantarse la sección ya está en su
  sitio. Se intercepta el clic en captura y se reemite marcado (`__telon`) para
  que el deck haga su trabajo una sola vez; con `prefers-reduced-motion` no
  aparece.
- **Panel de operación**: cada acción es un interruptor tipo iOS (pista y pomo
  como pseudo-elementos sobre `aria-pressed`), agrupado en filas con su rótulo.
- **Rótulos adaptativos**: «Pantalla completa» lleva dos `span` (`lbl-lg` /
  `lbl-sm`) y en móvil muestra «Pantalla», para que entren las tres acciones y
  el nombre de la marca a partir de 360 px.
- **Contraste revisado**: el subtítulo de la marca, las migas y la etiqueta de
  la barra de documentos pasaron de `--ink-4` (2,7:1) a `--ink-3`; en pantallas
  pequeñas el vidrio se opaca para que la letra gane sobre cualquier fondo.

`assets/js/ui-menus.js` escribe `--ui-mx` / `--ui-my` en la superficie que está
bajo el cursor y el CSS los usa como centro de un degradado radial, para que el
vidrio tenga un resplandor que acompaña al puntero. Si el script no corre, el CSS
cae en una posición por defecto y todo se ve igual. También se conecta solo a
los paneles que aparecen después de cargar el modelo (menú del recorrido y panel
de operación) con un `MutationObserver`.

## Volver a construir

El modelo se arma por partes en Blender y se exporta a glTF; el visor se
compila con esbuild.

```bat
python blender\client.py exec --file blender\build_all.py
python blender\client.py exec --file blender\web_export.py
cd visor
node build-modelo.js
npx esbuild src/main.js --bundle --format=iife --target=es2019 --minify ^
    --outfile=../../assets/js/visor3d.js
```

`build_all.py` reconstruye la escena, las cotas, el holograma, el almacén, el
muelle y las áreas de programa. Los pasos y las trampas conocidas están en
`camion-cedi360/estado.txt`.

## Modelos de terceros

Los vehículos provienen de Sketchfab y se usan con atribución CC-BY, que
aparece en el pie del recorrido 3D: «MAN TGX 2010 V8» de DevPoly3D,
«Mercedes-Benz Sprinter» de Savelliy 07, «Delivery Truck» de jasmin.daniel y
«Forklift low poly» de 380660711785.
