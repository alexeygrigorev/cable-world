import "./style.css";
import initialData from "./data/hex_map.json";

// the game's label font (scripts/map_panel.gd loads the same TTF)
const LABEL_FONT = "MapLabel";
new FontFace(LABEL_FONT, "url(/asset/LiberationSerif-BoldItalic.ttf)")
  .load()
  .then((ff) => { document.fonts.add(ff); render(); })
  .catch(() => {});

const SQRT3 = Math.sqrt(3);
// exact game palette (map_pipeline/compose_map.py + scripts/map_panel.gd)
const COLORS = {
  sea: "#315f6d",        // OCEAN
  landDE: "#9da05a",     // GERMANY_LAND
  landOther: "#8f9150",  // NEIGHBOR_LAND
  edge: "rgba(40,33,18,0.22)",
  outline: "#463c28",    // GERMANY_EDGE
  labelFill: "#f6df9b",  // city label text in the game
  labelStroke: "rgba(28,18,8,0.9)",
};
const ZOOM_LEVELS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0];

let state = structuredClone(initialData);
const canvas = document.getElementById("map");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");
const zoomValEl = document.getElementById("zoomVal");

// camera: fit-to-view at 100%, then user zoom on top, plus pan in CSS px
let zoomIdx = 2; // 1.0
let panX = 0, panY = 0;
let cssW = 0, cssH = 0, fitScale = 1;

const sizeW = () => state.grid.hex_size_px; // world px
const origin = () => state.view.origin;

// ----- hex math (pointy-top, axial q,r) in world px -----
function hexToContent(q, r) {
  const s = sizeW(), o = origin();
  return { x: s * SQRT3 * (q + r / 2) - o[0], y: s * 1.5 * r - o[1] };
}

function contentToHex(x, y) {
  const s = sizeW(), o = origin();
  const wx = x + o[0], wy = y + o[1];
  const qf = ((SQRT3 / 3) * wx - (1 / 3) * wy) / s;
  const rf = ((2 / 3) * wy) / s;
  let cx = qf, cz = rf, cy = -cx - cz;
  let rx = Math.round(cx), ry = Math.round(cy), rz = Math.round(cz);
  const dx = Math.abs(rx - cx), dy = Math.abs(ry - cy), dz = Math.abs(rz - cz);
  if (dx > dy && dx > dz) rx = -ry - rz;
  else if (dy > dz) ry = -rx - rz;
  else rz = -rx - ry;
  return { q: rx, r: rz };
}

function hexPath(cx, cy, s) {
  ctx.beginPath();
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI / 180) * (60 * i - 30);
    i === 0
      ? ctx.moveTo(cx + s * Math.cos(a), cy + s * Math.sin(a))
      : ctx.lineTo(cx + s * Math.cos(a), cy + s * Math.sin(a));
  }
  ctx.closePath();
}

function cellColor(cell) {
  // forests/mountains are glyphs on land, like the game — land color underneath
  if (cell.terrain === "sea") return COLORS.sea;
  return cell.country === "DE" ? COLORS.landDE : COLORS.landOther;
}

// ----- glyphs (save/restore so they never leak style into the grid) -----
function drawTree(cx, cy, s) {
  ctx.save();
  ctx.fillStyle = "#4e7a3f";
  ctx.beginPath();
  ctx.moveTo(cx, cy - s * 0.55);
  ctx.lineTo(cx + s * 0.4, cy + s * 0.3);
  ctx.lineTo(cx - s * 0.4, cy + s * 0.3);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = "#6a4a2a";
  ctx.fillRect(cx - s * 0.06, cy + s * 0.3, s * 0.12, s * 0.22);
  ctx.restore();
}

function drawPeak(cx, cy, s) {
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(cx, cy - s * 0.62);
  ctx.lineTo(cx + s * 0.55, cy + s * 0.45);
  ctx.lineTo(cx - s * 0.55, cy + s * 0.45);
  ctx.closePath();
  ctx.fillStyle = "#8a7d6b";
  ctx.fill();
  ctx.strokeStyle = "#5b5142";
  ctx.lineWidth = s * 0.04;
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(cx, cy - s * 0.62);
  ctx.lineTo(cx + s * 0.16, cy - s * 0.18);
  ctx.lineTo(cx - s * 0.16, cy - s * 0.18);
  ctx.closePath();
  ctx.fillStyle = "#f4f4f4";
  ctx.fill();
  ctx.restore();
}

