import { defineConfig } from "vite";
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const DATA_PATH = fileURLToPath(new URL("./src/data/hex_map.json", import.meta.url));

// Dev middleware: lets the browser persist edits back to hex_map.json.
// Writing the file triggers Vite HMR, so any edit (drag in browser, or me
// editing the file from chat) re-renders the page within a second.
function saveDataPlugin() {
  return {
    name: "save-hex-map",
    configureServer(server) {
      server.middlewares.use("/__save", (req, res) => {
        if (req.method !== "POST") return res.end();
        let body = "";
        req.on("data", (c) => (body += c));
        req.on("end", () => {
          try {
            const parsed = JSON.parse(body);
            writeFileSync(DATA_PATH, JSON.stringify(parsed, null, 2) + "\n");
            res.statusCode = 200;
            res.end("ok");
          } catch (e) {
            res.statusCode = 400;
            res.end(String(e));
          }
        });
      });
    },
  };
}

export default defineConfig({
  plugins: [saveDataPlugin()],
  server: { host: "0.0.0.0", port: 9050, strictPort: true },
  preview: { host: "0.0.0.0", port: 9050, strictPort: true },
});
