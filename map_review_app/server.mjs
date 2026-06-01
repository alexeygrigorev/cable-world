import { createServer } from "node:http";
import { mkdir, open, readFile, readdir, stat, writeFile } from "node:fs/promises";
import { createReadStream } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const APP_DIR = path.join(ROOT, "map_review_app", "static");
const REVIEW_DIR = path.join(ROOT, "assets", "map", "review");
const FEEDBACK_DIR = path.join(ROOT, "tmp", "map-review-feedback");
const HOST = process.env.HOST ?? "127.0.0.1";
const PORT = Number(process.env.PORT ?? "9010");

const CONTENT_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
};

function sendJson(response, status, body) {
  response.writeHead(status, {
    "Content-Type": CONTENT_TYPES[".json"],
    "Cache-Control": "no-store",
  });
  response.end(JSON.stringify(body));
}

async function readRequestJson(request) {
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
    const size = chunks.reduce((total, item) => total + item.length, 0);
    if (size > 1024 * 1024) {
      throw new Error("Request body is too large");
    }
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
}

async function listPreviewImages(directory, urlPrefix) {
  const entries = (await readdir(directory)).sort();
  const images = [];
  for (const name of entries) {
    const match = name.match(/(?:^|_)(\d{3})\.png$/);
    if (!match) {
      continue;
    }
    const filePath = path.join(directory, name);
    const fileStat = await stat(filePath);
    const dimensions = await readPngDimensions(filePath);
    images.push({
      id: match[1],
      label: `${Number(match[1])}%`,
      name,
      width: dimensions.width,
      height: dimensions.height,
      sizeBytes: fileStat.size,
      updatedAt: fileStat.mtime.toISOString(),
      url: `${urlPrefix}/${name}?t=${Number(fileStat.mtimeMs).toFixed(0)}`,
    });
  }
  images.sort((a, b) => Number(a.id) - Number(b.id));
  return images;
}

async function readPngDimensions(filePath) {
  const file = await open(filePath, "r");
  try {
    const buffer = Buffer.alloc(24);
    await file.read(buffer, 0, buffer.length, 0);
    const pngSignature = "89504e470d0a1a0a";
    if (buffer.subarray(0, 8).toString("hex") !== pngSignature) {
      return { width: null, height: null };
    }
    return {
      width: buffer.readUInt32BE(16),
      height: buffer.readUInt32BE(20),
    };
  } finally {
    await file.close();
  }
}

async function readReviewManifest() {
  try {
    const text = await readFile(path.join(REVIEW_DIR, "manifest.json"), "utf8");
    const manifest = JSON.parse(text);
    const tabs = Array.isArray(manifest.tabs) ? manifest.tabs : [];
    return new Map(tabs.map((tab) => [String(tab.id), tab]));
  } catch (error) {
    if (error.code === "ENOENT") {
      return new Map();
    }
    throw error;
  }
}

async function readReviewSetMetadata(directory) {
  for (const name of ["review.yml", "review.json"]) {
    try {
      const text = await readFile(path.join(directory, name), "utf8");
      return JSON.parse(text);
    } catch (error) {
      if (error.code === "ENOENT") {
        continue;
      }
      throw error;
    }
  }
  return {};
}

async function listReviewTabs() {
  const tabs = [];
  const manifestTabs = await readReviewManifest();
  const rootImages = await listPreviewImages(REVIEW_DIR, "/review");
  if (rootImages.length > 0) {
    const metadata = manifestTabs.get("full-map") ?? {};
    tabs.push({
      id: "full-map",
      title: metadata.title ?? "Full map",
      description: metadata.description ?? "Current generated map texture at review zoom levels.",
      images: rootImages,
    });
  }

  const entries = (await readdir(REVIEW_DIR, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name));
  for (const entry of entries) {
    if (!entry.isDirectory()) {
      continue;
    }
    const id = entry.name.replace(/[^a-zA-Z0-9_-]/g, "-");
    const directory = path.join(REVIEW_DIR, entry.name);
    const images = await listPreviewImages(directory, `/review/${entry.name}`);
    if (images.length === 0) {
      continue;
    }
    const review = await readReviewSetMetadata(directory);
    const metadata = manifestTabs.get(id) ?? {};
    tabs.push({
      id,
      title: review.title ?? metadata.title ?? entry.name.replaceAll("_", " "),
      description: review.description ?? metadata.description ?? `Review set: ${entry.name}`,
      review,
      images,
    });
  }
  return tabs;
}