// terrain glyph sets from the game (varied per hex by a stable hash)
const FOREST_GLYPHS = ["forest_cluster_1.png", "forest_cluster_2.png", "forest_cluster_3.png",
  "forest_cluster_4.png", "forest_cluster_5.png", "forest_cluster_6.png"];
const MOUNTAIN_GLYPHS = ["alps_peak_1.png", "alps_peak_2.png", "alps_range_1.png", "alps_range_2.png"];

function hashKey(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
function variant(key, arr) { return arr[hashKey(key) % arr.length]; }

// coalesce repaints (many image onloads -> one render per frame)
let renderQueued = false;
function requestRender() {
  if (renderQueued) return;
  renderQueued = true;
  requestAnimationFrame(() => { renderQueued = false; render(); });
}

// real game sprites, loaded on demand and cached (HTTP-cached too)
const imgCache = new Map();
function getImg(name) {
  if (imgCache.has(name)) return imgCache.get(name);
  const img = new Image();
  img.decoding = "async";
  img.onload = requestRender;
  img.src = `/asset/${name}`;
  imgCache.set(name, img);
  return img;
}

// which hexes a massif actually paints (sampling the image's alpha), so points
// land only where there's real art — not on transparent edges of the bbox.
const alphaData = new Map();   // image name -> ImageData
const filledCache = new Map(); // feature id -> { bkey, keys }
const SAMPLE = [[0, 0], [0.45, 0], [-0.45, 0], [0, 0.5], [0, -0.5], [0.35, 0.35], [-0.35, -0.35]];

function massifFilledKeys(f) {
  const img = getImg(f.image);
  if (!img.complete || !img.naturalWidth) return null; // not loaded yet
  const bkey = f.bounds_px.join(",");
  const cached = filledCache.get(f.id);
  if (cached && cached.bkey === bkey) return cached.keys;

  let data = alphaData.get(f.image);
  if (!data) {
    const oc = document.createElement("canvas");
    oc.width = img.naturalWidth;
    oc.height = img.naturalHeight;
    const octx = oc.getContext("2d", { willReadFrequently: true });
    octx.drawImage(img, 0, 0);
    data = octx.getImageData(0, 0, oc.width, oc.height);
    alphaData.set(f.image, data);
  }

  const [x0, y0, x1, y1] = f.bounds_px;
  const W = x1 - x0, H = y1 - y0, s = sizeW();
  const keys = [];
  for (const key in state.hexes) {
    const [q, r] = key.split(",").map(Number);
    const wx = s * SQRT3 * (q + r / 2), wy = s * 1.5 * r;
    if (wx < x0 || wx > x1 || wy < y0 || wy > y1) continue; // outside the glyph box
    let opaque = 0;
    for (const [ox, oy] of SAMPLE) {
      const ix = Math.round(((wx + ox * s - x0) / W) * data.width);
      const iy = Math.round(((wy + oy * s - y0) / H) * data.height);
      if (ix < 0 || iy < 0 || ix >= data.width || iy >= data.height) continue;
      if (data.data[(iy * data.width + ix) * 4 + 3] > 50) opaque++;
    }
    if (opaque / SAMPLE.length >= 0.6) keys.push(key); // hex mostly covered by art
  }
  filledCache.set(f.id, { bkey, keys });
  return keys;
}

// warm the cache for everything on the map so panning never pops in
function preloadAssets() {
  for (const f of state.features || []) {
    if (f.glyph === "city" && f.icon) getImg(`city_${f.icon}.png`);
    else if (f.glyph === "massif" && f.image) getImg(f.image);
  }
  for (const g of [...FOREST_GLYPHS]) getImg(g);
}

function drawTransport(cx, cy, s, f, showLabel) {
  ctx.save();
  const img = f.icon ? getImg(`icon_${f.icon}.png`) : null;
  let bottom;
  if (img && img.complete && img.naturalWidth) {
    const h = s * 2.0;
    const w = h * (img.naturalWidth / img.naturalHeight);
    ctx.drawImage(img, cx - w / 2, cy - h * 0.72, w, h);
    bottom = cy + h * 0.28;
  } else {
    ctx.beginPath();
    ctx.arc(cx, cy, s * 0.4, 0, Math.PI * 2);
    ctx.fillStyle = "#2e7d32";
    ctx.fill();
    ctx.lineWidth = s * 0.06;
    ctx.strokeStyle = "#fff";
    ctx.stroke();
    bottom = cy + s * 0.4;
  }
  if (f.label && showLabel) {
    const ly = bottom - s * 0.4;
    ctx.font = `${(s * 0.85).toFixed(1)}px "${LABEL_FONT}", serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.lineJoin = "round";
    ctx.lineWidth = s * 0.2;
    ctx.strokeStyle = COLORS.labelStroke;
    ctx.strokeText(f.label, cx, ly);
    ctx.fillStyle = COLORS.labelFill;
    ctx.fillText(f.label, cx, ly);
  }
  ctx.restore();
}

// draw a game sprite; baseAnchor=true sits its base on the hex, else centered.
// returns false if the image isn't ready yet (caller draws a fallback).
function drawSprite(name, cx, cy, s, h, baseAnchor) {
  const img = getImg(name);
  if (!img.complete || !img.naturalWidth) return false;
  const w = h * (img.naturalWidth / img.naturalHeight);
  const top = baseAnchor ? cy - h * 0.78 : cy - h / 2;
  ctx.drawImage(img, cx - w / 2, top, w, h);
  return true;
}

function drawCity(cx, cy, s, f, showLabel) {
  ctx.save();
  const capital = f.kind === "capital";
  const img = f.icon ? getImg(`city_${f.icon}.png`) : null;
  let bottom = cy;
  if (img && img.complete && img.naturalWidth) {
    // sprite footprint scaled to the hex; anchored so its base sits on the hex
    const h = s * (capital ? 5.0 : 4.0);
    const w = h * (img.naturalWidth / img.naturalHeight);
    ctx.drawImage(img, cx - w / 2, cy - h * 0.70, w, h); // anchor point sits higher in the sprite
    bottom = cy + h * 0.30;
  } else {
    const r = s * (capital ? 0.5 : 0.38);
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle = capital ? "#c0392b" : "#34495e";
    ctx.fill();
    ctx.lineWidth = s * 0.06;
    ctx.strokeStyle = "#fff";
    ctx.stroke();
    bottom = cy + r;
  }
  if (f.label && showLabel) {
    const ly = bottom - s * 0.55; // tucked closer under the city
    ctx.font = `${(s * 0.95).toFixed(1)}px "${LABEL_FONT}", serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.lineJoin = "round";
    ctx.lineWidth = s * 0.22;
    ctx.strokeStyle = COLORS.labelStroke;
    ctx.strokeText(f.label, cx, ly);
    ctx.fillStyle = COLORS.labelFill;
    ctx.fillText(f.label, cx, ly);
  }
  ctx.restore();
}

// ----- camera / rendering -----
function computeFit() {
  const rect = canvas.getBoundingClientRect();
  cssW = rect.width;
  cssH = rect.height;
  const [fw, fh] = state.focus.size; // 100% = same Germany geo_bounds as the game
  // COVER fit, matching the game's _map_base_size_for_viewport (fills the viewport)
  fitScale = Math.max(cssW / fw, cssH / fh);
}

function setupCanvas() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  computeFit();
  canvas.width = cssW * dpr;
  canvas.height = cssH * dpr;
}

