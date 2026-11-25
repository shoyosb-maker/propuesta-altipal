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
| `camion-cedi360/blender/` | fuentes del modelo: escena, almacén, muelle, áreas de programa, láminas |
| `camion-cedi360/visor/src/` | fuentes del visor (`main.js`, `secciones.js`) |
| `camion-cedi360/estado.txt` | bitácora técnica y decisiones del proyecto |
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
interior, 11 m, y banda norte, 12 m) y en la fachada este sobre el andén
(7,5 m); los tres se arman en `camion-cedi360/blender/marca_altipal.py` con la
textura `assets/marca/fundaserinco-blanco.png`.

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
