const rows = document.getElementById("rows");
const count = document.getElementById("count");
let seen = null;

function cell(text, className) {
  const td = document.createElement("td");
  if (className) td.className = className;
  td.textContent = text;
  return td;
}

function formatTime(iso) {
  const date = new Date(iso);
  return isNaN(date) ? iso : date.toLocaleString();
}

async function refresh() {
  let attempts;
  try {
    attempts = (await window.pywebview.api.attempts()).attempts;
  } catch {
    count.textContent = "Offline";
    count.previousElementSibling.classList.remove("on");
    return;
  }

  // Rows that weren't there last time get highlighted (but not on first load)
  const keys = attempts.map((a) => a.time + a.ip + a.excerpt);
  const fresh = seen ? new Set(keys.filter((k) => !seen.has(k))) : new Set();
  seen = new Set(keys);

  count.previousElementSibling.classList.add("on");
  count.textContent = `${attempts.length} ${attempts.length === 1 ? "attempt" : "attempts"}`;

  if (!attempts.length) {
    const tr = document.createElement("tr");
    const td = cell("No attempts logged yet.", "empty-row");
    td.colSpan = 7;
    tr.append(td);
    rows.replaceChildren(tr);
    return;
  }

  rows.replaceChildren(...attempts.map((a, i) => {
    const tr = document.createElement("tr");
    if (fresh.has(keys[i])) tr.className = "new";
    tr.append(
      cell(formatTime(a.time), "mono"),
      cell(a.ip, "mono"),
      cell(a.city),
      cell(a.state),
      cell(a.stage, "stage"),
      cell(a.reason, "reason"),
      cell(a.excerpt, "excerpt"),
    );
    return tr;
  }));
}

// pywebview connects the Python side shortly after the page loads
window.addEventListener("pywebviewready", () => {
  refresh();
  setInterval(refresh, 2000);
});