function scale() {
  return fitScale * ZOOM_LEVELS[zoomIdx];
}

// content-space center of the Germany focus box
function focusCenter() {
  const o = origin(), f = state.focus;
  return { x: f.origin[0] - o[0] + f.size[0] / 2, y: f.origin[1] - o[1] + f.size[1] / 2 };
}

// keep the screen-center within the Europe extent (+margin) at any zoom
function clampPan(fc, sc) {
  const [vw, vh] = state.view.size;
  const m = 300;
  let cx = fc.x - panX / sc, cy = fc.y - panY / sc;
  cx = Math.max(-m, Math.min(vw + m, cx));
  cy = Math.max(-m, Math.min(vh + m, cy));
  panX = (fc.x - cx) * sc;
  panY = (fc.y - cy) * sc;
}

function camera() {
  const sc = scale();
  const fc = focusCenter();
  clampPan(fc, sc);
  const tx = cssW / 2 - fc.x * sc + panX;
  const ty = cssH / 2 - fc.y * sc + panY;
  return { sc, tx, ty };
}

function render() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const { sc, tx, ty } = camera();
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = COLORS.sea;
  ctx.fillRect(0, 0, cssW, cssH);
  ctx.translate(tx, ty);
  ctx.scale(sc, sc);

  const s = sizeW();
  // visible content rect (for culling) + margin
  const vx0 = -tx / sc - s, vy0 = -ty / sc - s;
  const vx1 = (cssW - tx) / sc + s, vy1 = (cssH - ty) / sc + s;

  const onScreen = (x, y) => x >= vx0 && x <= vx1 && y >= vy0 && y <= vy1;

  // 1. land/sea fill
  for (const [key, cell] of Object.entries(state.hexes)) {
    const [q, r] = key.split(",").map(Number);
    const { x, y } = hexToContent(q, r);
    if (!onScreen(x, y)) continue;
    hexPath(x, y, s);
    ctx.fillStyle = cellColor(cell);
    ctx.fill();
    ctx.strokeStyle = COLORS.edge;
    ctx.lineWidth = s * 0.03;
    ctx.stroke();
  }

  // 2. country borders: edge between two land hexes of different countries
  ctx.strokeStyle = COLORS.outline;
  ctx.lineWidth = s * 0.14;
  ctx.lineCap = "round";
  const apothem = (s * SQRT3) / 2;
  for (const [key, cell] of Object.entries(state.hexes)) {
    const [q, r] = key.split(",").map(Number);
    const { x, y } = hexToContent(q, r);
    if (!onScreen(x, y)) continue;
    for (const [dq, dr] of NB) {
      const ncell = state.hexes[`${q + dq},${r + dr}`];
      if (!ncell || ncell.country === cell.country) continue;
      if (`${q + dq},${r + dr}` < key) continue; // draw each border once
      const n = hexToContent(q + dq, r + dr);
      const ux = n.x - x, uy = n.y - y;
      const len = Math.hypot(ux, uy) || 1;
      const mx = x + (ux / len) * apothem, my = y + (uy / len) * apothem;
      const px = -uy / len, py = ux / len;
      ctx.beginPath();
      ctx.moveTo(mx + px * (s / 2), my + py * (s / 2));
      ctx.lineTo(mx - px * (s / 2), my - py * (s / 2));
      ctx.stroke();
    }
  }

  // 3. multi-hex massif glyphs (each its own image, placed by geo_bounds)
  for (const f of state.features || []) {
    if (f.glyph !== "massif" || !f.image) continue;
    const img = getImg(f.image);
    if (!img.complete || !img.naturalWidth) continue;
    const held = f === dragging?.feature;
    const d = held && dragging.delta ? hexDeltaWorld(dragging.delta.dq, dragging.delta.dr) : { x: 0, y: 0 };
    const [x0, y0, x1, y1] = f.bounds_px;
    ctx.globalAlpha = held ? 0.6 : 1;
    ctx.drawImage(img, x0 - origin()[0] + d.x, y0 - origin()[1] + d.y, x1 - x0, y1 - y0);
    ctx.globalAlpha = 1;
  }

  // 3b. forest bundles: a cluster of forest glyphs over the hexes it covers
  for (const f of state.features || []) {
    if (f.glyph !== "forest") continue;
    const held = f === dragging?.feature;
    const dd = held && dragging.delta ? dragging.delta : { dq: 0, dr: 0 };
    ctx.globalAlpha = held ? 0.6 : 1;
    for (const k of f.cells || []) {
      const [q, r] = shiftKey(k, dd.dq, dd.dr).split(",").map(Number);
      const { x, y } = hexToContent(q, r);
      if (!onScreen(x, y)) continue;
      if (!drawSprite(variant(k, FOREST_GLYPHS), x, y, s, s * 1.9, false)) drawTree(x, y, s);
    }
    ctx.globalAlpha = 1;
  }

  // 5. point objects (cities + transport) on top, south-over-north
  const showLabels = s * sc > 13;
  const points = (state.features || [])
    .filter((f) => f.glyph === "city" || f.glyph === "transport")
    .map((f) => {
      const held = f === dragging?.feature;
      return { f, held, pos: held && dragPos ? dragPos : anchorContent(f) };
    })
    .sort((a, b) => a.pos.y - b.pos.y);
  for (const { f, held, pos } of points) {
    if (!onScreen(pos.x, pos.y)) continue;
    if (held) ctx.globalAlpha = 0.5;
    if (f.glyph === "city") drawCity(pos.x, pos.y, s, f, showLabels);
    else drawTransport(pos.x, pos.y, s, f, showLabels);
    ctx.globalAlpha = 1;
  }

  // 5b. occupied-hex points of the selected (or dragged) feature, drawn on top
  //     so they're visible even under a city/transport sprite
  const hi = dragging && dragPos ? dragging.feature : selected;
  if (hi) {
    let keys;
    const d = dragging?.feature === hi && dragging.delta ? dragging.delta : { dq: 0, dr: 0 };
    if (hi.glyph === "massif") {
      let filled = massifFilledKeys(hi); // points only where the art covers a hex
      if (!filled || filled.length === 0) filled = [hi.anchor];
      keys = filled.map((k) => shiftKey(k, d.dq, d.dr));
    } else if (hi.glyph === "forest") {
      keys = (hi.cells || []).map((k) => shiftKey(k, d.dq, d.dr));
    } else if (dragging?.feature === hi && dragPos) {
      const { q, r } = contentToHex(dragPos.x, dragPos.y);
      keys = [`${q},${r}`];
    } else {
      keys = [hi.anchor];
    }
    for (const k of keys) {
      const [q, r] = k.split(",").map(Number);
      const c = hexToContent(q, r);
      ctx.beginPath();
      ctx.arc(c.x, c.y, s * 0.2, 0, Math.PI * 2);
      ctx.fillStyle = "#1e88e5";
      ctx.fill();
      ctx.lineWidth = s * 0.06;
      ctx.strokeStyle = "#fff";
      ctx.stroke();
    }
  }

  // 6. ghost while dragging a new item from the palette
  if (placing && placeGhost) {
    const { q, r } = contentToHex(placeGhost.x, placeGhost.y);
    const c = hexToContent(q, r);
    hexPath(c.x, c.y, s);
    ctx.fillStyle = "rgba(30,136,229,0.28)";
    ctx.fill();
    ctx.strokeStyle = "#1e88e5";
    ctx.lineWidth = s * 0.1;
    ctx.stroke();
    ctx.globalAlpha = 0.7;
    if (placing.kind === "forest") {
      if (!drawSprite(FOREST_GLYPHS[0], c.x, c.y, s, s * 1.9, false)) drawTree(c.x, c.y, s);
    } else {
      drawTransport(c.x, c.y, s, { icon: placing.icon }, false);
    }
    ctx.globalAlpha = 1;
  }
}

