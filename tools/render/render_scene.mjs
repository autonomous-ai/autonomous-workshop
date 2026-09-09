#!/usr/bin/env node
// Trusted-host product renderer: three.js in headless Chromium (swiftshader).
//
// Usage:
//   node render_scene.mjs <scene.json> <out_dir>
//   node render_scene.mjs --self-check <out_dir>
//
// The scene file names STL parts (relative to its own directory), one colour
// and one row-major 4x4 transform per part (CAD millimetres, Z up), and the
// views to render. Every asset is served to the page from a loopback HTTP
// server; the page never touches the network. One PNG per view is written to
// <out_dir>/<view>.png and a JSON summary is printed on stdout.
import { chromium } from 'playwright';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const THREE_ROOT = path.join(HERE, 'node_modules', 'three');
const MAX_VIEW_SIZE = 4096;
const MAX_VIEWS = 16;
const MAX_PARTS = 512;
const MAX_ASSET_BYTES = 256 * 1024 * 1024;
const VIEW_TIMEOUT_MS = 180_000;

function fail(message) {
  process.stdout.write(JSON.stringify({ ok: false, error: String(message) }) + '\n');
  process.exit(2);
}

function isHexColour(value) {
  return typeof value === 'string' && /^#[0-9a-f]{6}$/.test(value);
}

function validateScene(scene) {
  if (!scene || typeof scene !== 'object') fail('scene must be an object');
  if (scene.schema_version !== 1) fail('scene schema_version must be 1');
  if (!isHexColour(scene.background)) fail('scene background must be #rrggbb');
  if (!Array.isArray(scene.views) || scene.views.length < 1 || scene.views.length > MAX_VIEWS) {
    fail('scene views must be a non-empty list');
  }
  if (!scene.scenes || typeof scene.scenes !== 'object') fail('scene scenes must be an object');
  const names = new Set();
  for (const view of scene.views) {
    if (!view || typeof view !== 'object') fail('view must be an object');
    if (typeof view.name !== 'string' || !/^[a-z0-9][a-z0-9_-]{0,63}$/.test(view.name)) fail('view name is unsafe');
    if (names.has(view.name)) fail('duplicate view name ' + view.name);
    names.add(view.name);
    if (!Number.isInteger(view.size) || view.size < 64 || view.size > MAX_VIEW_SIZE) fail('view size out of range');
    for (const key of ['azimuth', 'elevation']) {
      if (typeof view[key] !== 'number' || !Number.isFinite(view[key])) fail('view ' + key + ' must be finite');
    }
    if (typeof view.scene !== 'string' || !(view.scene in scene.scenes)) fail('view names an unknown scene');
  }
  for (const [name, definition] of Object.entries(scene.scenes)) {
    if (!/^[a-z0-9][a-z0-9_-]{0,63}$/.test(name)) fail('scene name is unsafe');
    if (!definition || !Array.isArray(definition.parts) || definition.parts.length < 1 || definition.parts.length > MAX_PARTS) {
      fail('scene ' + name + ' must list parts');
    }
    for (const part of definition.parts) {
      if (typeof part.stl !== 'string' || part.stl.startsWith('/') || part.stl.includes('..') || part.stl.includes('\\')) {
        fail('part stl path is unsafe');
      }
      if (!isHexColour(part.color)) fail('part colour must be #rrggbb');
      if (!Array.isArray(part.transform) || part.transform.length !== 16 || !part.transform.every((v) => typeof v === 'number' && Number.isFinite(v))) {
        fail('part transform must be 16 finite numbers');
      }
      if (part.shell_colors !== undefined) {
        if (!Array.isArray(part.shell_colors) || part.shell_colors.length < 1 || part.shell_colors.length > MAX_PARTS) fail('shell_colors must be a list');
        for (const entry of part.shell_colors) {
          if (typeof entry.name !== 'string' || !/^[a-z0-9][a-z0-9_-]{0,127}$/.test(entry.name)) fail('shell colour name is unsafe');
          if (typeof entry.volume !== 'number' || !Number.isFinite(entry.volume) || entry.volume <= 0) fail('shell colour volume must be positive');
          if (!isHexColour(entry.color)) fail('shell colour must be #rrggbb');
        }
      }
    }
  }
}

