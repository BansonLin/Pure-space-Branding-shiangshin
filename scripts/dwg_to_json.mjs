// Parse a DWG with the libredwg WebAssembly build and dump the converted database as JSON.
// usage: node scripts/dwg_to_json.mjs input.dwg out.json
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Dwg_File_Type, LibreDwg } from '@mlightcad/libredwg-web';

const [,, inPath, outPath] = process.argv;
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const libredwg = await LibreDwg.create(path.join(root, 'node_modules/@mlightcad/libredwg-web/wasm/'));
const dwg = libredwg.dwg_read_data(fs.readFileSync(inPath), Dwg_File_Type.DWG);
const db = libredwg.convert(dwg);
const replacer = (k, v) => (v instanceof Uint8Array ? `<bytes ${v.length}>` : (typeof v === 'bigint' ? v.toString() : v));
fs.writeFileSync(outPath, JSON.stringify(db, replacer));
console.log('entities', db.entities.length, 'layers', db.tables.LAYER.entries.length, 'blocks', db.tables.BLOCK_RECORD.entries.length);