const NB = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, -1], [-1, 1]];

function anchorContent(f) {
  const [q, r] = f.anchor.split(",").map(Number);
  return hexToContent(q, r);
}

function shiftKey(key, dq, dr) {
  const [q, r] = key.split(",").map(Number);
  return `${q + dq},${r + dr}`;
}

// a hex is "fully filled" by a massif when nearly all its neighbours are also
// mountain; an edge hex where the glyph only just spills over is not
function isFilledMountain(key) {
  const [q, r] = key.split(",").map(Number);
  let n = 0;
  for (const [dq, dr] of NB) {
    const c = state.hexes[`${q + dq},${r + dr}`];
    if (c && c.terrain === "mountain") n++;
  }
  return n >= 5;
}

function hexDeltaWorld(dq, dr) {
  const s = sizeW();
  return { x: s * SQRT3 * (dq + dr / 2), y: s * 1.5 * dr };
}

// ----- selection + info panel -----
let selected = null;
let moveEnabled = false; // objects are locked by default; toggle to drag them
const panelEl = document.getElementById("panel");
const panelBody = document.getElementById("panelBody");
const panelDeleteBtn = document.getElementById("panelDelete");
const panelResetBtn = document.getElementById("panelReset");
document.getElementById("panelClose").addEventListener("click", deselect);
panelDeleteBtn.addEventListener("click", deleteSelected);
panelResetBtn.addEventListener("click", resetSelected);