const PAGE_SCRIPT = `
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import * as BGU from 'three/addons/utils/BufferGeometryUtils.js';

const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const pmrem = new THREE.PMREMGenerator(renderer);
const environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
const geometryCache = new Map();

function parseStl(buffer) {
  const bytes = new Uint8Array(buffer);
  const head = new TextDecoder().decode(bytes.subarray(0, Math.min(bytes.length, 512)));
  const view = new DataView(buffer);
  const binaryCount = bytes.length >= 84 ? view.getUint32(80, true) : -1;
  const binaryMatches = bytes.length === 84 + binaryCount * 50;
  if (!binaryMatches && head.trimStart().startsWith('solid') && head.includes('facet')) {
    const text = new TextDecoder().decode(bytes);
    const numbers = [];
    const re = /vertex\\s+([-+0-9.eE]+)\\s+([-+0-9.eE]+)\\s+([-+0-9.eE]+)/g;
    let match;
    while ((match = re.exec(text)) !== null) {
      numbers.push(parseFloat(match[1]), parseFloat(match[2]), parseFloat(match[3]));
    }
    return new Float32Array(numbers);
  }
  const positions = new Float32Array(binaryCount * 9);
  let offset = 84;
  for (let i = 0; i < binaryCount; i++) {
    offset += 12; // facet normal
    for (let v = 0; v < 9; v++) { positions[i * 9 + v] = view.getFloat32(offset, true); offset += 4; }
    offset += 2; // attribute byte count
  }
  return positions;
}

async function positionsFor(url) {
  if (geometryCache.has(url)) return geometryCache.get(url);
  const response = await fetch(url);
  if (!response.ok) throw new Error('cannot load ' + url);
  const positions = parseStl(await response.arrayBuffer());
  if (positions.length < 9) throw new Error('empty mesh ' + url);
  geometryCache.set(url, positions);
  return positions;
}

function geometryFromPositions(positions) {
  let geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  return BGU.toCreasedNormals(geometry, THREE.MathUtils.degToRad(32));
}

// Connected shells of a triangle soup: triangles sharing a (quantised) vertex
// belong to one shell.  The same rule the sealed-mesh inspector uses.
function splitShells(positions) {
  const triangles = positions.length / 9;
  const ids = new Int32Array(triangles * 3);
  const lookup = new Map();
  let next = 0;
  for (let i = 0; i < triangles * 3; i++) {
    const key = (Math.round(positions[i * 3] * 1e4) + ',' + Math.round(positions[i * 3 + 1] * 1e4) + ',' + Math.round(positions[i * 3 + 2] * 1e4));
    let id = lookup.get(key);
    if (id === undefined) { id = next++; lookup.set(key, id); }
    ids[i] = id;
  }
  const parent = new Int32Array(next);
  for (let i = 0; i < next; i++) parent[i] = i;
  const find = (x) => { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; };
  const unite = (a, b) => { const ra = find(a), rb = find(b); if (ra !== rb) parent[rb] = ra; };
  for (let t = 0; t < triangles; t++) { unite(ids[t * 3], ids[t * 3 + 1]); unite(ids[t * 3], ids[t * 3 + 2]); }
  const groups = new Map();
  for (let t = 0; t < triangles; t++) {
    const root = find(ids[t * 3]);
    let list = groups.get(root);
    if (list === undefined) { list = []; groups.set(root, list); }
    list.push(t);
  }
  const shells = [];
  for (const list of groups.values()) {
    const shellPositions = new Float32Array(list.length * 9);
    let volume = 0;
    for (let n = 0; n < list.length; n++) {
      const t = list[n];
      for (let v = 0; v < 9; v++) shellPositions[n * 9 + v] = positions[t * 9 + v];
      const ax = positions[t * 9], ay = positions[t * 9 + 1], az = positions[t * 9 + 2];
      const bx = positions[t * 9 + 3], by = positions[t * 9 + 4], bz = positions[t * 9 + 5];
      const cx = positions[t * 9 + 6], cy = positions[t * 9 + 7], cz = positions[t * 9 + 8];
      volume += (ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)) / 6;
    }
    shells.push({ positions: shellPositions, volume: Math.abs(volume), triangles: list.length });
  }
  // File order of first triangle keeps the shell order deterministic.
  shells.sort((a, b) => a.first - b.first);
  return shells;
}

// Assign sealed part colours to shells by nearest relative volume; a shell
// no part explains keeps the base colour.  Ratios are reported so the
// evidence shows how confident each match was.
function assignShellColours(shells, shellColors) {
  const candidates = [];
  shells.forEach((shell, s) => {
    shellColors.forEach((part, p) => {
      if (shell.volume > 0) candidates.push({ s, p, cost: Math.abs(Math.log(shell.volume / part.volume)) });
    });
  });
  candidates.sort((a, b) => a.cost - b.cost || a.s - b.s || a.p - b.p);
  const shellPart = new Array(shells.length).fill(null);
  const used = new Set();
  for (const candidate of candidates) {
    if (shellPart[candidate.s] !== null || used.has(candidate.p) || candidate.cost > Math.log(1.5)) continue;
    shellPart[candidate.s] = candidate.p;
    used.add(candidate.p);
  }
  return shells.map((shell, s) => ({
    index: s,
    triangles: shell.triangles,
    volume: shell.volume,
    part: shellPart[s] === null ? null : shellColors[shellPart[s]].name,
    color: shellPart[s] === null ? null : shellColors[shellPart[s]].color,
    volume_ratio: shellPart[s] === null ? null : shell.volume / shellColors[shellPart[s]].volume,
  }));
}

function buildScene(definition) {
  const scene = new THREE.Scene();
  scene.environment = environment;
  const root = new THREE.Group();
  const cad = new THREE.Group();
  root.add(cad);
  scene.add(root);
  return { scene, root, cad };
}

async function renderView(spec, definition, background) {
  const { scene, root, cad } = buildScene(definition);
  const materialFor = (colour) => new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(colour), metalness: 0, roughness: 0.48,
    clearcoat: 0.25, clearcoatRoughness: 0.5, envMapIntensity: 0.7,
  });
  const shellReports = [];
  let triangles = 0;
  for (const part of definition.parts) {
    const positions = await positionsFor('/assets/' + part.stl);
    triangles += positions.length / 9;
    const pieces = [];
    if (Array.isArray(part.shell_colors)) {
      const shells = splitShells(positions);
      const report = assignShellColours(shells, part.shell_colors);
      shellReports.push({ stl: part.stl, shells: report });
      shells.forEach((shell, index) => {
        pieces.push({ positions: shell.positions, color: report[index].color || part.color });
      });
    } else {
      pieces.push({ positions, color: part.color });
    }
    for (const piece of pieces) {
      const mesh = new THREE.Mesh(geometryFromPositions(piece.positions), materialFor(piece.color));
      // Row-major CAD transform; never bake it into the shared cached mesh data.
      mesh.matrixAutoUpdate = false;
      mesh.matrix.set(...part.transform);
      mesh.castShadow = true; mesh.receiveShadow = true;
      cad.add(mesh);
    }
  }
  // CAD is Z up; three.js is Y up.
  cad.rotation.x = -Math.PI / 2;
  cad.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(cad);
  const size = new THREE.Vector3(); box.getSize(size);
  const center = new THREE.Vector3(); box.getCenter(center);
  root.position.set(-center.x, -box.min.y, -center.z);
  root.updateMatrixWorld(true);
  const R = Math.max(size.x, size.y, size.z, 1e-6);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(R * 40, R * 40), new THREE.ShadowMaterial({ opacity: 0.22 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const key = new THREE.DirectionalLight(0xfff4e6, 2.2);
  key.position.set(-1.2 * R, 2.4 * R, 1.6 * R); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048); key.shadow.radius = 4;
  const cam = key.shadow.camera; cam.left = cam.bottom = -R; cam.right = cam.top = R; cam.near = 0.1; cam.far = 10 * R;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xdde8ff, 0.7); fill.position.set(2 * R, 1.2 * R, -1 * R); scene.add(fill);
  const rim = new THREE.DirectionalLight(0xffffff, 0.9); rim.position.set(0.5 * R, 1.5 * R, -2.5 * R); scene.add(rim);
  const camera = new THREE.PerspectiveCamera(28, 1, 0.01 * R, 100 * R);
  const az = THREE.MathUtils.degToRad(spec.azimuth), el = THREE.MathUtils.degToRad(spec.elevation);
  const dist = (R * 0.62) / Math.tan(THREE.MathUtils.degToRad(14)) * 1.02;
  camera.position.set(dist * Math.cos(el) * Math.sin(az), dist * Math.sin(el), dist * Math.cos(el) * Math.cos(az));
  camera.lookAt(0, size.y * 0.42, 0);
  renderer.setSize(spec.size, spec.size, true);
  document.body.style.width = spec.size + 'px';
  document.body.style.height = spec.size + 'px';
  document.body.style.background = background;
  renderer.render(scene, camera);
  return { triangles, shells: shellReports };
}

window.__renderView = async (spec, definition, background) => {
  try {
    const info = await renderView(spec, definition, background);
    window.__result = { ok: true, ...info };
  } catch (error) {
    window.__result = { ok: false, error: String(error && error.message || error) };
  }
};
window.__ready = true;
`;

