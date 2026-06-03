import "./style.css";
import initialData from "./data/hex_map.json";
import mapConfig from "./data/map_config.json";
import liftDensity from "./data/lift_density.json";
import mountainRegions from "./data/mountain_regions_by_hex.json";
import hexElevation from "./data/hex_elevation.json";

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
  edge: "rgba(40,33,18,0.07)",
  outline: "rgba(70,60,40,0.55)", // country border
  labelFill: "#f6df9b",  // city label text in the game
  labelStroke: "rgba(28,18,8,0.9)",
};
const CITY_LABEL_FONT_SCALE = 0.72;
const CITY_LABEL_OUTLINE_SCALE = 0.17;
const FIXED_MAP_SCALE = 0.64;
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

// ----- Layer B: OSM lift-density overlay (see docs/pipelines/osm-lift-density.md) -----
const overlayParams = new URLSearchParams(window.location.search);
const overlays = {
  liftDensity: overlayParams.get("liftDensity") === "1", // press "L" to toggle
  alpsTarget: overlayParams.get("alpsTarget") !== "0",   // press "A" to toggle
  mountains: false,   // press "M" to toggle (see docs/pipelines/mountain-regions.md)
  elevation: false,   // hypsometric tint
};
let liftIndex = null;          // lazy-loaded named drill-in data (~900 KB)
const LIFT_DENSITY = liftDensity.by_hex || {};
const LIFT_NMAX = Math.max(1, ...Object.values(LIFT_DENSITY).map((c) => c.passenger_total));
const liftOverlayBtn = document.getElementById("liftOverlayToggle");
const LIFT_GROUP_LABEL = {
  cable_car: "канатные/фуникулёры", gondola: "гондольные",
  chair_lift: "кресельные", surface_tow: "бугельные/наземные",
  zip_line: "зиплайны", water_ski: "вейкборд/водные лыжи",
};
const LIFT_DOT = {
  cable_car: "#d0321e", gondola: "#f2783a", chair_lift: "#f6b733",
  surface_tow: "#9aa0a6", zip_line: "#6aa0c8", water_ski: "#3aa0d0",
};
// emphasis order: real aerial ropeways first, water-ski last
const LIFT_GROUP_ORDER = ["cable_car", "gondola", "chair_lift", "surface_tow", "zip_line", "water_ski"];
// raw OSM aerialway value -> short Russian label, so each lift says what it is
const LIFT_TYPE_LABEL = {
  cable_car: "канатная (кабина)", cablecar: "канатная (кабина)", mixed_lift: "комбинированная",
  funicular: "фуникулёр", gondola: "гондола", chair_lift: "кресельная",
  drag_lift: "бугель", "t-bar": "Т-бугель", platter: "тарелочный", "j-bar": "J-бугель",
  rope_tow: "верёвочный", magic_carpet: "траволатор", zip_line: "зиплайн",
};

// ----- Mountain regions overlay (see docs/pipelines/mountain-regions.md) -----
const MOUNTAIN_REGIONS = mountainRegions.by_hex || {};
const MOUNTAIN_ICON_SCALE = { small: 0.42, medium: 0.62, large: 0.85 };
// per-hex elevation in metres (null where no DEM coverage)
const HEX_ELEVATION = hexElevation.by_hex || {};

function liftHeat(n) {
  const t = Math.log1p(n) / Math.log1p(LIFT_NMAX);
  const stops = [[0, [255, 245, 200]], [0.35, [255, 196, 90]], [0.65, [242, 120, 40]], [0.85, [208, 50, 30]], [1, [150, 18, 24]]];
  for (let i = 0; i < stops.length - 1; i++) {
    const [t0, c0] = stops[i], [t1, c1] = stops[i + 1];
    if (t <= t1) {
      const f = t1 === t0 ? 0 : (t - t0) / (t1 - t0);
      return `rgb(${c0.map((v, j) => Math.round(v + (c1[j] - v) * f)).join(",")})`;
    }
  }
  return "rgb(150,18,24)";
}

// The named drill-in list is large, so it is fetched only on first hex open.
async function ensureLiftIndex() {
  if (!liftIndex) {
    const mod = await import("./data/lift_index_by_hex.json");
    liftIndex = mod.default.by_hex || {};
  }
  return liftIndex;
}