function deselect() {
  selected = null;
  panelEl.hidden = true;
  render();
}

function updatePanelButtons(f) {
  panelDeleteBtn.hidden = !f.user; // user objects: delete
  // reset only for a system GEOGRAPHIC object (city/massif) moved off its home;
  // forests aren't tied to real coords, so position doesn't matter for them
  const geographic = f.glyph === "city" || f.glyph === "massif";
  panelResetBtn.hidden = !(!f.user && geographic && f.home && f.anchor !== f.home);
}

function selectFeature(f) {
  selected = f;
  renderPanel(f);
  panelEl.hidden = false;
  updatePanelButtons(f);
  render(); // show the occupied-hex points right away
}

function deleteSelected() {
  if (!selected || !selected.user) return; // system objects are protected
  pushUndo();
  state.features = state.features.filter((x) => x !== selected);
  deselect();
  save();
}

// snap a system object back to its original (real-world-derived) position
function resetSelected() {
  const f = selected;
  if (!f || f.user || !f.home) return;
  const [hq, hr] = f.home.split(",").map(Number);
  const [aq, ar] = f.anchor.split(",").map(Number);
  const dq = hq - aq, dr = hr - ar;
  if (dq || dr) {
    pushUndo();
    f.anchor = f.home;
    if (f.cells) f.cells = f.cells.map((k) => shiftKey(k, dq, dr));
    if (f.bounds_px) {
      const d = hexDeltaWorld(dq, dr);
      f.bounds_px = [f.bounds_px[0] + d.x, f.bounds_px[1] + d.y, f.bounds_px[2] + d.x, f.bounds_px[3] + d.y];
    }
    save();
  }
  renderPanel(f);
  updatePanelButtons(f);
  render();
}

