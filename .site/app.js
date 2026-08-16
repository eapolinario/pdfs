"use strict";

// The query string in the search box is the single source of truth: tag chips,
// the URL and the rendered list are all derived from it.

const FIELDS = {
  tag: "tags",
  tags: "tags",
  author: "authors",
  year: "year",
  title: "title",
  note: "notes",
  notes: "notes",
};

const HIGHLIGHTED_FIELDS = new Set(["authors", "title", "notes"]);

const el = {
  q: document.getElementById("q"),
  tags: document.getElementById("tags"),
  sort: document.getElementById("sort"),
  count: document.getElementById("count"),
  results: document.getElementById("results"),
  empty: document.getElementById("empty"),
  clear: document.getElementById("clear"),
  summary: document.getElementById("summary"),
  preview: document.getElementById("preview"),
  previewTitle: document.getElementById("preview-title"),
  previewOpen: document.getElementById("preview-open"),
  previewClose: document.getElementById("preview-close"),
  previewFrame: document.getElementById("preview-frame"),
};

let manifest = { entries: [], tags: [] };

/* Utilities ---------------------------------------------------------------- */

function esc(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// Escape text while wrapping every occurrence of a search term in <mark>.
function highlight(text, terms) {
  text = String(text);
  if (!terms.length) return esc(text);

  const lower = text.toLowerCase();
  const hits = [];
  for (const term of terms) {
    if (!term) continue;
    let at = lower.indexOf(term);
    while (at !== -1) {
      hits.push([at, at + term.length]);
      at = lower.indexOf(term, at + term.length);
    }
  }
  if (!hits.length) return esc(text);

  hits.sort((a, b) => a[0] - b[0]);
  const merged = [hits[0]];
  for (const [start, end] of hits.slice(1)) {
    const last = merged[merged.length - 1];
    if (start <= last[1]) last[1] = Math.max(last[1], end);
    else merged.push([start, end]);
  }

  let html = "";
  let pos = 0;
  for (const [start, end] of merged) {
    html += esc(text.slice(pos, start)) + "<mark>" + esc(text.slice(start, end)) + "</mark>";
    pos = end;
  }
  return html + esc(text.slice(pos));
}

function humanSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  const units = ["KB", "MB", "GB"];
  let value = bytes;
  for (const unit of units) {
    value /= 1024;
    if (value < 1024) return (value >= 10 ? value.toFixed(0) : value.toFixed(1)) + " " + unit;
  }
  return value.toFixed(1) + " TB";
}

/* Query parsing ------------------------------------------------------------ */

function tokenize(query) {
  const tokens = [];
  const re = /"([^"]*)"|(\S+)/g;
  let match;
  while ((match = re.exec(query)) !== null) {
    tokens.push(match[1] !== undefined ? match[1] : match[2]);
  }
  return tokens.filter(Boolean);
}

function parseQuery(query) {
  const terms = [];
  const filters = [];
  for (const token of tokenize(query)) {
    const at = token.indexOf(":");
    if (at > 0) {
      const field = FIELDS[token.slice(0, at).toLowerCase()];
      const value = token.slice(at + 1).toLowerCase();
      if (field && value) {
        filters.push({ field, value });
        continue;
      }
    }
    terms.push(token.toLowerCase());
  }
  return { terms, filters };
}

function haystack(entry) {
  if (entry._hay === undefined) {
    entry._hay = [
      entry.title, entry.authors, entry.year, entry.tags.join(" "),
      entry.notes, entry.path,
    ].join(" \u0000 ").toLowerCase();
  }
  return entry._hay;
}

function matches(entry, query) {
  for (const term of query.terms) {
    if (!haystack(entry).includes(term)) return false;
  }
  for (const { field, value } of query.filters) {
    if (field === "tags") {
      if (!entry.tags.some((tag) => tag.toLowerCase() === value || tag.toLowerCase().includes(value))) {
        return false;
      }
    } else if (field === "year") {
      if (!String(entry.year).includes(value)) return false;
    } else if (!String(entry[field]).toLowerCase().includes(value)) {
      return false;
    }
  }
  return true;
}

// Terms worth highlighting: free words plus the values of text-ish filters.
function highlightTerms(query) {
  const terms = query.terms.slice();
  for (const { field, value } of query.filters) {
    if (HIGHLIGHTED_FIELDS.has(field)) terms.push(value);
  }
  return terms;
}

/* Sorting ------------------------------------------------------------------ */

const SORTS = {
  "added-desc": (a, b) => b.added.localeCompare(a.added) || a.title.localeCompare(b.title),
  "year-desc": (a, b) => b.year - a.year || a.title.localeCompare(b.title),
  "year-asc": (a, b) => a.year - b.year || a.title.localeCompare(b.title),
  "title-asc": (a, b) => a.title.localeCompare(b.title),
  "pages-desc": (a, b) => b.pages - a.pages || a.title.localeCompare(b.title),
  "pages-asc": (a, b) => a.pages - b.pages || a.title.localeCompare(b.title),
};

/* Rendering ---------------------------------------------------------------- */

function activeTags(query) {
  return new Set(query.filters.filter((f) => f.field === "tags").map((f) => f.value));
}

