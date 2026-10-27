// Convert a DWG to one SVG of the whole model space (Y is flipped: svg_y = -world_y).
// usage: node scripts/dwg_to_svg.mjs input.dwg out.svg
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Dwg_File_Type, LibreDwg } from '@mlightcad/libredwg-web';

const [,, inPath, outPath] = process.argv;
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const libredwg = await LibreDwg.create(path.join(root, 'node_modules/@mlightcad/libredwg-web/wasm/'));
const db = libredwg.convert(libredwg.dwg_read_data(fs.readFileSync(inPath), Dwg_File_Type.DWG));
fs.writeFileSync(outPath, libredwg.dwg_to_svg(db));
console.log('wrote', outPath);