function renderPanel(f) {
  if (f.glyph === "city") {
    panelBody.innerHTML = `
      <h2>${f.label}</h2>
      <div class="kind">${f.kind === "capital" ? "Столица" : "Город"}</div>
      <dl>
        <dt>Тип</dt><dd>город</dd>
        <dt>id</dt><dd>${f.id}</dd>
        <dt>Координаты</dt><dd>${(f.lat ?? 0).toFixed(4)}, ${(f.lon ?? 0).toFixed(4)}</dd>
        <dt>Гекс</dt><dd>${f.anchor}</dd>
        <dt>Иконка</dt><dd>city_${f.icon}.png</dd>
      </dl>`;
  } else if (f.glyph === "massif") {
    panelBody.innerHTML = `
      <h2>${f.label}</h2>
      <div class="kind">Горный массив</div>
      <img class="thumb" src="/asset/${f.image}" alt="">
      <dl>
        <dt>Тип</dt><dd>массив (горы)</dd>
        <dt>id</dt><dd>${f.id}</dd>
        <dt>Занято гексов</dt><dd>${(f.cells || []).length}</dd>
        <dt>Якорь</dt><dd>${f.anchor}</dd>
        <dt>Картинка</dt><dd>${f.image}</dd>
      </dl>`;
  } else if (f.glyph === "forest") {
    panelBody.innerHTML = `
      <h2>Лес</h2>
      <div class="kind">Лесной массив</div>
      <dl>
        <dt>Тип</dt><dd>лес (пучок)</dd>
        <dt>id</dt><dd>${f.id}</dd>
        <dt>Гексов</dt><dd>${(f.cells || []).length}</dd>
        <dt>Якорь</dt><dd>${f.anchor}</dd>
      </dl>`;
  } else if (f.glyph === "transport") {
    panelBody.innerHTML = `
      <h2>${f.label || "Объект"}</h2>
      <div class="kind">Транспортный объект</div>
      <img class="thumb" src="/asset/icon_${f.icon}.png" alt="">
      <dl>
        <dt>Тип</dt><dd>${TRANSPORT_LABELS[f.icon] || f.icon}</dd>
        <dt>id</dt><dd>${f.id}</dd>
        <dt>Координаты</dt><dd>${(f.lat ?? 0).toFixed(4)}, ${(f.lon ?? 0).toFixed(4)}</dd>
        <dt>Гекс</dt><dd>${f.anchor}</dd>
      </dl>`;
  }
}

// ----- pointer: drag feature, or pan -----
let dragging = null, dragPos = null, panning = null, dragMoved = false;

function eventToContent(e) {
  const rect = canvas.getBoundingClientRect();
  const { sc, tx, ty } = camera();
  return { x: (e.clientX - rect.left - tx) / sc, y: (e.clientY - rect.top - ty) / sc };
}

function featureAt(p) {
  const s = sizeW(), o = origin();
  // point objects first (cities + transport sit on top)
  for (const f of state.features || []) {
    if (f.glyph !== "city" && f.glyph !== "transport") continue;
    const c = anchorContent(f);
    if (Math.hypot(p.x - c.x, p.y - c.y) < s * 0.9) return f;
  }
  // forests: pointer over any of the bundle's hexes
  const ph = contentToHex(p.x, p.y);
  const pk = `${ph.q},${ph.r}`;
  for (const f of state.features || []) {
    if (f.glyph === "forest" && (f.cells || []).includes(pk)) return f;
  }
  // massifs by their footprint box
  for (const f of state.features || []) {
    if (f.glyph !== "massif" || !f.bounds_px) continue;
    const [x0, y0, x1, y1] = f.bounds_px;
    if (p.x >= x0 - o[0] && p.x <= x1 - o[0] && p.y >= y0 - o[1] && p.y <= y1 - o[1]) return f;
  }
  return null;
}

const isMultiHex = (f) => f.glyph === "massif" || f.glyph === "forest";

