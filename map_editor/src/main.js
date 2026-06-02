import "./style.css";
import initialData from "./data/hex_map.json";
import mapConfig from "./data/map_config.json";

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
const CITY_LABEL_FONT_SCALE = 0.72;
const CITY_LABEL_OUTLINE_SCALE = 0.17;
// zoom range/step/default shared with the game (scripts/hex_map_model.gd reads
// the same map_config.json)
const ZCFG = (mapConfig && mapConfig.zoom) || { min: 0.25, max: 3.0, step: 0.25, default: 1.0 };
const assetVersions = new Map();

let state = structuredClone(initialData);
const canvas = document.getElementById("map");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");
const zoomValEl = document.getElementById("zoomVal");

// camera: fit-to-view at 100%, then user zoom on top, plus pan in CSS px
let zoomVal = ZCFG.default; // 1.0 = 100%
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
const FOREST_GLYPHS = [
  "forest_pine_single_v1.png",
  "forest_mixed_single_v1.png",
  "forest_broadleaf_single_v1.png",
  "forest_dark_conifer_single_v1.png",
  "forest_pine_bundle_3_v1.png",
  "forest_mixed_bundle_3_v1.png",
  "forest_broadleaf_bundle_3_v1.png",
  "forest_rocky_bundle_3_v1.png",
  "forest_pine_bundle_7_v1.png",
  "forest_mixed_bundle_7_v1.png",
  "forest_broadleaf_bundle_7_v1.png",
  "forest_sparse_edge_bundle_7_v1.png",
];
const MOUNTAIN_GLYPHS = [
  "mountain_harz_brocken_v1.png",
  "mountain_saxon_switzerland_v1.png",
  "mountain_erzgebirge_ridge_v1.png",
  "mountain_alps_central_wall_v1.png",
];
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
function assetUrl(name) {
  return `/asset/${name}?v=${assetVersions.get(name) || "dev"}`;
}

function getImg(name) {
  if (imgCache.has(name)) return imgCache.get(name);
  const img = new Image();
  img.decoding = "async";
  img.onload = requestRender;
  img.src = assetUrl(name);
  imgCache.set(name, img);
  return img;
}

// which hexes a massif actually paints (sampling the image's alpha). Primary
// points mark mostly opaque art; faint points mark weak alpha. Fully transparent
// bbox area is not part of the footprint and cannot select the glyph.
const alphaData = new Map();   // image name -> ImageData
const coverageCache = new Map(); // glyph render key -> { primaryOffsets, faintOffsets }
const HEX_ALPHA_STEP = 0.18;
const PRIMARY_ALPHA_RATIO = 0.22;

function pointInsideHex(dx, dy, s) {
  return Math.abs(dx) <= (Math.sqrt(3) / 2) * s && Math.abs(dy) + Math.abs(dx) / Math.sqrt(3) <= s;
}

function parseKey(key) {
  const [q, r] = key.split(",").map(Number);
  return { q, r };
}

function offsetKey(dq, dr) {
  return `${dq},${dr}`;
}

function applyOffset(anchor, offset) {
  const a = parseKey(anchor);
  const o = parseKey(offset);
  return `${a.q + o.q},${a.r + o.r}`;
}

function hexToWorld(q, r) {
  const s = sizeW();
  return { x: s * SQRT3 * (q + r / 2), y: s * 1.5 * r };
}

function glyphMetadata(f) {
  return f.glyph_ref ? state.glyphs?.[f.glyph_ref] : null;
}

function glyphRefFor(image, zoomFactor) {
  return `massif:${image}@${Number(zoomFactor || 5).toFixed(1)}`;
}

function ensureMassifGlyphMetadata(image, zoomFactor, aspect) {
  state.glyphs ||= {};
  const ref = glyphRefFor(image, zoomFactor);
  if (!state.glyphs[ref]) {
    const width = Number(zoomFactor || 5);
    const height = width / Number(aspect || 2);
    state.glyphs[ref] = {
      type: "massif",
      file: image,
      anchor_offset: "0,0",
      zoom_factor: round1(width),
      render_width_hex: round1(width),
      render_height_hex: round1(height),
      bounds_offset_hex: [
        round1(-width / 2),
        round1(-height / 2),
        round1(width / 2),
        round1(height / 2),
      ],
    };
  }
  return ref;
}

