const tabsElement = document.querySelector("#tabs");
const panelElement = document.querySelector("#panel");
const statusElement = document.querySelector("#status");
const saveButton = document.querySelector("#saveButton");
const lightbox = document.querySelector("#lightbox");
const lightboxTitle = document.querySelector("#lightboxTitle");
const lightboxViewport = document.querySelector("#lightboxViewport");
const lightboxImage = document.querySelector("#lightboxImage");
const zoomInButton = document.querySelector("#zoomInButton");
const zoomOutButton = document.querySelector("#zoomOutButton");
const zoomResetButton = document.querySelector("#zoomResetButton");

let tabs = [];
let activeTabId = "";
const feedbackByTab = new Map();
let lightboxScale = 1;
let lightboxOffset = { x: 0, y: 0 };
let dragState = null;

function setStatus(message) {
  statusElement.textContent = message;
}

function formatBytes(value) {
  if (value > 1024 * 1024) {
    return `${(value / 1024 / 1024).toFixed(1)} MB`;
  }
  return `${Math.round(value / 1024)} KB`;
}

function formatDimensions(image) {
  if (!image.width || !image.height) {
    return formatBytes(image.sizeBytes);
  }
  return `${image.width}×${image.height} · ${formatBytes(image.sizeBytes)}`;
}

function renderTabs() {
  tabsElement.replaceChildren(
    ...tabs.map((tab, index) => {
      const button = document.createElement("button");
      button.className = "tabButton";
      if ((feedbackByTab.get(tab.id) ?? "").trim()) {
        button.classList.add("hasFeedback");
      }
      button.type = "button";
      const label = document.createElement("span");
      label.textContent = `${index + 1}. ${tab.title}`;
      const marker = document.createElement("span");
      marker.className = "feedbackMarker";
      marker.textContent = "saved draft";
      button.append(label, marker);
      button.setAttribute("aria-selected", String(tab.id === activeTabId));
      button.addEventListener("click", () => {
        activeTabId = tab.id;
        render();
      });
      return button;
    }),
  );
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function updateLightboxTransform() {
  lightboxImage.style.transform = `translate(calc(-50% + ${lightboxOffset.x}px), calc(-50% + ${lightboxOffset.y}px)) scale(${lightboxScale})`;
  zoomResetButton.textContent = `${Math.round(lightboxScale * 100)}%`;
}

function resetLightboxTransform() {
  lightboxScale = 1;
  lightboxOffset = { x: 0, y: 0 };
  updateLightboxTransform();
}

function zoomLightbox(delta, center = null) {
  const previousScale = lightboxScale;
  lightboxScale = clamp(lightboxScale * delta, 0.5, 6);
  if (center && previousScale !== lightboxScale) {
    const rect = lightboxViewport.getBoundingClientRect();
    const dx = center.x - rect.left - rect.width / 2 - lightboxOffset.x;
    const dy = center.y - rect.top - rect.height / 2 - lightboxOffset.y;
    const factor = lightboxScale / previousScale - 1;
    lightboxOffset.x -= dx * factor;
    lightboxOffset.y -= dy * factor;
  }
  updateLightboxTransform();
}

function openLightbox(tab, image) {
  lightboxTitle.textContent = `${tab.title} · ${image.label}`;
  lightboxImage.src = image.url;
  lightboxImage.alt = `${tab.title} ${image.label}`;
  resetLightboxTransform();
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
  const feedbackTarget = tab.review?.feedbackTarget ? ` Target: ${tab.review.feedbackTarget}` : "";
  description.textContent = `${tab.description}${feedbackTarget}`;
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
    button.addEventListener("click", () => openLightbox(tab, image));
    const img = document.createElement("img");
    img.src = image.url;
    img.alt = `${tab.title} ${image.label}`;
    button.append(img);

    const meta = document.createElement("div");
    meta.className = "previewMeta";
    const label = document.createElement("strong");
    label.textContent = image.label;
    const size = document.createElement("span");
    size.textContent = formatDimensions(image);
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
    renderTabs();
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
  const filledTabs = tabs
    .map((tab) => ({
      id: tab.id,
      title: tab.title,
      review: tab.review ?? {},
      images: tab.images.map((image) => ({
        name: image.name,
        label: image.label,
        width: image.width,
        height: image.height,
      })),
      feedback: (feedbackByTab.get(tab.id) ?? "").trim(),
    }))
    .filter((tab) => tab.feedback.length > 0);
  if (filledTabs.length === 0) {
    setStatus("Nothing to save: add feedback to at least one tab.");
    return;
  }
  const payload = {
    tabs: filledTabs,
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
  setStatus(`Saved ${filledTabs.length} tab(s): ${data.saved.markdownPath}`);
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

zoomInButton.addEventListener("click", () => zoomLightbox(1.25));
zoomOutButton.addEventListener("click", () => zoomLightbox(0.8));
zoomResetButton.addEventListener("click", resetLightboxTransform);

lightboxViewport.addEventListener("wheel", (event) => {
  event.preventDefault();
  zoomLightbox(event.deltaY < 0 ? 1.12 : 0.89, { x: event.clientX, y: event.clientY });
});

lightboxViewport.addEventListener("pointerdown", (event) => {
  lightboxViewport.setPointerCapture(event.pointerId);
  lightboxViewport.classList.add("isDragging");
  dragState = {
    pointerId: event.pointerId,
    startX: event.clientX,
    startY: event.clientY,
    offsetX: lightboxOffset.x,
    offsetY: lightboxOffset.y,
  };
});

lightboxViewport.addEventListener("pointermove", (event) => {
  if (!dragState || dragState.pointerId !== event.pointerId) {
    return;
  }
  lightboxOffset = {
    x: dragState.offsetX + event.clientX - dragState.startX,
    y: dragState.offsetY + event.clientY - dragState.startY,
  };
  updateLightboxTransform();
});

function endLightboxDrag(event) {
  if (dragState?.pointerId === event.pointerId) {
    dragState = null;
    lightboxViewport.classList.remove("isDragging");
  }
}

lightboxViewport.addEventListener("pointerup", endLightboxDrag);
lightboxViewport.addEventListener("pointercancel", endLightboxDrag);

lightbox.addEventListener("close", () => {
  lightboxImage.removeAttribute("src");
  dragState = null;
  lightboxViewport.classList.remove("isDragging");
});

loadTabs().catch((error) => setStatus(error.message));