canvas.addEventListener("pointerdown", (e) => {
  const p = eventToContent(e);
  const f = featureAt(p);
  // user-added (palette) objects are always editable; base-map objects only
  // when the lock is open
  if (f && (f.user || moveEnabled)) {
    // move mode: drag the feature
    dragging = { feature: f, start: { x: e.clientX, y: e.clientY } };
    dragMoved = false;
    dragPos = p;
    if (isMultiHex(f)) {
      dragging.pickHex = contentToHex(p.x, p.y);
      dragging.delta = { dq: 0, dr: 0 };
    }
    selectFeature(f);
    render();
  } else {
    // locked (default): click selects, the object stays put; drag pans the map
    if (f) selectFeature(f);
    else if (selected) deselect();
    panning = { x: e.clientX, y: e.clientY, panX, panY };
  }
  canvas.setPointerCapture(e.pointerId);
});

canvas.addEventListener("pointermove", (e) => {
  if (dragging) {
    if (!dragMoved && Math.hypot(e.clientX - dragging.start.x, e.clientY - dragging.start.y) > 4) {
      pushUndo();
      dragMoved = true;
    }
    dragPos = eventToContent(e);
    if (isMultiHex(dragging.feature)) {
      const h = contentToHex(dragPos.x, dragPos.y);
      dragging.delta = { dq: h.q - dragging.pickHex.q, dr: h.r - dragging.pickHex.r };
    }
    render();
  } else if (panning) {
    panX = panning.panX + (e.clientX - panning.x);
    panY = panning.panY + (e.clientY - panning.y);
    render();
  }
});

canvas.addEventListener("pointerup", () => {
  if (dragging) {
    const f = dragging.feature;
    if (dragMoved) {
      if (isMultiHex(f)) {
        const { dq, dr } = dragging.delta || { dq: 0, dr: 0 };
        if (dq || dr) {
          f.anchor = shiftKey(f.anchor, dq, dr);
          f.cells = (f.cells || []).map((k) => shiftKey(k, dq, dr));
          if (f.bounds_px) {
            const d = hexDeltaWorld(dq, dr);
            f.bounds_px = [f.bounds_px[0] + d.x, f.bounds_px[1] + d.y,
                           f.bounds_px[2] + d.x, f.bounds_px[3] + d.y];
          }
        }
      } else {
        const { q, r } = contentToHex(dragPos.x, dragPos.y);
        f.anchor = `${q},${r}`;
        // user objects adopt the hex's real coords; base objects keep their
        // canonical real-world lon/lat so "reset" stays meaningful
        if (f.user) {
          const cell = state.hexes[`${q},${r}`];
          if (cell?.center) { f.lon = cell.center[0]; f.lat = cell.center[1]; }
        }
      }
      if (selected === f) { renderPanel(f); updatePanelButtons(f); }
      save();
    }
    dragging = null; dragPos = null;
    render();
  }
  panning = null;
});

// ----- zoom -----
function setZoom(idx) {
  zoomIdx = Math.max(0, Math.min(ZOOM_LEVELS.length - 1, idx));
  zoomValEl.textContent = `${Math.round(ZOOM_LEVELS[zoomIdx] * 100)}%`;
  render();
}
document.getElementById("zoomIn").addEventListener("click", () => setZoom(zoomIdx + 1));
document.getElementById("zoomOut").addEventListener("click", () => setZoom(zoomIdx - 1));
// wheel/trackpad pans the map (zoom is only via the +/- buttons)
canvas.addEventListener("wheel", (e) => {
  e.preventDefault();
  panX -= e.deltaX;
  panY -= e.deltaY;
  render();
}, { passive: false });

// ----- undo -----
const undoStack = [];
function pushUndo() {
  undoStack.push(JSON.stringify(state.features));
  if (undoStack.length > 100) undoStack.shift();
}
function undo() {
  if (!undoStack.length) return;
  state.features = JSON.parse(undoStack.pop());
  selected = null;          // old reference is gone after restore
  panelEl.hidden = true;
  render();
  save();
}
document.getElementById("undo").addEventListener("click", undo);
window.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") { e.preventDefault(); undo(); }
  else if ((e.key === "Delete" || e.key === "Backspace") && selected?.user) { e.preventDefault(); deleteSelected(); }
});

// ----- move toggle (objects locked by default) -----
const moveBtn = document.getElementById("moveToggle");
moveBtn.addEventListener("click", () => {
  moveEnabled = !moveEnabled;
  moveBtn.textContent = moveEnabled ? "🔓 базовая карта" : "🔒 базовая карта";
  moveBtn.classList.toggle("on", moveEnabled);
  if (selected) updatePanelButtons(selected);
});