async function saveFeedback(payload) {
  const now = new Date();
  await mkdir(FEEDBACK_DIR, { recursive: true });
  await writeFile(path.join(FEEDBACK_DIR, ".keep"), "", { flag: "a" });
  const stamp = now.toISOString().replaceAll(":", "-").replace(/\.\d{3}Z$/, "Z");
  const tabs = Array.isArray(payload.tabs) ? payload.tabs : [];
  const jsonPath = path.join(FEEDBACK_DIR, `${stamp}.json`);
  const markdownPath = path.join(FEEDBACK_DIR, `${stamp}.md`);
  const filledTabs = tabs
    .map((tab) => ({
      id: String(tab.id ?? ""),
      title: String(tab.title ?? ""),
      feedback: String(tab.feedback ?? "").trim(),
      images: Array.isArray(tab.images) ? tab.images : [],
      review: tab.review && typeof tab.review === "object" ? tab.review : {},
    }))
    .filter((tab) => tab.feedback.length > 0);
  if (filledTabs.length === 0) {
    throw new Error("No feedback text to save");
  }
  const data = {
    createdAt: now.toISOString(),
    tabs: filledTabs,
  };
  const markdown = ["# Map Review Feedback", "", `Created: ${data.createdAt}`, ""];
  for (const tab of data.tabs) {
    markdown.push(`## ${tab.title || tab.id || "Untitled"}`);
    if (Object.keys(tab.review).length > 0) {
      markdown.push("", "```json", JSON.stringify(tab.review, null, 2), "```");
    }
    markdown.push("", tab.feedback || "_No feedback text._", "");
  }
  await writeFile(jsonPath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
  await writeFile(markdownPath, `${markdown.join("\n")}\n`, "utf8");
  return {
    jsonPath: path.relative(ROOT, jsonPath),
    markdownPath: path.relative(ROOT, markdownPath),
  };
}

async function serveStatic(response, filePath) {
  const ext = path.extname(filePath);
  const contentType = CONTENT_TYPES[ext] ?? "application/octet-stream";
  const fileStat = await stat(filePath);
  response.writeHead(200, {
    "Content-Type": contentType,
    "Content-Length": fileStat.size,
    "Cache-Control": "no-store",
  });
  createReadStream(filePath).pipe(response);
}

async function handle(request, response) {
  const url = new URL(request.url ?? "/", `http://${HOST}:${PORT}`);
  try {
    if (request.method === "GET" && url.pathname === "/api/review-tabs") {
      sendJson(response, 200, { tabs: await listReviewTabs() });
      return;
    }
    if (request.method === "POST" && url.pathname === "/api/feedback") {
      const saved = await saveFeedback(await readRequestJson(request));
      sendJson(response, 200, { ok: true, saved });
      return;
    }
    if (request.method === "GET" && url.pathname.startsWith("/review/")) {
      const relativePath = decodeURIComponent(url.pathname.replace(/^\/review\//, ""));
      const resolvedPath = path.resolve(REVIEW_DIR, relativePath);
      const pathFromReviewDir = path.relative(REVIEW_DIR, resolvedPath);
      if (pathFromReviewDir.startsWith("..") || path.isAbsolute(pathFromReviewDir)) {
        sendJson(response, 403, { error: "Forbidden" });
        return;
      }
      await serveStatic(response, resolvedPath);
      return;
    }
    if (request.method === "GET") {
      const name = url.pathname === "/" ? "index.html" : path.basename(decodeURIComponent(url.pathname));
      await serveStatic(response, path.join(APP_DIR, name));
      return;
    }
    sendJson(response, 405, { error: "Method not allowed" });
  } catch (error) {
    if (error.code === "ENOENT") {
      sendJson(response, 404, { error: "Not found" });
    } else {
      sendJson(response, 500, { error: error.message });
    }
  }
}

createServer(handle).listen(PORT, HOST, () => {
  console.log(`Map review app: http://${HOST}:${PORT}/`);
});
