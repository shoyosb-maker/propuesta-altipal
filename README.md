# Propuesta ALTIPAL 2026 · CEDI 360

Propuesta comercial interactiva de FUNDASERINCO para ALTIPAL: el documento de
la propuesta y un recorrido 3D por el CEDI (centro de distribución), con las
áreas del programa —centro de acopio, plataforma de descargue, cámara de frío,
subestación, sala técnica, centro de seguridad electrónica y sala de juntas—
en el sitio donde aplica cada eje.

## Qué hay aquí

| Ruta | Contenido |
| --- | --- |
| `index.html` | la propuesta en HTML (se abre con doble clic) |
| `recorrido3d.html` | recorrido 3D de 23 paradas por la planta |
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
texto y el índice `01`–`23`, y tocar un número salta a esa parte del recorrido.
El panel arranca cerrado para dejar el modelo despejado y se cierra con la ×,
con `Esc` o tocando el modelo.
El botón **Recorrer a pie** activa el modo juego: `W` adelante, `S` atrás,
`A` izquierda, `D` derecha, `Shift` agacharse y la barra espaciadora subir;
en el celular aparece un joystick y el arrastre de la mirada.

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