function pageHtml() {
  return `<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;overflow:hidden}canvas{display:block}</style>
<script type="importmap">{"imports":{"three":"/three/build/three.module.js","three/addons/":"/three/examples/jsm/"}}</script>
</head><body><canvas id="c" width="64" height="64"></canvas>
<script type="module">${PAGE_SCRIPT}</script></body></html>`;
}

function serve(assetRoot) {
  const server = http.createServer((request, response) => {
    const url = decodeURIComponent((request.url || '/').split('?')[0]);
    let file = null;
    if (url === '/') {
      response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      response.end(pageHtml());
      return;
    }
    if (url.startsWith('/three/')) file = path.join(THREE_ROOT, url.slice('/three/'.length));
    else if (url.startsWith('/assets/')) file = path.join(assetRoot, url.slice('/assets/'.length));
    if (file === null || file.includes('..')) { response.writeHead(404); response.end(); return; }
    const base = url.startsWith('/three/') ? THREE_ROOT : assetRoot;
    const resolved = path.resolve(file);
    if (!resolved.startsWith(path.resolve(base) + path.sep)) { response.writeHead(404); response.end(); return; }
    fs.stat(resolved, (error, stats) => {
      if (error || !stats.isFile() || stats.size > MAX_ASSET_BYTES) { response.writeHead(404); response.end(); return; }
      const type = resolved.endsWith('.js') ? 'text/javascript' : 'application/octet-stream';
      response.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' });
      fs.createReadStream(resolved).pipe(response);
    });
  });
  return server;
}

