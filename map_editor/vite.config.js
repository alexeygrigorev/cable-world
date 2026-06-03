import { defineConfig } from "vite";
import { writeFileSync, existsSync, createReadStream, readdirSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";

const DATA_PATH = fileURLToPath(new URL("./src/data/hex_map.json", import.meta.url));
const MAPS_DIR = fileURLToPath(new URL("./maps/", import.meta.url));

const readBody = (req) => new Promise((res) => {
  let b = ""; req.on("data", (c) => (b += c)); req.on("end", () => res(b));
});
const safeName = (n) => /^[\w -]+$/.test(n) ? n.replace(/\s+/g, "-") : null;

// real game assets live in the repo, outside the editor folder
const ASSET_DIRS = [
  fileURLToPath(new URL("../assets/sprites/transport_glow/", import.meta.url)),
  fileURLToPath(new URL("../assets/sprites/", import.meta.url)),
  fileURLToPath(new URL("../assets/sprites/city_landmark_clusters_hi_res/outlined_thin/", import.meta.url)),
  fileURLToPath(new URL("../assets/map/glyphs/", import.meta.url)),
  fileURLToPath(new URL("../assets/map/massifs/", import.meta.url)),
  fileURLToPath(new URL("../assets/map/hex_terrain/generated_2026_06_01/forests/", import.meta.url)),
  fileURLToPath(new URL("../assets/map/hex_terrain/generated_2026_06_01/wooded_mountains/", import.meta.url)),
  fileURLToPath(new URL("../assets/map/hex_terrain/generated_2026_06_01/german_mountains/", import.meta.url)),
  fileURLToPath(new URL("../assets/map/hex_terrain/generated_2026_06_01/alps/", import.meta.url)),
  fileURLToPath(new URL("../assets/fonts/", import.meta.url)),
];
const MIME = { png: "image/png", ttf: "font/ttf", otf: "font/otf", woff2: "font/woff2" };

function findAsset(name) {
  if (!/^[\w.-]+$/.test(name)) return null;
  for (const dir of ASSET_DIRS) {
    const p = dir + name;
    if (existsSync(p)) return p;
  }
  return null;
}

// serve /asset/<file> from the game asset dirs (first match wins)
function gameAssetsPlugin() {
  return {
    name: "game-assets",
    configureServer(server) {
      server.middlewares.use("/asset/", (req, res) => {
        const name = decodeURIComponent(req.url.split("?")[0]).replace(/^\/+/, "");
        const ext = name.split(".").pop();
        if (!/^[\w.-]+$/.test(name) || !MIME[ext]) { res.statusCode = 400; return res.end(); }
        const p = findAsset(name);
        if (p) {
          res.setHeader("Content-Type", MIME[ext]);
          // Asset URLs include a mtime/size fingerprint from /__asset_versions.
          // That keeps reloads fast but changes URL whenever the file changes.
          res.setHeader("Cache-Control", "public, max-age=31536000, immutable");
          return createReadStream(p).pipe(res);
        }
        res.statusCode = 404;
        res.end();
      });
    },
  };
}

// Dev middleware: lets the browser persist edits back to hex_map.json.
// Writing the file triggers Vite HMR, so any edit (drag in browser, or me
// editing the file from chat) re-renders the page within a second.
function saveDataPlugin() {
  return {
    name: "save-hex-map",
    configureServer(server) {
      // live working file (auto-save on edits)
      server.middlewares.use("/__save", (req, res) => {
        if (req.method !== "POST") return res.end();
        let body = "";
        req.on("data", (c) => (body += c));
        req.on("end", () => {
          try {
            writeFileSync(DATA_PATH, JSON.stringify(JSON.parse(body), null, 2) + "\n");
            res.statusCode = 200;
            res.end("ok");
          } catch (e) {
            res.statusCode = 400;
            res.end(String(e));
          }
        });
      });

      // "Save As" to a named file under maps/ (won't touch the working file)
      server.middlewares.use("/__saveas", async (req, res) => {
        if (req.method !== "POST") return res.end();
        const u = new URL(req.url, "http://x");
        const name = safeName(u.searchParams.get("name") || "");
        if (!name) { res.statusCode = 400; return res.end("bad name"); }
        mkdirSync(MAPS_DIR, { recursive: true });
        const file = MAPS_DIR + name + ".json";
        if (existsSync(file) && u.searchParams.get("overwrite") !== "1") {
          res.statusCode = 409; return res.end("exists");
        }
        try {
          writeFileSync(file, JSON.stringify(JSON.parse(await readBody(req)), null, 2) + "\n");
          res.statusCode = 200; res.end("ok");
        } catch (e) { res.statusCode = 400; res.end(String(e)); }
      });

      // list saved maps
      server.middlewares.use("/__maps", (req, res) => {
        mkdirSync(MAPS_DIR, { recursive: true });
        const files = readdirSync(MAPS_DIR).filter((f) => f.endsWith(".json")).map((f) => f.slice(0, -5));
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify(files));
      });

      // stable cache keys for game assets used by the editor
      server.middlewares.use("/__asset_versions", (req, res) => {
        const u = new URL(req.url, "http://x");
        const names = (u.searchParams.get("names") || "").split(",").filter(Boolean);
        const versions = {};
        for (const name of names) {
          const p = findAsset(name);
          if (!p) continue;
          const st = statSync(p);
          versions[name] = `${st.size}-${Math.floor(st.mtimeMs)}`;
        }
        res.setHeader("Content-Type", "application/json");
        res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0");
        res.end(JSON.stringify(versions));
      });

      // load a saved map
      server.middlewares.use("/__open", (req, res) => {
        const u = new URL(req.url, "http://x");
        const name = safeName(u.searchParams.get("name") || "");
        const file = name && MAPS_DIR + name + ".json";
        if (!file || !existsSync(file)) { res.statusCode = 404; return res.end("not found"); }
        res.setHeader("Content-Type", "application/json");
        res.end(readFileSync(file));
      });
    },
  };
}

export default defineConfig({
  plugins: [saveDataPlugin(), gameAssetsPlugin()],
  server: { host: "0.0.0.0", port: 9050, strictPort: true },
  preview: { host: "0.0.0.0", port: 9050, strictPort: true },
});