function renderChips(query) {
  const active = activeTags(query);
  el.tags.innerHTML = manifest.tags
    .map(
      (tag) =>
        `<button type="button" class="chip" data-tag="${esc(tag.name)}" ` +
        `aria-pressed="${active.has(tag.name.toLowerCase())}">` +
        `${esc(tag.name)}<span class="n">${tag.count}</span></button>`
    )
    .join("");
}

function renderEntry(entry, terms) {
  const pdf = esc(entry.path);
  const tags = entry.tags
    .map((tag) => `<button type="button" class="chip" data-tag="${esc(tag)}">${esc(tag)}</button>`)
    .join("");

  return (
    `<li class="entry">` +
    `<h2><a href="${pdf}">${highlight(entry.title, terms)}</a></h2>` +
    `<p class="meta">${highlight(entry.authors, terms)} &middot; ${highlight(entry.year, terms)} ` +
    `&middot; ${entry.pages} pp &middot; ${esc(entry.size)}</p>` +
    `<p class="notes">${highlight(entry.notes, terms)}</p>` +
    `<div class="tags">${tags}</div>` +
    `<div class="actions">` +
    `<a href="${pdf}">Open PDF</a>` +
    `<button type="button" data-preview="${pdf}" data-title="${esc(entry.title)}">Preview</button>` +
    `<a href="${esc(entry.source)}" target="_blank" rel="noopener">Source</a>` +
    `</div></li>`
  );
}

function render() {
  const raw = el.q.value.trim();
  const query = parseQuery(raw);
  const terms = highlightTerms(query);

  const shown = manifest.entries
    .filter((entry) => matches(entry, query))
    .sort(SORTS[el.sort.value] || SORTS["added-desc"]);

  el.results.innerHTML = shown.map((entry) => renderEntry(entry, terms)).join("");
  el.empty.hidden = shown.length > 0 || manifest.entries.length === 0;

  const pages = shown.reduce((sum, entry) => sum + entry.pages, 0);
  const bytes = shown.reduce((sum, entry) => sum + (entry.bytes || 0), 0);
  const scope = shown.length === manifest.entries.length
    ? `${shown.length} document${shown.length === 1 ? "" : "s"}`
    : `${shown.length} of ${manifest.entries.length} documents`;
  el.count.textContent = `${scope} \u00b7 ${pages} pages \u00b7 ${humanSize(bytes)}`;

  renderChips(query);

  const url = new URL(location.href);
  if (raw) url.searchParams.set("q", raw);
  else url.searchParams.delete("q");
  if (el.sort.value !== "added-desc") url.searchParams.set("sort", el.sort.value);
  else url.searchParams.delete("sort");
  history.replaceState(null, "", url);
}

/* Interaction -------------------------------------------------------------- */

function toggleTag(name) {
  const wanted = `tag:${name}`;
  const tokens = tokenize(el.q.value);
  const kept = tokens.filter((token) => token.toLowerCase() !== wanted.toLowerCase());
  el.q.value = (kept.length === tokens.length ? tokens.concat(wanted) : kept).join(" ");
  render();
}

function openPreview(path, title) {
  el.previewTitle.textContent = title;
  el.previewOpen.href = path;
  el.previewFrame.src = path;
  if (typeof el.preview.showModal === "function") el.preview.showModal();
  else window.open(path, "_blank");
}

document.addEventListener("click", (event) => {
  const chip = event.target.closest("[data-tag]");
  if (chip) {
    toggleTag(chip.dataset.tag);
    return;
  }
  const preview = event.target.closest("[data-preview]");
  if (preview) openPreview(preview.dataset.preview, preview.dataset.title);
});

el.q.addEventListener("input", render);
el.sort.addEventListener("change", render);
el.clear.addEventListener("click", () => {
  el.q.value = "";
  render();
  el.q.focus();
});

el.previewClose.addEventListener("click", () => el.preview.close());
el.preview.addEventListener("close", () => {
  el.previewFrame.removeAttribute("src");
});
el.preview.addEventListener("click", (event) => {
  if (event.target === el.preview) el.preview.close();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "/" && document.activeElement !== el.q) {
    event.preventDefault();
    el.q.focus();
    el.q.select();
  } else if (event.key === "Escape" && document.activeElement === el.q && el.q.value) {
    el.q.value = "";
    render();
  }
});

/* Boot --------------------------------------------------------------------- */

fetch("manifest.json")
  .then((response) => {
    if (!response.ok) throw new Error(`manifest.json: ${response.status}`);
    return response.json();
  })
  .then((data) => {
    manifest = data;
    const params = new URLSearchParams(location.search);
    el.q.value = params.get("q") || "";
    if (params.get("sort") && SORTS[params.get("sort")]) el.sort.value = params.get("sort");

    el.summary.textContent =
      `${data.count} document${data.count === 1 ? "" : "s"}, ${data.totalPages} pages, ` +
      `${data.totalSize}. Last built ${data.generated.slice(0, 10)}.`;
    render();
  })
  .catch((error) => {
    el.results.innerHTML =
      `<li class="entry">Could not load the index: ${esc(error.message)}</li>`;
  });
