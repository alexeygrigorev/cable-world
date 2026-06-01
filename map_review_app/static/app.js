const tabsElement = document.querySelector("#tabs");
const panelElement = document.querySelector("#panel");
const statusElement = document.querySelector("#status");
const saveButton = document.querySelector("#saveButton");
const lightbox = document.querySelector("#lightbox");
const lightboxImage = document.querySelector("#lightboxImage");

let tabs = [];
let activeTabId = "";
const feedbackByTab = new Map();

function setStatus(message) {
  statusElement.textContent = message;
}

function formatBytes(value) {
  if (value > 1024 * 1024) {
    return `${(value / 1024 / 1024).toFixed(1)} MB`;
  }
  return `${Math.round(value / 1024)} KB`;
}

function renderTabs() {
  tabsElement.replaceChildren(
    ...tabs.map((tab, index) => {
      const button = document.createElement("button");
      button.className = "tabButton";
      button.type = "button";
      button.textContent = `${index + 1}. ${tab.title}`;
      button.setAttribute("aria-selected", String(tab.id === activeTabId));
      button.addEventListener("click", () => {
        activeTabId = tab.id;
        render();
      });
      return button;
    }),
  );
}

function openLightbox(image) {
  lightboxImage.src = image.url;
  lightboxImage.alt = image.label;
  lightbox.showModal();
}

function renderPanel() {
  const tab = tabs.find((item) => item.id === activeTabId);
  if (!tab) {
    panelElement.textContent = "No review images found. Run map_pipeline.render_map_previews first.";
    return;
  }

  const header = document.createElement("div");
  header.className = "panelHeader";
  const titleBlock = document.createElement("div");
  const title = document.createElement("h2");
  title.textContent = tab.title;
  const description = document.createElement("p");
  description.textContent = tab.description;
  titleBlock.append(title, description);
  const count = document.createElement("p");
  count.textContent = `${tab.images.length} images`;
  header.append(titleBlock, count);

  const grid = document.createElement("div");
  grid.className = "grid";
  for (const image of tab.images) {
    const card = document.createElement("article");
    card.className = "previewCard";
    const button = document.createElement("button");
    button.className = "previewButton";
    button.type = "button";
    button.addEventListener("click", () => openLightbox(image));
    const img = document.createElement("img");
    img.src = image.url;
    img.alt = `${tab.title} ${image.label}`;
    button.append(img);

    const meta = document.createElement("div");
    meta.className = "previewMeta";
    const label = document.createElement("strong");
    label.textContent = image.label;
    const size = document.createElement("span");
    size.textContent = formatBytes(image.sizeBytes);
    meta.append(label, size);
    card.append(button, meta);
    grid.append(card);
  }

  const textarea = document.createElement("textarea");
  textarea.className = "feedback";
  textarea.placeholder = `Feedback for ${tab.title}`;
  textarea.value = feedbackByTab.get(tab.id) ?? "";
  textarea.addEventListener("input", () => {
    feedbackByTab.set(tab.id, textarea.value);
  });

  panelElement.replaceChildren(header, grid, textarea);
}

function render() {
  renderTabs();
  renderPanel();
}

async function loadTabs() {
  const response = await fetch("/api/review-tabs", { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load tabs: ${response.status}`);
  }
  const data = await response.json();
  tabs = data.tabs ?? [];
  activeTabId = tabs[0]?.id ?? "";
  render();
}

async function saveFeedback() {
  const payload = {
    tabs: tabs.map((tab) => ({
      id: tab.id,
      title: tab.title,
      images: tab.images.map((image) => image.name),
      feedback: feedbackByTab.get(tab.id) ?? "",
    })),
  };
  const response = await fetch("/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error ?? `Save failed: ${response.status}`);
  }
  setStatus(`Saved: ${data.saved.markdownPath}`);
}

saveButton.addEventListener("click", () => {
  saveButton.disabled = true;
  setStatus("Saving...");
  saveFeedback()
    .catch((error) => setStatus(error.message))
    .finally(() => {
      saveButton.disabled = false;
    });
});

loadTabs().catch((error) => setStatus(error.message));