function massifBounds(f) {
  const meta = glyphMetadata(f);
  if (meta?.bounds_offset_hex) {
    const a = parseKey(f.anchor);
    const c = hexToWorld(a.q, a.r);
    const s = sizeW();
    const [x0, y0, x1, y1] = meta.bounds_offset_hex.map((v) => v * s);
    return [c.x + x0, c.y + y0, c.x + x1, c.y + y1].map(round1);
  }
  return null;
}

function massifRelativeBounds(f) {
  const meta = glyphMetadata(f);
  if (meta?.bounds_offset_hex) return meta.bounds_offset_hex.map((v) => round1(v * sizeW()));
  return null;
}

function massifCoverageKey(f, data) {
  const version = assetVersions.get(f.image) || "dev";
  return [
    f.image,
    version,
    data.width,
    data.height,
    massifRelativeBounds(f).join(","),
  ].join("|");
}

function coverageCellsFromOffsets(f, offsets) {
  return offsets
    .map((offset) => applyOffset(f.anchor, offset))
    .filter((key) => state.hexes[key]);
}

function massifCoverage(f) {
  const meta = glyphMetadata(f);
  if (meta?.primary_offsets && meta?.faint_offsets) {
    return {
      primaryOffsets: meta.primary_offsets,
      faintOffsets: meta.faint_offsets,
      primary: coverageCellsFromOffsets(f, meta.primary_offsets),
      faint: coverageCellsFromOffsets(f, meta.faint_offsets),
    };
  }
  if (!f.image || !meta?.bounds_offset_hex) return null;
  const img = getImg(f.image);
  if (!img.complete || !img.naturalWidth) return null; // not loaded yet

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

  const cacheKey = massifCoverageKey(f, data);
  let pattern = coverageCache.get(cacheKey);
  if (pattern) {
    return {
      ...pattern,
      primary: coverageCellsFromOffsets(f, pattern.primaryOffsets),
      faint: coverageCellsFromOffsets(f, pattern.faintOffsets),
    };
  }

  const relBounds = massifRelativeBounds(f);
  if (!relBounds) return null;
  const [x0, y0, x1, y1] = relBounds;
  const W = x1 - x0, H = y1 - y0, s = sizeW();
  const primaryOffsets = [];
  const faintOffsets = [];
  const maxDq = Math.ceil((Math.abs(x0) + Math.abs(x1)) / (SQRT3 * s)) + 3;
  const maxDr = Math.ceil((Math.abs(y0) + Math.abs(y1)) / (1.5 * s)) + 3;
  for (let dr = -maxDr; dr <= maxDr; dr++) {
    for (let dq = -maxDq; dq <= maxDq; dq++) {
      const { x: wx, y: wy } = hexDeltaWorld(dq, dr);
      if (wx + s < x0 || wx - s > x1 || wy + s < y0 || wy - s > y1) continue; // hex cannot overlap glyph box
      let opaque = 0;
      let sampled = 0;
      for (let oy = -0.9; oy <= 0.91; oy += HEX_ALPHA_STEP) {
        for (let ox = -0.9; ox <= 0.91; ox += HEX_ALPHA_STEP) {
          const sx = wx + ox * s;
          const sy = wy + oy * s;
          if (!pointInsideHex(sx - wx, sy - wy, s)) continue;
          const ix = Math.round(((sx - x0) / W) * (data.width - 1));
          const iy = Math.round(((sy - y0) / H) * (data.height - 1));
          if (ix < 0 || iy < 0 || ix >= data.width || iy >= data.height) continue;
          sampled++;
          if (data.data[(iy * data.width + ix) * 4 + 3] > 50) opaque++;
        }
      }
      if (!sampled || !opaque) continue;
      const coverage = opaque / sampled;
      const key = offsetKey(dq, dr);
      if (coverage >= PRIMARY_ALPHA_RATIO) primaryOffsets.push(key);
      else faintOffsets.push(key);
    }
  }
  pattern = { primaryOffsets, faintOffsets };
  coverageCache.set(cacheKey, pattern);
  return {
    ...pattern,
    primary: coverageCellsFromOffsets(f, pattern.primaryOffsets),
    faint: coverageCellsFromOffsets(f, pattern.faintOffsets),
  };
}