// ----- palette + drag-to-place -----
const TRANSPORT_LABELS = {
  cable_gondola: "Гондольная канатка",
  aerial_tram: "Маятниковая канатка",
  funicular: "Фуникулёр",
  cog_railway: "Зубчатая ж/д",
  chairlift: "Кресельная дорога",
  elevator: "Лифт",
  suspended_monorail: "Подвесной монорельс",
};
const PALETTE = [
  { kind: "forest", label: "Лес", emoji: "🌲" },
  { kind: "transport", icon: "cable_gondola", label: "Канатка" },
  { kind: "transport", icon: "aerial_tram", label: "Маятниковая" },
  { kind: "transport", icon: "funicular", label: "Фуникулёр" },
  { kind: "transport", icon: "cog_railway", label: "Зубчатая ж/д" },
  { kind: "transport", icon: "chairlift", label: "Кресельная" },
  { kind: "transport", icon: "elevator", label: "Лифт" },
  { kind: "transport", icon: "suspended_monorail", label: "Монорельс" },
];

let placing = null, placeGhost = null, nextId = 1;

(function buildPalette() {
  const host = document.getElementById("paletteItems");
  for (const p of PALETTE) {
    const el = document.createElement("div");
    el.className = "palette-item";
    el.innerHTML = (p.icon ? `<img src="/asset/icon_${p.icon}.png" alt="">`
      : `<span class="swatch">${p.emoji || "▩"}</span>`) + `<span>${p.label}</span>`;
    el.addEventListener("pointerdown", (e) => { e.preventDefault(); placing = p; placeGhost = null; });
    host.appendChild(el);
  }
})();

function clientToContent(clientX, clientY) {
  const rect = canvas.getBoundingClientRect();
  if (clientX < rect.left || clientX > rect.right || clientY < rect.top || clientY > rect.bottom) return null;
  const { sc, tx, ty } = camera();
  return { x: (clientX - rect.left - tx) / sc, y: (clientY - rect.top - ty) / sc };
}

window.addEventListener("pointermove", (e) => {
  if (!placing) return;
  placeGhost = clientToContent(e.clientX, e.clientY);
  render();
});
window.addEventListener("pointerup", (e) => {
  if (!placing) return;
  const pos = clientToContent(e.clientX, e.clientY);
  if (pos) placeFeature(placing, contentToHex(pos.x, pos.y));
  placing = null; placeGhost = null;
  render();
});

function placeFeature(p, hex) {
  const key = `${hex.q},${hex.r}`;
  const cell = state.hexes[key];
  pushUndo();
  let f;
  if (p.kind === "forest") {
    f = { id: `forest-new-${nextId++}`, glyph: "forest", label: "Лес", cells: [key], anchor: key, user: true };
  } else {
    f = { id: `${p.icon}-${nextId++}`, glyph: "transport", icon: p.icon, label: p.label,
          anchor: key, lon: cell?.center?.[0], lat: cell?.center?.[1], user: true };
  }
  state.features.push(f);
  selectFeature(f);
  render();
  save();
}

// ----- save (writes the working hex_map.json; restorable via the generator) -----
const saveBtn = document.getElementById("saveBtn");
saveBtn.addEventListener("click", async () => {
  const res = await fetch("/__save", { method: "POST", body: JSON.stringify(state) });
  const old = saveBtn.textContent;
  saveBtn.textContent = res.ok ? "✓ сохранено" : "✕ ошибка";
  setTimeout(() => { saveBtn.textContent = old; }, 1200);
});

// ----- persistence -----
let saveTimer = null;
function save() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    fetch("/__save", { method: "POST", body: JSON.stringify(state) }).catch(() => {});
  }, 150);
}

// ----- boot + live reload -----
function boot(data) {
  state = structuredClone(data);
  panX = 0; panY = 0;
  setupCanvas();
  preloadAssets();
  render();
  const c = {};
  for (const f of state.features || []) c[f.glyph] = (c[f.glyph] || 0) + 1;
  statusEl.textContent = `Европа · ${state.grid.nominal_km} км · города ${c.city || 0} · массивы ${c.massif || 0} · леса ${c.forest || 0} · транспорт ${c.transport || 0}`;
}

window.addEventListener("resize", () => { setupCanvas(); render(); });

boot(initialData);

if (import.meta.hot) {
  import.meta.hot.accept("./data/hex_map.json", (mod) => {
    if (mod?.default) boot(mod.default);
  });
}