async function renderAll(scene, assetRoot, outDir) {
  validateScene(scene);
  fs.mkdirSync(outDir, { recursive: true });
  const server = serve(assetRoot);
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  const browser = await chromium.launch({
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-dev-shm-usage'],
  });
  const outputs = [];
  try {
    const context = await browser.newContext({ viewport: { width: 256, height: 256 } });
    await context.route('**/*', (route) => {
      const target = new URL(route.request().url());
      if (target.hostname === '127.0.0.1' && target.port === String(port)) return route.continue();
      return route.abort();
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(String(error.message || error)));
    await page.goto(`http://127.0.0.1:${port}/`);
    await page.waitForFunction(() => window.__ready === true, null, { timeout: VIEW_TIMEOUT_MS });
    for (const view of scene.views) {
      await page.setViewportSize({ width: view.size, height: view.size });
      await page.evaluate(() => { window.__result = undefined; });
      await page.evaluate(
        ([spec, definition, background]) => window.__renderView(spec, definition, background),
        [view, scene.scenes[view.scene], scene.background],
      );
      await page.waitForFunction(() => window.__result !== undefined, null, { timeout: VIEW_TIMEOUT_MS });
      const result = await page.evaluate(() => window.__result);
      if (!result || !result.ok) throw new Error('view ' + view.name + ' failed: ' + (result && result.error));
      const file = path.join(outDir, view.name + '.png');
      await page.screenshot({ path: file, clip: { x: 0, y: 0, width: view.size, height: view.size }, type: 'png' });
      outputs.push({ name: view.name, path: file, width: view.size, height: view.size, triangles: result.triangles, shells: result.shells });
    }
    if (errors.length) throw new Error('page errors: ' + errors.join('; '));
    return { ok: true, outputs, three: JSON.parse(fs.readFileSync(path.join(THREE_ROOT, 'package.json'), 'utf8')).version, chromium: browser.version(), node: process.version };
  } finally {
    await browser.close();
    server.close();
  }
}

function selfCheckScene(dir) {
  // A unit cube as binary STL: 12 triangles.
  const faces = [];
  const quad = (a, b, c, d) => { faces.push([a, b, c], [a, c, d]); };
  const p = (x, y, z) => [x, y, z];
  quad(p(0, 0, 0), p(0, 1, 0), p(1, 1, 0), p(1, 0, 0));
  quad(p(0, 0, 1), p(1, 0, 1), p(1, 1, 1), p(0, 1, 1));
  quad(p(0, 0, 0), p(1, 0, 0), p(1, 0, 1), p(0, 0, 1));
  quad(p(0, 1, 0), p(0, 1, 1), p(1, 1, 1), p(1, 1, 0));
  quad(p(0, 0, 0), p(0, 0, 1), p(0, 1, 1), p(0, 1, 0));
  quad(p(1, 0, 0), p(1, 1, 0), p(1, 1, 1), p(1, 0, 1));
  const buffer = Buffer.alloc(84 + faces.length * 50);
  buffer.writeUInt32LE(faces.length, 80);
  let offset = 84;
  for (const face of faces) {
    offset += 12;
    for (const vertex of face) for (const value of vertex) { buffer.writeFloatLE(value * 20, offset); offset += 4; }
    offset += 2;
  }
  fs.writeFileSync(path.join(dir, 'cube.stl'), buffer);
  return {
    schema_version: 1,
    background: '#f5f0e6',
    views: [{ name: 'self-check', azimuth: 35, elevation: 26, size: 256, scene: 'cube' }],
    scenes: { cube: { parts: [{ stl: 'cube.stl', color: '#d1822e', transform: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1] }] } },
  };
}

async function main() {
  const [first, second] = process.argv.slice(2);
  if (!first || !second) fail('usage: render_scene.mjs <scene.json>|--self-check <out_dir>');
  let scene;
  let assetRoot;
  if (first === '--self-check') {
    assetRoot = path.resolve(second);
    fs.mkdirSync(assetRoot, { recursive: true });
    scene = selfCheckScene(assetRoot);
  } else {
    const scenePath = path.resolve(first);
    const raw = fs.readFileSync(scenePath, 'utf8');
    if (raw.length > 8 * 1024 * 1024) fail('scene file is too large');
    scene = JSON.parse(raw);
    assetRoot = path.dirname(scenePath);
  }
  const summary = await renderAll(scene, assetRoot, path.resolve(second));
  process.stdout.write(JSON.stringify(summary) + '\n');
}

main().catch((error) => fail(error && error.stack ? error.stack.split('\n')[0] : error));