// warm the cache for everything on the map so panning never pops in
function preloadAssets() {
  requestAssetVersions();
  for (const f of state.features || []) {
    if (f.glyph === "city" && f.icon) getImg(`city_${f.icon}.png`);
    else if (f.glyph === "massif" && f.image) getImg(f.image);
  }
  for (const g of [...FOREST_GLYPHS]) getImg(g);
}

function assetNamesInUse() {
  const names = new Set([...FOREST_GLYPHS]);
  for (const f of state.features || []) {
    if (f.glyph === "city" && f.icon) names.add(`city_${f.icon}.png`);
    else if (f.glyph === "transport" && f.icon) names.add(`icon_${f.icon}.png`);
    else if (f.glyph === "massif" && f.image) names.add(f.image);
  }
  for (const p of PALETTE) {
    if (p.image) names.add(p.image);
    if (p.icon) names.add(`icon_${p.icon}.png`);
  }
  return [...names];
}

async function requestAssetVersions() {
  const names = assetNamesInUse();
  if (!names.length) return;
  const res = await fetch(`/__asset_versions?names=${encodeURIComponent(names.join(","))}`).catch(() => null);
  if (!res?.ok) return;
  const data = await res.json();
  let changed = false;
  for (const [name, version] of Object.entries(data)) {
    if (assetVersions.get(name) !== version) {
      assetVersions.set(name, version);
      imgCache.delete(name);
      alphaData.delete(name);
      coverageCache.clear();
      changed = true;
    }
  }
  if (changed) requestRender();
}