function escLift(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function syncOverlayButtons() {
  if (liftOverlayBtn) {
    liftOverlayBtn.classList.toggle("on", overlays.liftDensity);
    liftOverlayBtn.setAttribute("aria-pressed", overlays.liftDensity ? "true" : "false");
  }
  const set = (id, on) => { const el = document.getElementById(id); if (el) el.checked = on; };
  set("flt-lifts", overlays.liftDensity);
  set("flt-mountains", overlays.mountains);
  set("flt-elevation", overlays.elevation);
}

function toggleLiftOverlay() {
  setAllLiftGroups(!overlays.liftDensity);
  render();
}

window.addEventListener("keydown", (e) => {
  const t = e.target;
  if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA")) return;
  if (e.key === "l" || e.key === "L") { toggleLiftOverlay(); }
  else if (e.key === "a" || e.key === "A") { overlays.alpsTarget = !overlays.alpsTarget; render(); }
  else if (e.key === "m" || e.key === "M") { overlays.mountains = !overlays.mountains; syncOverlayButtons(); render(); }
});
liftOverlayBtn?.addEventListener("click", toggleLiftOverlay);

// ----- layer filter (checkboxes inside the right palette) -----
const LIFT_GROUPS_ON = new Set(LIFT_GROUP_ORDER); // which lift categories are shown
let NAMED_ON = true, UNNAMED_ON = true;            // "с названием" / "без названия"
function liftShown(c) {
  const named = c.named || {};
  let n = 0;
  for (const g of LIFT_GROUPS_ON) {
    const tot = c[g] || 0, nm = named[g] || 0;
    if (NAMED_ON) n += nm;
    if (UNNAMED_ON) n += tot - nm;
  }
  return n;
}
function setAllLiftGroups(on) {
  LIFT_GROUPS_ON.clear();
  if (on) for (const g of LIFT_GROUP_ORDER) LIFT_GROUPS_ON.add(g);
  overlays.liftDensity = on;
  for (const cb of document.querySelectorAll(".flt-lg")) cb.checked = on;
  syncOverlayButtons();
}
function eleColor(m) {
  const stops = [[-20, [60, 110, 150]], [0, [90, 150, 95]], [400, [170, 185, 110]],
    [1000, [175, 150, 100]], [2000, [150, 120, 95]], [3000, [225, 225, 230]], [4000, [255, 255, 255]]];
  for (let i = 0; i < stops.length - 1; i++) {
    const [a, ca] = stops[i], [b, cb] = stops[i + 1];
    if (m <= b) { const f = b === a ? 0 : (m - a) / (b - a); return `rgb(${ca.map((v, j) => Math.round(v + (cb[j] - v) * f)).join(",")})`; }
  }
  return "rgb(255,255,255)";
}
function wireFilters() {
  const lifts = document.getElementById("flt-lifts");
  const mtns = document.getElementById("flt-mountains");
  const elev = document.getElementById("flt-elevation");
  if (lifts) lifts.addEventListener("change", () => { setAllLiftGroups(lifts.checked); render(); });
  if (mtns) mtns.addEventListener("change", () => { overlays.mountains = mtns.checked; render(); });
  if (elev) elev.addEventListener("change", () => { overlays.elevation = elev.checked; render(); });
  for (const cb of document.querySelectorAll(".flt-lg")) {
    cb.addEventListener("change", () => {
      if (cb.checked) LIFT_GROUPS_ON.add(cb.dataset.g); else LIFT_GROUPS_ON.delete(cb.dataset.g);
      overlays.liftDensity = LIFT_GROUPS_ON.size > 0;
      syncOverlayButtons();
      render();
    });
  }
  const named = document.getElementById("flt-named");
  const unnamed = document.getElementById("flt-unnamed");
  if (named) named.addEventListener("change", () => { NAMED_ON = named.checked; render(); });
  if (unnamed) unnamed.addEventListener("change", () => { UNNAMED_ON = unnamed.checked; render(); });
}
wireFilters();
syncOverlayButtons();
let cssW = 0, cssH = 0;

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
  return cell.country === currentCountry() ? COLORS.landDE : COLORS.landOther;
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

function drawAlpsTargetMarker(cx, cy, s, band) {
  ctx.save();
  const scale = band === "main_alpine_wall" ? 0.72 : band === "northern_alpine_foothills" ? 0.55 : 0.44;
  ctx.globalAlpha = band === "main_alpine_wall" ? 0.82 : 0.62;
  drawPeak(cx, cy + s * 0.16, s * scale);
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
  img.assetStatus = "loading";
  img.onload = () => {
    img.assetStatus = "loaded";
    requestRender();
  };
  img.onerror = () => {
    img.assetStatus = "error";
    console.warn(`asset image failed: ${name}`, img.src);
    requestRender();
  };
  img.src = assetUrl(name);
  imgCache.set(name, img);
  return img;
}

// Multi-hex glyph footprint is metadata of glyph_ref, not a per-instance
// calculation. Primary points mark mostly opaque art; faint points mark weak
// alpha. Empty alpha has no point and cannot select the glyph.

function parseKey(key) {
  const [q, r] = key.split(",").map(Number);
  return { q, r };
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

function hexAnchorWorld(q, r) {
  const c = hexToWorld(q, r);
  const s = sizeW();
  return { x: c.x - (SQRT3 * s) / 2, y: c.y + s * 0.75 };
}

function worldToContent(x, y) {
  const o = origin();
  return { x: x - o[0], y: y - o[1] };
}

function glyphMetadata(f) {
  return f.glyph_ref ? state.glyphs?.[f.glyph_ref] : null;
}

function glyphRefFor(image) {
  return `massif:${image.replace(/\.png$/, "")}`;
}

function ensureMassifGlyphMetadata(image, zoomFactor, aspect) {
  state.glyphs ||= {};
  const ref = glyphRefFor(image);
  if (!state.glyphs[ref]) {
    const width = Number(zoomFactor || 5);
    const height = width / Number(aspect || 2);
    state.glyphs[ref] = {
      type: "massif",
      file: image,
      anchor_offset: "bottom-left",
      zoom_factor: round1(width),
      render_width_hex: round1(width),
      render_height_hex: round1(height),
      bounds_offset_hex: [
        0,
        round1(-height),
        round1(width),
        0,
      ],
    };
  }
  return ref;
}

function massifBounds(f, unit = sizeW()) {
  const meta = glyphMetadata(f);
  if (meta?.bounds_offset_hex) {
    const a = parseKey(f.anchor);
    const c = hexAnchorWorld(a.q, a.r);
    const [x0, y0, x1, y1] = meta.bounds_offset_hex.map((v) => v * unit);
    return [c.x + x0, c.y + y0, c.x + x1, c.y + y1].map(round1);
  }
  return null;
}

function massifAnchorContent(f, delta = { dq: 0, dr: 0 }) {
  const [q, r] = shiftKey(f.anchor, delta.dq, delta.dr).split(",").map(Number);
  return hexToContent(q, r);
}

function coverageCellsFromOffsets(f, offsets) {
  return offsets.map((offset) => applyOffset(f.anchor, offset));
}

function massifCoverage(f) {
  const meta = glyphMetadata(f);
  if (!meta?.primary_offsets || !meta?.faint_offsets) return null;
  return {
    primaryOffsets: meta.primary_offsets,
    faintOffsets: meta.faint_offsets,
    primary: coverageCellsFromOffsets(f, meta.primary_offsets),
    faint: coverageCellsFromOffsets(f, meta.faint_offsets),
  };
}

// warm the cache for everything on the map so panning never pops in
// Asset versions must be known before creating Image objects; otherwise the
// first render can load ?v=dev, then invalidate the whole image cache and leave
// point fallbacks visible until the second wave of PNGs decodes.
async function preloadAssets() {
  await requestAssetVersions();
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
    const dx = cx - w / 2, dy = cy - h * 0.72;
    ctx.drawImage(img, dx, dy, w, h);
  } else if (!img || img.assetStatus === "error") {
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
  const img = f.icon ? getImg(`city_${f.icon}.png`) : null;
  let bottom = cy;
  if (img && img.complete && img.naturalWidth) {
    // sprite footprint scaled to the hex; anchored so its base sits on the hex
    const h = s * 4.0;
    const w = h * (img.naturalWidth / img.naturalHeight);
    const tx = cx - w / 2, ty = cy - h * 0.70; // anchor point sits higher in the sprite
    ctx.drawImage(img, tx, ty, w, h);
    bottom = cy + h * 0.30;
  } else if (!img || img.assetStatus === "error") {
    const r = s * 0.38;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle = "#34495e";
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
function computeViewport() {
  updateLayoutMetrics();
  const rect = canvas.getBoundingClientRect();
  cssW = rect.width;
  cssH = rect.height;
}

function setupCanvas() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  computeViewport();
  canvas.width = cssW * dpr;
  canvas.height = cssH * dpr;
}

function updateLayoutMetrics() {
  const bar = document.getElementById("bar");
  const barHeight = Math.ceil(bar?.getBoundingClientRect().height || 48);
  document.documentElement.style.setProperty("--bar-height", `${barHeight}px`);
}

function scale() {
  return FIXED_MAP_SCALE * zoomVal;
}

function objectUnit() {
  return sizeW();
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
  const os = objectUnit();
  const objectScreenS = os * sc;
  // visible content rect (for culling) + margin
  const cullMargin = Math.max(s, os * 12);
  const vx0 = -tx / sc - cullMargin, vy0 = -ty / sc - cullMargin;
  const vx1 = (cssW - tx) / sc + cullMargin, vy1 = (cssH - ty) / sc + cullMargin;

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
    ctx.lineWidth = s * 0.012;
    ctx.stroke();
  }

  // 1a. elevation hypsometric tint
  if (overlays.elevation) {
    for (const key in HEX_ELEVATION) {
      const m = HEX_ELEVATION[key];
      if (m === null || m === undefined || !state.hexes[key]) continue;
      const [q, r] = key.split(",").map(Number);
      const { x, y } = hexToContent(q, r);
      if (!onScreen(x, y)) continue;
      hexPath(x, y, s);
      ctx.globalAlpha = 0.6;
      ctx.fillStyle = eleColor(m);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  }

  // 1b. Layer B: OSM lift-density heat tint (overview), respecting category filter
  if (overlays.liftDensity) {
    for (const key in LIFT_DENSITY) {
      if (!state.hexes[key]) continue;
      const n = liftShown(LIFT_DENSITY[key]);
      if (!n) continue;
      const [q, r] = key.split(",").map(Number);
      const { x, y } = hexToContent(q, r);
      if (!onScreen(x, y)) continue;
      hexPath(x, y, s);
      ctx.globalAlpha = 0.5;
      ctx.fillStyle = liftHeat(n);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  }

  // 2. country borders: edge between two land hexes of different countries
  ctx.strokeStyle = COLORS.outline;
  ctx.lineWidth = s * 0.08;
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

  // 3. multi-hex massif glyphs (each its own image, placed from glyph_ref metadata)
  for (const f of state.features || []) {
    if (f.glyph !== "massif" || !f.image) continue;
    const img = getImg(f.image);
    if (!img.complete || !img.naturalWidth) continue;
    const held = f === dragging?.feature;
    const d = held && dragging.delta ? hexDeltaWorld(dragging.delta.dq, dragging.delta.dr) : { x: 0, y: 0 };
    const bounds = massifBounds(f, os);
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
      if (!drawSprite(variant(k, FOREST_GLYPHS), x, y, os, os * 1.9, false)) drawTree(x, y, os);
    }
    ctx.globalAlpha = 1;
  }

  // 4. Planning layer: Alpine target cells where mountains should exist.
  // This is separate from the lift-density overlay and marks target hexes only;
  // final Alpine massif art must still be generated as hex-aware pieces.
  if (overlays.alpsTarget) {
    for (const [key, cell] of Object.entries(state.hexes)) {
      if (!cell.alps_target) continue;
      const [q, r] = key.split(",").map(Number);
      const { x, y } = hexToContent(q, r);
      if (!onScreen(x, y)) continue;
      drawAlpsTargetMarker(x, y, os, cell.alps_target_band);
    }
  }

  // 4b. Mountain-regions overlay: a peak icon per hex, sized by icon_size class
  // (see docs/pipelines/mountain-regions.md). Reuses drawPeak() like the Alpine
  // planning marker; independent of the lift overlay and alps_target planning.
  if (overlays.mountains) {
    for (const key in MOUNTAIN_REGIONS) {
      if (!state.hexes[key]) continue;
      const [q, r] = key.split(",").map(Number);
      const { x, y } = hexToContent(q, r);
      if (!onScreen(x, y)) continue;
      const scale = MOUNTAIN_ICON_SCALE[MOUNTAIN_REGIONS[key].icon_size] || 0.5;
      drawPeak(x, y + os * 0.1, os * scale);
    }
  }

  // 5. point objects (cities + transport) on top, south-over-north
  const showLabels = objectScreenS > 13;
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
    if (f.glyph === "city") drawCity(pos.x, pos.y, os, f, showLabels);
    else drawTransport(pos.x, pos.y, os, f, showLabels);
    ctx.globalAlpha = 1;
  }

  // 5c. Layer B: lift count numbers on top (legible above glyphs)
  if (overlays.liftDensity && s * sc >= 18) {
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = `${Math.max(7, s * 0.5)}px ui-sans-serif, system-ui, sans-serif`;
    ctx.lineWidth = s * 0.06;
    ctx.strokeStyle = "rgba(0,0,0,0.75)";
    ctx.fillStyle = "#ffffff";
    for (const key in LIFT_DENSITY) {
      if (!state.hexes[key]) continue;
      const n = liftShown(LIFT_DENSITY[key]);
      if (n < 6) continue;
      const [q, r] = key.split(",").map(Number);
      const { x, y } = hexToContent(q, r);
      if (!onScreen(x, y)) continue;
      ctx.strokeText(String(n), x, y);
      ctx.fillText(String(n), x, y);
    }
    ctx.restore();
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
      ctx.arc(c.x, c.y, os * 0.13, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(215,215,215,0.42)";
      ctx.fill();
      ctx.lineWidth = os * 0.035;
      ctx.strokeStyle = "rgba(80,80,80,0.35)";
      ctx.stroke();
    }
    for (const k of primaryKeys) {
      const [q, r] = k.split(",").map(Number);
      const c = hexToContent(q, r);
      ctx.beginPath();
      ctx.arc(c.x, c.y, os * 0.2, 0, Math.PI * 2);
      ctx.fillStyle = "#1e88e5";
      ctx.fill();
      ctx.lineWidth = os * 0.06;
      ctx.strokeStyle = "#fff";
      ctx.stroke();
    }
    if (hi.glyph === "massif") {
      const c = massifAnchorContent(hi, d);
      ctx.beginPath();
      ctx.arc(c.x, c.y, os * 0.31, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(246,223,155,0.18)";
      ctx.fill();
      ctx.lineWidth = os * 0.08;
      ctx.strokeStyle = "#f6df9b";
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(c.x, c.y, os * 0.08, 0, Math.PI * 2);
      ctx.fillStyle = "#f6df9b";
      ctx.fill();
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
      if (!drawSprite(FOREST_GLYPHS[0], c.x, c.y, os, os * 1.9, false)) drawTree(c.x, c.y, os);
    } else if (placing.kind === "massif") {
      const width = os * (placing.zoomFactor || 5.0);
      const img = placing.image ? getImg(placing.image) : null;
      const aspect = img?.complete && img.naturalWidth ? img.naturalWidth / img.naturalHeight : (placing.aspect || 2.0);
      if (!drawSprite(placing.image, c.x, c.y, os, width / aspect, false)) drawPeak(c.x, c.y, os);
    } else {
      drawTransport(c.x, c.y, os, { icon: placing.icon }, false);
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

function currentCountry() {
  return state.hexes[selectedHex]?.country || "DE";
}

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
  return false;
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
      anchor_cell: f.anchor,
      anchor_source_px: glyphMetadata(f)?.anchor_source_px || null,
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
    return `<h2>${f.label}</h2><div class="kind">Город</div>
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

// Drill-in: per-hex lift breakdown + named list (the "zoom-in on a hex" idea).
// Named lifts first; unnamed lifts are still listed but muted ("без названия").
function appendLiftSection(hexKey) {
  const c = LIFT_DENSITY[hexKey];
  if (!c) return;
  const box = document.createElement("div");
  box.className = "hex-debug";
  const parts = LIFT_GROUP_ORDER
    .filter((g) => c[g]).map((g) => `${LIFT_GROUP_LABEL[g]}: ${c[g]}`).join(" · ");
  box.innerHTML = `<h2>Подъёмники (OSM): ${c.passenger_total}</h2>` +
    `<div style="margin:2px 0 6px;color:#cfcfcf;font-size:12px">${parts}</div>` +
    `<div class="lift-list" style="font-size:12px;color:#bbb">загрузка списка…</div>`;
  panelBody.appendChild(box);
  const listEl = box.querySelector(".lift-list");
  const want = hexKey;
  const dot = (g) => `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${LIFT_DOT[g] || "#888"};margin-right:6px"></span>`;
  ensureLiftIndex().then((idx) => {
    if (selectedHex !== want) return;            // user moved to another hex
    const entry = idx[hexKey];
    if (!entry) { listEl.textContent = ""; return; }
    const CAP = 120;
    // named lifts: dot + name + the specific type so it's clear what each one is
    const namedRows = entry.lifts.slice(0, CAP).map((l) => {
      const t = LIFT_TYPE_LABEL[l.type] || l.type;
      const nm = l.id
        ? `<a href="https://www.openstreetmap.org/way/${l.id}" target="_blank" rel="noopener" style="color:#bcd">${escLift(l.name)}</a>`
        : escLift(l.name);
      return `<li style="list-style:none;margin:1px 0">${dot(l.group)}${nm} <span style="color:#888">· ${t}</span></li>`;
    }).join("");
    const more = entry.lifts.length > CAP ? `<li style="list-style:none;color:#999">…ещё ${entry.lifts.length - CAP} именованных</li>` : "";
    // unnamed lifts: not listed by name, but show how many of each type are there
    // unnamed lifts: collapsible — click to expand and open each on OSM to dig in
    const un = entry.unnamed || [];
    let unnamedHtml = "";
    if (un.length) {
      const byG = {};
      for (const u of un) byG[u.group] = (byG[u.group] || 0) + 1;
      const summary = LIFT_GROUP_ORDER.filter((g) => byG[g])
        .map((g) => `${dot(g)}${LIFT_GROUP_LABEL[g]} ×${byG[g]}`).join(" · ");
      const UNCAP = 300;
      const uItems = un.slice(0, UNCAP).map((u) => {
        const t = LIFT_TYPE_LABEL[u.type] || u.type;
        return `<li style="list-style:none;margin:1px 0">${dot(u.group)}<a href="https://www.openstreetmap.org/way/${u.id}" target="_blank" rel="noopener" style="color:#bcd">${t}</a> <span style="color:#777">· way/${u.id}</span></li>`;
      }).join("");
      const uMore = un.length > UNCAP ? `<li style="list-style:none;color:#777">…ещё ${un.length - UNCAP}</li>` : "";
      unnamedHtml = `<details style="margin-top:6px;color:#999"><summary style="cursor:pointer">Без названия: ${summary}</summary>` +
        `<ul style="padding-left:0;margin:4px 0">${uItems}${uMore}</ul></details>`;
    }
    listEl.innerHTML = `<ul style="padding-left:0;margin:4px 0">${namedRows}${more}</ul>${unnamedHtml}`;
  }).catch(() => { listEl.textContent = "(не удалось загрузить список)"; });
}

// Drill-in: which mountain SYSTEM -> SUB-REGION the hex is in, its icon-size
// class, and notable named peaks (see docs/pipelines/mountain-regions.md).
const MOUNTAIN_SIZE_LABEL = { small: "малый", medium: "средний", large: "крупный" };
function appendMountainSection(hexKey) {
  const m = MOUNTAIN_REGIONS[hexKey];
  if (!m) return;
  const box = document.createElement("div");
  box.className = "hex-debug";
  const where = m.subregion
    ? `${escLift(m.system)} → ${escLift(m.subregion)}`
    : (m.system ? escLift(m.system) : "—");
  const meta = [`размер иконки: ${MOUNTAIN_SIZE_LABEL[m.icon_size] || m.icon_size}`];
  if (m.max_ele != null) meta.push(`макс. высота: ${m.max_ele} м`);
  let peaksHtml = "";
  if (m.peaks && m.peaks.length) {
    const rows = m.peaks.map((p) => {
      const ele = p.ele != null ? ` <span style="color:#999">${p.ele} м</span>` : "";
      return `<li style="list-style:none;margin:1px 0">⛰ ${escLift(p.name)}${ele}</li>`;
    }).join("");
    peaksHtml = `<ul style="padding-left:0;margin:4px 0;font-size:12px;color:#ddd">${rows}</ul>`;
  }
  box.innerHTML = `<h2>Горы: ${where}</h2>` +
    `<div style="margin:2px 0 6px;color:#cfcfcf;font-size:12px">${meta.join(" · ")}</div>` +
    peaksHtml;
  panelBody.appendChild(box);
}

function renderPanelList(list, hexKey = selectedHex) {
  panelBody.innerHTML = "";
  if (hexKey) {
    const hexInfo = document.createElement("div");
    hexInfo.className = "hex-debug";
    const cell = state.hexes[hexKey];
    const ele = HEX_ELEVATION[hexKey];
    const eleStr = (ele === null || ele === undefined) ? "—" : `${ele} м`;
    hexInfo.innerHTML = `<h2>Гекс ${hexKey}</h2>
      <dl><dt>id</dt><dd>${hexKey}</dd>
      <dt>Страна</dt><dd>${cell?.country || "—"}</dd>
      <dt>Высота</dt><dd>${eleStr}</dd>
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
  // OSM-derived ambient context (lifts, mountains) goes below placed objects.
  if (hexKey) {
    appendLiftSection(hexKey);
    appendMountainSection(hexKey);
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
const TAP_MOVE_THRESHOLD_PX = 8;

function eventToContent(e) {
  const rect = canvas.getBoundingClientRect();
  const { sc, tx, ty } = camera();
  return { x: (e.clientX - rect.left - tx) / sc, y: (e.clientY - rect.top - ty) / sc };
}

function featureAt(p) {
  const s = objectUnit();
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
    }
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
    panning = { x: e.clientX, y: e.clientY, panX, panY, moved: false };
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
    const dx = e.clientX - panning.x;
    const dy = e.clientY - panning.y;
    if (Math.hypot(dx, dy) > TAP_MOVE_THRESHOLD_PX) panning.moved = true;
    panX = panning.panX + dx;
    panY = panning.panY + dy;
    render();
  }
});

canvas.addEventListener("pointerup", (e) => {
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
  if (panning && !panning.moved) selectAt(eventToContent(e));
  panning = null;
});

canvas.addEventListener("pointercancel", () => {
  dragging = null; dragPos = null; panning = null; dragMoved = false;
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
async function boot(data) {
  state = structuredClone(data);
  panX = 0; panY = 0;
  zoomValEl.textContent = `${Math.round(zoomVal * 100)}%`;
  syncPaletteToggle();
  setupCanvas();
  await preloadAssets();
  render();
  const c = {};
  for (const f of state.features || []) c[f.glyph] = (c[f.glyph] || 0) + 1;
  statusEl.textContent = `Европа · ${state.grid.nominal_km} км · города ${c.city || 0} · массивы ${c.massif || 0} · леса ${c.forest || 0} · транспорт ${c.transport || 0}`;
}

window.addEventListener("resize", () => {
  const center = cssW && cssH ? viewportCenterContent() : null;
  syncPaletteToggle();
  setupCanvas();
  if (center) {
    const sc = scale();
    const fc = focusCenter();
    panX = (fc.x - center.x) * sc;
    panY = (fc.y - center.y) * sc;
  }
  render();
});

void boot(initialData);

if (import.meta.hot) {
  import.meta.hot.accept("./data/hex_map.json", (mod) => {
    if (mod?.default) void boot(mod.default);
  });
}
