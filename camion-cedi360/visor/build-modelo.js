const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const glb = fs.readFileSync(path.join(__dirname, '..', 'export', 'cedi360.glb'));
const gz = zlib.gzipSync(glb, { level: 9 });
const b64 = gz.toString('base64');
const salida = path.join(__dirname, 'modelo.js');

fs.writeFileSync(
  salida,
  'export default "data:application/gzip;base64,' + b64 + '";\n',
  'utf8'
);

const kb = (n) => (n / 1024).toFixed(0) + ' KB';
console.log(
  'glb ' + kb(glb.length) + ' -> gzip ' + kb(gz.length) + ' -> modelo.js ' +
  kb(fs.statSync(salida).size)
);