function drawTransport(cx, cy, s, f) {
  ctx.save();
  const img = f.icon ? getImg(`icon_${f.icon}.png`) : null;
  if (img && img.complete && img.naturalWidth) {
    const h = s * 2.0;
    const w = h * (img.naturalWidth / img.naturalHeight);
    // dark outline-glow so the icon reads over busy terrain (built up by a few
    // shadowed passes), then a crisp draw on top — not white, but visible
    const dx = cx - w / 2, dy = cy - h * 0.72;
    ctx.shadowColor = "rgba(22,16,9,0.9)";
    ctx.shadowBlur = s * 0.22;
    ctx.drawImage(img, dx, dy, w, h);
    ctx.drawImage(img, dx, dy, w, h);
    ctx.drawImage(img, dx, dy, w, h);
    ctx.shadowBlur = 0;
    ctx.drawImage(img, dx, dy, w, h);
  } else {
    ctx.beginPath();
    ctx.arc(cx, cy, s * 0.4, 0, Math.PI * 2);
    ctx.fillStyle = "#2e7d32";
    ctx.fill();
    ctx.lineWidth = s * 0.06;
    ctx.strokeStyle = "#fff";
    ctx.stroke();
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
    const tx = cx - w / 2, ty = cy - h * 0.70; // anchor point sits higher in the sprite
    ctx.drawImage(img, tx, ty, w, h);
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
    ctx.font = `${(s * CITY_LABEL_FONT_SCALE).toFixed(1)}px "${LABEL_FONT}", serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.lineJoin = "round";
    ctx.lineWidth = s * CITY_LABEL_OUTLINE_SCALE;
    ctx.strokeStyle = COLORS.labelStroke;
    ctx.strokeText(f.label, cx, ly);
    ctx.fillStyle = COLORS.labelFill;
    ctx.fillText(f.label, cx, ly);
  }
  ctx.restore();
}

// ----- camera / rendering -----
function computeFit() {
  updateLayoutMetrics();
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

function updateLayoutMetrics() {
  const bar = document.getElementById("bar");
  const barHeight = Math.ceil(bar?.getBoundingClientRect().height || 48);
  document.documentElement.style.setProperty("--bar-height", `${barHeight}px`);
}

function scale() {
  return fitScale * zoomVal;
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

function viewportCenterContent() {
  const sc = scale();
  const fc = focusCenter();
  clampPan(fc, sc);
  return { x: fc.x - panX / sc, y: fc.y - panY / sc };
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
    const bounds = massifBounds(f);
    if (!bounds) continue;
    const [x0, y0, x1, y1] = bounds;
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

  // 5a. clicked hex debug outline. It is independent from feature selection so
  // empty hexes can still show their id in the panel.
  if (selectedHex) {
    const [q, r] = selectedHex.split(",").map(Number);
    const c = hexToContent(q, r);
    if (onScreen(c.x, c.y)) {
      hexPath(c.x, c.y, s);
      ctx.fillStyle = "rgba(246,223,155,0.08)";
      ctx.fill();
      ctx.strokeStyle = "#f6df9b";
      ctx.lineWidth = s * 0.09;
      ctx.stroke();
    }
  }

  // 5b. occupied-hex points of the selected (or dragged) feature, drawn on top
  //     so they're visible even under a city/transport sprite
  const hi = dragging && dragPos ? dragging.feature : selected;
  if (hi) {
    let primaryKeys;
    let faintKeys = [];
    const d = dragging?.feature === hi && dragging.delta ? dragging.delta : { dq: 0, dr: 0 };
    if (hi.glyph === "massif") {
      const coverage = massifCoverage(hi);
      let filled = coverage?.primary || []; // points only where the art mostly covers a hex
      if (!filled.length) filled = [hi.anchor];
      primaryKeys = filled.map((k) => shiftKey(k, d.dq, d.dr));
      faintKeys = (coverage?.faint || [])
        .filter((k) => !filled.includes(k))
        .map((k) => shiftKey(k, d.dq, d.dr));
    } else if (hi.glyph === "forest") {
      primaryKeys = (hi.cells || []).map((k) => shiftKey(k, d.dq, d.dr));
    } else if (dragging?.feature === hi && dragPos) {
      const { q, r } = contentToHex(dragPos.x, dragPos.y);
      primaryKeys = [`${q},${r}`];
    } else {
      primaryKeys = [hi.anchor];
    }
    for (const k of faintKeys) {
      const [q, r] = k.split(",").map(Number);
      const c = hexToContent(q, r);
      ctx.beginPath();
      ctx.arc(c.x, c.y, s * 0.13, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(215,215,215,0.42)";
      ctx.fill();
      ctx.lineWidth = s * 0.035;
      ctx.strokeStyle = "rgba(80,80,80,0.35)";
      ctx.stroke();
    }
    for (const k of primaryKeys) {
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
    } else if (placing.kind === "massif") {
      const width = s * (placing.zoomFactor || 5.0);
      const img = placing.image ? getImg(placing.image) : null;
      const aspect = img?.complete && img.naturalWidth ? img.naturalWidth / img.naturalHeight : (placing.aspect || 2.0);
      if (!drawSprite(placing.image, c.x, c.y, s, width / aspect, false)) drawPeak(c.x, c.y, s);
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
let selectedHex = null;
document.getElementById("panelClose").addEventListener("click", deselect);

function deselect() {
  selected = null;
  selectedHex = null;
  panelEl.hidden = true;
  render();
}

// ordering in the panel: transport objects first, then cities, then the rest
const featureRank = (f) => (f.glyph === "transport" ? 0 : f.glyph === "city" ? 1 : 2);

function featuresAtHex(key) {
  return (state.features || [])
    .filter((f) => featureOccupiesHex(f, key))
    .sort((a, b) => featureRank(a) - featureRank(b));
}

function featureOccupiesHex(f, key) {
  if (f.glyph === "city" || f.glyph === "transport") return f.anchor === key;
  if (f.glyph === "forest") return (f.cells || []).includes(key);
  if (f.glyph !== "massif") return (f.cells || []).includes(key);
  const coverage = f.image ? massifCoverage(f) : null;
  if (coverage) return coverage.primary.includes(key) || coverage.faint.includes(key);
  return (f.cells || []).includes(key);
}

function canReset(f) {
  return !f.user && f.glyph !== "forest" && f.home && f.anchor !== f.home;
}

function canDelete(f) {
  return f.user || (moveEnabled && (f.glyph === "forest" || f.glyph === "massif"));
}

// select everything sitting on the clicked hex; show all in the panel
function selectAt(p) {
  const { q, r } = contentToHex(p.x, p.y);
  const key = `${q},${r}`;
  let list = featuresAtHex(key);
  const top = featureAt(p);
  if (top && !list.includes(top)) list = [top, ...list];
  selected = list.length ? (top && list.includes(top) ? top : list[0]) : null;
  selectedHex = key;
  renderPanelList(list, key);
  panelEl.hidden = false;
  render();
}

function refreshPanel() {
  if (!selectedHex) return;
  const list = featuresAtHex(selectedHex);
  renderPanelList(list, selectedHex);
}

function deleteFeature(f) {
  if (!canDelete(f)) return;
  pushUndo();
  state.features = state.features.filter((x) => x !== f);
  if (selected === f) selected = featuresAtHex(selectedHex).find((x) => x !== f) || null;
  refreshPanel();
  save();
  render();
}

// snap a system object back to its original (real-world-derived) position
function resetFeature(f) {
  if (f.user || !f.home) return;
  const [hq, hr] = f.home.split(",").map(Number);
  const [aq, ar] = f.anchor.split(",").map(Number);
  const dq = hq - aq, dr = hr - ar;
  if (dq || dr) {
    pushUndo();
    f.anchor = f.home;
    if (f.cells) f.cells = f.cells.map((k) => shiftKey(k, dq, dr));
    save();
  }
  refreshPanel();
  render();
}

function glyphName(f) {
  if (f.glyph === "city") return f.icon ? `city_${f.icon}.png` : "точка города";
  if (f.glyph === "transport") return f.icon ? `icon_${f.icon}.png` : "точка объекта";
  if (f.glyph === "massif") return f.image || "massif";
  if (f.glyph === "forest") return variant(f.anchor || (f.cells || [])[0] || f.id, FOREST_GLYPHS);
  return f.glyph || "unknown";
}

function glyphPreviewHtml(f) {
  const name = glyphName(f);
  if (name.endsWith(".png")) return `<img class="thumb" src="${assetUrl(name)}" alt="">`;
  return "";
}

function glyphDebugRows(f) {
  const name = glyphName(f);
  if (!name.endsWith(".png")) return "";
  const img = getImg(name);
  const natural = img.complete && img.naturalWidth ? `${img.naturalWidth}×${img.naturalHeight}` : "загрузка";
  if (f.glyph !== "massif") return `<dt>PNG</dt><dd>${natural}</dd>`;

  const bounds = massifBounds(f);
  if (!bounds) return `<dt>PNG</dt><dd>${natural}</dd>`;
  const [x0, y0, x1, y1] = bounds;
  const widthHex = ((x1 - x0) / sizeW()).toFixed(1);
  const heightHex = ((y1 - y0) / sizeW()).toFixed(1);
  const coverage = massifCoverage(f);
  const primary = coverage?.primary?.length ?? 0;
  const faint = coverage?.faint?.length ?? 0;
  const zoom = glyphMetadata(f)?.zoom_factor;
  return `<dt>PNG</dt><dd>${natural}</dd>
    <dt>Рендер</dt><dd>${widthHex}×${heightHex} гексов, zoom ${zoom ?? widthHex}</dd>
    <dt>Alpha</dt><dd>${primary} primary · ${faint} faint</dd>`;
}

function glyphDebugPayload(f, hexKey = selectedHex) {
  const name = glyphName(f);
  const img = name.endsWith(".png") ? getImg(name) : null;
  const payload = {
    clicked_hex: hexKey,
    clicked_cell: hexKey ? state.hexes[hexKey] : null,
    feature: {
      id: f.id,
      glyph: f.glyph,
      label: f.label,
      glyph_file: name,
      glyph_ref: f.glyph_ref || null,
      anchor: f.anchor,
      legacy_cells_count: (f.cells || []).length,
      legacy_cells: f.cells || [],
      lon: f.lon ?? null,
      lat: f.lat ?? null,
    },
    image: img && img.complete && img.naturalWidth ? {
      natural_width: img.naturalWidth,
      natural_height: img.naturalHeight,
      aspect: round1(img.naturalWidth / img.naturalHeight),
    } : null,
  };
  if (f.glyph === "massif") {
    const bounds = massifBounds(f);
    const coverage = massifCoverage(f);
    if (!bounds) return payload;
    const [x0, y0, x1, y1] = bounds;
    payload.render = {
      width_hex: round1((x1 - x0) / sizeW()),
      height_hex: round1((y1 - y0) / sizeW()),
      aspect_preserved: true,
      glyph_ref: f.glyph_ref || null,
      anchor_offset: glyphMetadata(f)?.anchor_offset || "0,0",
      zoom_factor: glyphMetadata(f)?.zoom_factor ?? null,
      primary_alpha_offsets: coverage?.primaryOffsets || [],
      faint_alpha_offsets: coverage?.faintOffsets || [],
      primary_alpha_cells_count: coverage?.primary?.length ?? null,
      primary_alpha_cells: coverage?.primary || [],
      faint_alpha_cells_count: coverage?.faint?.length ?? null,
      faint_alpha_cells: coverage?.faint || [],
    };
  }
  return payload;
}

async function copyGlyphDebug(f) {
  const text = JSON.stringify(glyphDebugPayload(f), null, 2);
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    area.remove();
    return ok;
  }
}

function cardHtml(f) {
  if (f.glyph === "city") {
    return `<h2>${f.label}</h2><div class="kind">${f.kind === "capital" ? "Столица" : "Город"}</div>
      ${glyphPreviewHtml(f)}
      <dl><dt>Тип</dt><dd>город</dd><dt>id</dt><dd>${f.id}</dd><dt>Глиф</dt><dd>${glyphName(f)}</dd>${glyphDebugRows(f)}
      <dt>Координаты</dt><dd>${(f.lat ?? 0).toFixed(4)}, ${(f.lon ?? 0).toFixed(4)}</dd>
      <dt>Гекс</dt><dd>${f.anchor}</dd></dl>`;
  }
  if (f.glyph === "transport") {
    return `<h2>${f.label || "Объект"}</h2><div class="kind">Транспортный объект</div>
      ${glyphPreviewHtml(f)}
      <dl><dt>Тип</dt><dd>${TRANSPORT_LABELS[f.icon] || f.icon}</dd><dt>id</dt><dd>${f.id}</dd><dt>Глиф</dt><dd>${glyphName(f)}</dd>${glyphDebugRows(f)}
      <dt>Координаты</dt><dd>${(f.lat ?? 0).toFixed(4)}, ${(f.lon ?? 0).toFixed(4)}</dd>
      <dt>Гекс</dt><dd>${f.anchor}</dd></dl>`;
  }
  if (f.glyph === "massif") {
    const coverage = massifCoverage(f);
    const footprintCount = (coverage?.primary?.length ?? 0) + (coverage?.faint?.length ?? 0);
    return `<h2>${f.label}</h2><div class="kind">Горный массив</div>
      ${glyphPreviewHtml(f)}
      <dl><dt>id</dt><dd>${f.id}</dd><dt>Глиф</dt><dd>${glyphName(f)}</dd>${glyphDebugRows(f)}<dt>Footprint</dt><dd>${footprintCount}</dd>
      <dt>Якорь</dt><dd>${f.anchor}</dd></dl>`;
  }
  return `<h2>Лес</h2><div class="kind">Лесной массив</div>
    ${glyphPreviewHtml(f)}
    <dl><dt>id</dt><dd>${f.id}</dd><dt>Глиф</dt><dd>${glyphName(f)}</dd>${glyphDebugRows(f)}<dt>Гексов</dt><dd>${(f.cells || []).length}</dd>
    <dt>Якорь</dt><dd>${f.anchor}</dd></dl>`;
}

function renderPanelList(list, hexKey = selectedHex) {
  panelBody.innerHTML = "";
  if (hexKey) {
    const hexInfo = document.createElement("div");
    hexInfo.className = "hex-debug";
    const cell = state.hexes[hexKey];
    hexInfo.innerHTML = `<h2>Гекс ${hexKey}</h2>
      <dl><dt>id</dt><dd>${hexKey}</dd>
      <dt>Страна</dt><dd>${cell?.country || "—"}</dd>
      <dt>Террейн</dt><dd>${cell?.terrain || "—"}</dd></dl>`;
    panelBody.appendChild(hexInfo);
  }
  if (list.length > 1) {
    const h = document.createElement("div");
    h.className = "panel-count";
    h.textContent = `Объектов на гексе: ${list.length}`;
    panelBody.appendChild(h);
  } else if (!list.length) {
    const h = document.createElement("div");
    h.className = "panel-count";
    h.textContent = "Объектов на гексе нет";
    panelBody.appendChild(h);
  }
  for (const f of list) {
    const card = document.createElement("div");
    card.className = "obj-card" + (f === selected ? " sel" : "");
    card.innerHTML = cardHtml(f);
    card.addEventListener("click", () => {
      if (panelHasTextSelection()) return;
      selected = f;
      render();
      refreshPanel();
    });
    if (canDelete(f)) {
      const b = document.createElement("button");
      b.className = "card-act del";
      b.textContent = "🗑 удалить";
      b.addEventListener("click", (e) => { e.stopPropagation(); deleteFeature(f); });
      card.appendChild(b);
    } else if (canReset(f)) {
      const b = document.createElement("button");
      b.className = "card-act reset";
      b.textContent = "↺ вернуть на место";
      b.addEventListener("click", (e) => { e.stopPropagation(); resetFeature(f); });
      card.appendChild(b);
    }
    const copy = document.createElement("button");
    copy.className = "card-act copy";
    copy.textContent = "copy glyph debug";
    copy.addEventListener("click", async (e) => {
      e.stopPropagation();
      copy.textContent = await copyGlyphDebug(f) ? "copied" : "copy failed";
      setTimeout(() => { copy.textContent = "copy glyph debug"; }, 900);
    });
    card.appendChild(copy);
    panelBody.appendChild(card);
  }
}

function panelHasTextSelection() {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed || selection.rangeCount === 0) return false;
  const range = selection.getRangeAt(0);
  return panelEl.contains(range.commonAncestorContainer);
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
  // transport objects first (they sit on top and are the focus), then cities
  for (const f of state.features || []) {
    if (f.glyph !== "transport") continue;
    const c = anchorContent(f);
    if (Math.hypot(p.x - c.x, p.y - c.y) < s * 0.9) return f;
  }
  for (const f of state.features || []) {
    if (f.glyph !== "city") continue;
    const c = anchorContent(f);
    if (Math.hypot(p.x - c.x, p.y - c.y) < s * 0.9) return f;
  }
  // forests: pointer over any of the bundle's hexes
  const ph = contentToHex(p.x, p.y);
  const pk = `${ph.q},${ph.r}`;
  for (const f of state.features || []) {
    if (f.glyph === "forest" && (f.cells || []).includes(pk)) return f;
  }
  // massifs by glyph footprint: no transparent bbox hit-testing once the image
  // has loaded and its alpha metadata is available.
  for (const f of state.features || []) {
    if (f.glyph !== "massif" || !f.image) continue;
    const coverage = massifCoverage(f);
    if (coverage) {
      if (coverage.primary.includes(pk) || coverage.faint.includes(pk)) return f;
      continue;
    }
    const bounds = massifBounds(f);
    if (!bounds) continue;
    const [x0, y0, x1, y1] = bounds;
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
    selectAt(p);
  } else {
    // locked (default): click selects, the object stays put; drag pans the map
    selectAt(p);
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
      if (selected === f) { selectedHex = f.anchor; refreshPanel(); }
      save();
    }
    dragging = null; dragPos = null;
    render();
  }
  panning = null;
});

// ----- zoom -----
function setZoom(value) {
  const center = viewportCenterContent();
  const stepped = Math.round(value / ZCFG.step) * ZCFG.step;
  zoomVal = Math.max(ZCFG.min, Math.min(ZCFG.max, stepped));
  const sc = scale();
  const fc = focusCenter();
  panX = (fc.x - center.x) * sc;
  panY = (fc.y - center.y) * sc;
  zoomValEl.textContent = `${Math.round(zoomVal * 100)}%`;
  render();
}
document.getElementById("zoomIn").addEventListener("click", () => setZoom(zoomVal + ZCFG.step));
document.getElementById("zoomOut").addEventListener("click", () => setZoom(zoomVal - ZCFG.step));
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
  selectedHex = null;
  panelEl.hidden = true;
  render();
  save();
}
document.getElementById("undo").addEventListener("click", undo);
window.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") { e.preventDefault(); undo(); }
  else if ((e.key === "Delete" || e.key === "Backspace") && selected && canDelete(selected)) {
    e.preventDefault();
    deleteFeature(selected);
  }
});

// ----- move toggle (objects locked by default) -----
const moveBtn = document.getElementById("moveToggle");
moveBtn.addEventListener("click", () => {
  moveEnabled = !moveEnabled;
  moveBtn.textContent = moveEnabled ? "🔓 базовая карта" : "🔒 базовая карта";
  moveBtn.classList.toggle("on", moveEnabled);
  refreshPanel();
});

// ----- palette show/hide -----
const paletteToggle = document.getElementById("paletteToggle");
function syncPaletteToggle() {
  const hidden = document.body.classList.contains("palette-hidden");
  paletteToggle.setAttribute("aria-expanded", hidden ? "false" : "true");
  paletteToggle.textContent = window.matchMedia("(max-width: 700px)").matches
    ? (hidden ? "⌃" : "⌄")
    : (hidden ? "‹" : "›");
}
paletteToggle.addEventListener("click", () => {
  document.body.classList.toggle("palette-hidden");
  syncPaletteToggle();
  render();
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
  { kind: "forest", size: 1, label: "Лес (малый)", emoji: "🌲" },
  { kind: "forest", size: 7, label: "Лес (пучок)", emoji: "🌳" },
  { kind: "massif", label: "Schwarzwald", image: "black_forest.png", zoomFactor: 5.2, aspect: 446 / 310 },
  { kind: "massif", label: "Bayerischer Wald", image: "bavarian_forest.png", zoomFactor: 5.0, aspect: 452 / 285 },
  { kind: "massif", label: "Eifel-Hunsrueck", image: "eifel_hunsrueck.png", zoomFactor: 4.8, aspect: 478 / 183 },
  { kind: "massif", label: "Harz", image: "harz.png", zoomFactor: 4.3, aspect: 461 / 329 },
  { kind: "massif", label: "Erzgebirge", image: "erzgebirge.png", zoomFactor: 5.6, aspect: 491 / 319 },
  { kind: "massif", label: "Saxon Switzerland", image: "saxon_switzerland.png", zoomFactor: 3.8, aspect: 462 / 320 },
  { kind: "massif", label: "Western Alps", image: "western_alps_massif.png", zoomFactor: 11.0, aspect: 628 / 304 },
  { kind: "massif", label: "Swiss Alps", image: "swiss_alps_massif.png", zoomFactor: 11.2, aspect: 753 / 250 },
  { kind: "massif", label: "Bavarian/Tyrol Alps", image: "bavarian_tyrol_alps_massif.png", zoomFactor: 10.8, aspect: 975 / 168 },
  { kind: "massif", label: "German Alpine Edge", image: "german_alpine_edge_massif.png", zoomFactor: 9.2, aspect: 1042 / 155 },
  { kind: "massif", label: "Austrian Alps", image: "austrian_alps_massif.png", zoomFactor: 10.6, aspect: 1040 / 196 },
];

let placing = null, placeGhost = null, nextId = 1;

(function buildPalette() {
  const host = document.getElementById("paletteItems");
  for (const p of PALETTE) {
    const el = document.createElement("div");
    el.className = "palette-item";
    el.innerHTML = (p.image ? `<img src="${assetUrl(p.image)}" alt="">`
      : p.icon ? `<img src="${assetUrl(`icon_${p.icon}.png`)}" alt="">`
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
    const cells = [key];
    if (p.size === 7) for (const [dq, dr] of NB) cells.push(shiftKey(key, dq, dr));
    f = { id: `forest-new-${nextId++}`, glyph: "forest", label: "Лес", cells, anchor: key, user: true };
  } else if (p.kind === "massif") {
    const ref = ensureMassifGlyphMetadata(p.image, p.zoomFactor, p.aspect);
    f = {
      id: `${p.image.replace(/\.png$/, "")}-${nextId++}`,
      glyph: "massif",
      image: p.image,
      glyph_ref: ref,
      label: p.label,
      anchor: key,
      user: true,
    };
  } else {
    f = { id: `${p.icon}-${nextId++}`, glyph: "transport", icon: p.icon, label: p.label,
          anchor: key, lon: cell?.center?.[0], lat: cell?.center?.[1], user: true };
  }
  state.features.push(f);
  selected = f;
  selectedHex = key;
  renderPanelList(featuresAtHex(key), key);
  panelEl.hidden = false;
  render();
  save();
}

function round1(value) {
  return Math.round(value * 10) / 10;
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
  zoomValEl.textContent = `${Math.round(zoomVal * 100)}%`;
  syncPaletteToggle();
  setupCanvas();
  preloadAssets();
  render();
  const c = {};
  for (const f of state.features || []) c[f.glyph] = (c[f.glyph] || 0) + 1;
  statusEl.textContent = `Европа · ${state.grid.nominal_km} км · города ${c.city || 0} · массивы ${c.massif || 0} · леса ${c.forest || 0} · транспорт ${c.transport || 0}`;
}

window.addEventListener("resize", () => { syncPaletteToggle(); setupCanvas(); render(); });

boot(initialData);

if (import.meta.hot) {
  import.meta.hot.accept("./data/hex_map.json", (mod) => {
    if (mod?.default) boot(mod.default);
  });
}
