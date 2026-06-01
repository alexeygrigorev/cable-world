import "./style.css";
import initialData from "./data/hex_map.json";

// the game's label font (scripts/map_panel.gd loads the same TTF)
const LABEL_FONT = "MapLabel";
new FontFace(LABEL_FONT, "url(/asset/LiberationSerif-BoldItalic.ttf)")
  .load()
  .then((ff) => { document.fonts.add(ff); render(); })
  .catch(() => {});

const SQRT3 = Math.sqrt(3);
const COLORS = {
  sea: "#bcd3e2",
  plainDE: "#e7c98f",
  plainOther: "#ded3c2",
  forest: "#9bbf78",
  mountain: "#bcae97",
  edge: "rgba(255,255,255,0.40)",
  outline: "#b8954e",
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
  if (cell.terrain === "sea") return COLORS.sea;
  if (cell.terrain === "forest") return COLORS.forest;
  if (cell.terrain === "mountain") return COLORS.mountain;
  return cell.country === "DE" ? COLORS.plainDE : COLORS.plainOther;
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

// real game sprites, loaded on demand and cached
const imgCache = new Map();
function getImg(name) {
  if (imgCache.has(name)) return imgCache.get(name);
  const img = new Image();
  img.onload = () => render();
  img.src = `/asset/${name}`;
  imgCache.set(name, img);
  return img;
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
    ctx.drawImage(img, cx - w / 2, cy - h * 0.82, w, h);
    bottom = cy + h * 0.18;
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
    ctx.lineWidth = s * 0.2;
    ctx.strokeStyle = "rgba(255,255,255,0.92)";
    ctx.strokeText(f.label, cx, ly);
    ctx.fillStyle = "#2c3540";
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

  for (const [key, cell] of Object.entries(state.hexes)) {
    const [q, r] = key.split(",").map(Number);
    const { x, y } = hexToContent(q, r);
    if (x < vx0 || x > vx1 || y < vy0 || y > vy1) continue; // off-screen
    hexPath(x, y, s);
    ctx.fillStyle = cellColor(cell);
    ctx.fill();
    ctx.strokeStyle = COLORS.edge;
    ctx.lineWidth = s * 0.03;
    ctx.stroke();
    if (cell.terrain === "forest") drawTree(x, y, s);
    else if (cell.terrain === "mountain") drawPeak(x, y, s);
  }

  ctx.strokeStyle = COLORS.outline;
  ctx.lineWidth = s * 0.05;
  for (const poly of state.reference_outline || []) {
    ctx.beginPath();
    poly.forEach(([wx, wy], i) => {
      const x = wx - origin()[0], y = wy - origin()[1];
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  // while dragging, highlight the target anchor hex under the cursor
  if (dragging && dragPos) {
    const { q, r } = contentToHex(dragPos.x, dragPos.y);
    const c = hexToContent(q, r);
    hexPath(c.x, c.y, s);
    ctx.fillStyle = "rgba(30,136,229,0.28)";
    ctx.fill();
    ctx.strokeStyle = "#1e88e5";
    ctx.lineWidth = s * 0.12;
    ctx.stroke();
    // exact anchor point at the hex center
    ctx.beginPath();
    ctx.arc(c.x, c.y, s * 0.16, 0, Math.PI * 2);
    ctx.fillStyle = "#1e88e5";
    ctx.fill();
    ctx.lineWidth = s * 0.05;
    ctx.strokeStyle = "#fff";
    ctx.stroke();
  }

  const showLabels = s * sc > 13; // only when zoomed in enough to read
  for (const f of state.features || []) {
    const held = f === dragging?.feature;
    const pos = held && dragPos ? dragPos : anchorContent(f);
    if (pos.x < vx0 || pos.x > vx1 || pos.y < vy0 || pos.y > vy1) continue;
    if (held) ctx.globalAlpha = 0.5;
    if (f.glyph === "city") drawCity(pos.x, pos.y, s, f, showLabels);
    ctx.globalAlpha = 1;
  }
}

function anchorContent(f) {
  const [q, r] = f.anchor.split(",").map(Number);
  return hexToContent(q, r);
}

// ----- pointer: drag feature, or pan -----
let dragging = null, dragPos = null, panning = null;

function eventToContent(e) {
  const rect = canvas.getBoundingClientRect();
  const { sc, tx, ty } = camera();
  return { x: (e.clientX - rect.left - tx) / sc, y: (e.clientY - rect.top - ty) / sc };
}

function featureAt(p) {
  const s = sizeW();
  for (let i = (state.features || []).length - 1; i >= 0; i--) {
    const f = state.features[i];
    const c = anchorContent(f);
    if (Math.hypot(p.x - c.x, p.y - c.y) < s * 0.9) return f;
  }
  return null;
}

canvas.addEventListener("pointerdown", (e) => {
  const p = eventToContent(e);
  const f = featureAt(p);
  if (f) {
    pushUndo();
    dragging = { feature: f };
    dragPos = p;
  } else {
    panning = { x: e.clientX, y: e.clientY, panX, panY };
  }
  canvas.setPointerCapture(e.pointerId);
});

canvas.addEventListener("pointermove", (e) => {
  if (dragging) {
    dragPos = eventToContent(e);
    render();
  } else if (panning) {
    panX = panning.panX + (e.clientX - panning.x);
    panY = panning.panY + (e.clientY - panning.y);
    render();
  }
});

canvas.addEventListener("pointerup", () => {
  if (dragging) {
    const { q, r } = contentToHex(dragPos.x, dragPos.y);
    dragging.feature.anchor = `${q},${r}`;
    const cell = state.hexes[`${q},${r}`];
    if (cell?.center) { dragging.feature.lon = cell.center[0]; dragging.feature.lat = cell.center[1]; }
    dragging = null; dragPos = null;
    render();
    save();
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
  render();
  save();
}
document.getElementById("undo").addEventListener("click", undo);
window.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") { e.preventDefault(); undo(); }
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
  render();
  const t = {};
  for (const c of Object.values(state.hexes)) t[c.terrain] = (t[c.terrain] || 0) + 1;
  statusEl.textContent = `Германия · ${state.grid.nominal_km} км · леса ${t.forest || 0} · горы ${t.mountain || 0} · города ${state.features?.length || 0}`;
}

window.addEventListener("resize", () => { setupCanvas(); render(); });

boot(initialData);

if (import.meta.hot) {
  import.meta.hot.accept("./data/hex_map.json", (mod) => {
    if (mod?.default) boot(mod.default);
  });
}
