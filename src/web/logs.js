const rows = document.getElementById("rows");
const count = document.getElementById("count");
const sortButtons = document.querySelectorAll("[data-sort]");
const detail = document.getElementById("detail");

let attempts = [];
let seen = null;
let signature = "";
let sort = loadSort();
let openId = null;

const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

// The chosen sort is remembered for next time (if storage is available)
function loadSort() {
  try {
    const saved = JSON.parse(localStorage.getItem("logsSort"));
    if (saved && saved.key && saved.dir) return saved;
  } catch { /* storage unavailable */ }
  return { key: "time", dir: "desc" };
}

function saveSort() {
  try { localStorage.setItem("logsSort", JSON.stringify(sort)); } catch { /* storage unavailable */ }
}

function sorted() {
  const list = [...attempts].sort((a, b) => collator.compare(String(a[sort.key] ?? ""), String(b[sort.key] ?? "")));
  return sort.dir === "desc" ? list.reverse() : list;
}

function formatTime(iso, long = false) {
  const date = new Date(iso);
  if (isNaN(date)) return iso;
  return long ? date.toLocaleString() : date.toLocaleString(undefined, { month: "numeric", day: "numeric", hour: "numeric", minute: "2-digit" });
}

function cell(text, className) {
  const td = document.createElement("td");
  if (className) td.className = className;
  const inner = document.createElement("div");
  inner.textContent = text;
  td.append(inner);
  return td;
}

function renderHeaders() {
  sortButtons.forEach((button) => {
    const active = button.dataset.sort === sort.key;
    button.classList.toggle("active", active);
    button.dataset.dir = active ? sort.dir : "";
    button.closest("th").setAttribute("aria-sort", active ? (sort.dir === "asc" ? "ascending" : "descending") : "none");
  });
}

function render(fresh = new Set()) {
  renderHeaders();
  count.textContent = `${attempts.length} ${attempts.length === 1 ? "attempt" : "attempts"}`;

  if (!attempts.length) {
    const tr = document.createElement("tr");
    const td = cell("No attempts logged yet.", "empty-row");
    td.colSpan = 7;
    tr.append(td);
    rows.replaceChildren(tr);
    return;
  }

  rows.replaceChildren(...sorted().map((a) => {
    const tr = document.createElement("tr");
    tr.tabIndex = 0;
    if (fresh.has(a.id)) tr.classList.add("new");
    tr.append(
      cell(formatTime(a.time), "mono"),
      cell(a.ip, "mono"),
      cell(a.city, "place"),
      cell(a.state, "place"),
      cell(a.stage, "stage"),
      cell(a.reason, "reason"),
      cell(a.message, "excerpt"),
    );
    tr.addEventListener("click", () => openDetail(a.id));
    tr.addEventListener("keydown", (event) => { if (event.key === "Enter") openDetail(a.id); });
    return tr;
  }));
}

async function refresh() {
  let latest;
  try {
    latest = (await window.pywebview.api.attempts()).attempts;
  } catch {
    count.textContent = "Offline";
    count.previousElementSibling.classList.remove("on");
    return;
  }
  count.previousElementSibling.classList.add("on");

  // Only redraw when something changed, so the table doesn't jump while you read it
  const ids = latest.map((a) => a.id);
  const next = ids.join(",");
  if (next === signature) return;
  signature = next;

  // Rows that weren't there last time get highlighted (but not on first load)
  const fresh = seen ? new Set(ids.filter((id) => !seen.has(id))) : new Set();
  seen = new Set(ids);
  attempts = latest;
  render(fresh);
}

sortButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const key = button.dataset.sort;
    if (sort.key === key) {
      sort.dir = sort.dir === "asc" ? "desc" : "asc";
    } else {
      // Newest first is the natural start for time; A to Z for everything else
      sort = { key, dir: key === "time" ? "desc" : "asc" };
    }
    saveSort();
    render();
  });
});

// Detail view

async function openDetail(id) {
  let entry;
  try {
    entry = await window.pywebview.api.attempt(id);
  } catch {
    return;
  }
  if (entry.error) return;
  openId = id;

  const fields = document.getElementById("detail-fields");
  fields.replaceChildren();
  [
    ["Time", formatTime(entry.time, true)],
    ["IP", entry.ip],
    ["City", entry.city],
    ["State", entry.state],
    ["Caught by", entry.stage],
    ["Reason", entry.reason],
  ].forEach(([label, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value;
    fields.append(dt, dd);
  });

  document.getElementById("detail-message").textContent = entry.message;
  document.getElementById("detail-length").textContent = `${entry.message.length.toLocaleString()} characters`;
  document.getElementById("detail-copy").textContent = "Copy message";

  // Previous and next follow the table's current sort order
  const order = sorted().map((a) => a.id);
  const position = order.indexOf(id);
  document.getElementById("detail-prev").disabled = position <= 0;
  document.getElementById("detail-next").disabled = position === -1 || position >= order.length - 1;

  detail.hidden = false;
  document.getElementById("detail-message").scrollTop = 0;
}

function step(offset) {
  const order = sorted().map((a) => a.id);
  const target = order[order.indexOf(openId) + offset];
  if (target !== undefined) openDetail(target);
}

function closeDetail() {
  detail.hidden = true;
  openId = null;
}

async function copyMessage() {
  const text = document.getElementById("detail-message").textContent;
  const button = document.getElementById("detail-copy");
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    // Older fallback if the clipboard API isn't allowed
    const area = document.createElement("textarea");
    area.value = text;
    document.body.append(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }
  button.textContent = "Copied";
}

document.getElementById("detail-close").addEventListener("click", closeDetail);
document.getElementById("detail-prev").addEventListener("click", () => step(-1));
document.getElementById("detail-next").addEventListener("click", () => step(1));
document.getElementById("detail-copy").addEventListener("click", copyMessage);
detail.addEventListener("click", (event) => { if (event.target === detail) closeDetail(); });
document.addEventListener("keydown", (event) => {
  if (detail.hidden) return;
  if (event.key === "Escape") closeDetail();
  if (event.key === "ArrowUp") { event.preventDefault(); step(-1); }
  if (event.key === "ArrowDown") { event.preventDefault(); step(1); }
});

renderHeaders();

// pywebview connects the Python side shortly after the page loads
window.addEventListener("pywebviewready", () => {
  refresh();
  setInterval(refresh, 2000);
});
