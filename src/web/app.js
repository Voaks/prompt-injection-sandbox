const thread = document.getElementById("thread");
const scroller = document.getElementById("messages");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendButton = document.getElementById("send");
const fileInput = document.getElementById("file-input");
const pendingList = document.getElementById("pending-files");

let messages = [];
let pendingFiles = [];
let editing = null;
let editError = "";
let busy = false;

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// Claude's replies are rendered as Markdown. Everything is sanitized, and images are
// stripped, because an injected reply could use an image URL to send data to another site.
function setReply(node, text) {
  if (window.marked && window.DOMPurify) {
    node.innerHTML = DOMPurify.sanitize(marked.parse(text), { FORBID_TAGS: ["img", "style"] });
  } else {
    node.classList.add("plain");
    node.textContent = text;
  }
}

function render() {
  thread.replaceChildren();

  document.getElementById("status-dot").classList.toggle("on", busy);

  if (!messages.length && !busy) {
    const empty = el("div", "empty");
    const ring = el("div", "ring");
    ring.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"><path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6l7-3z"/></svg>';
    empty.append(ring, el("div", "hint", "Say something  ·  Try to break it"));
    thread.append(empty);
  }

  messages.forEach((message, i) => thread.append(renderMessage(message, i)));

  if (busy) {
    const dots = el("div", "msg assistant");
    const thinking = el("div", "thinking");
    thinking.append(el("span"), el("span"), el("span"));
    dots.append(thinking);
    thread.append(dots);
  }

  scroller.scrollTop = scroller.scrollHeight;
}

function renderMessage(message, i) {
  const wrap = el("div", `msg ${message.role}`);

  if (editing === i) {
    const box = el("textarea", "edit-box");
    box.value = message.text;
    const actions = el("div", "edit-actions");
    const save = el("button", "btn primary", "Save");
    const cancel = el("button", "btn", "Cancel");
    save.onclick = () => saveEdit(i, box.value, save);
    cancel.onclick = () => { editing = null; editError = ""; render(); };
    actions.append(save, cancel);
    wrap.append(box, actions);
    if (editError) wrap.append(el("div", "edit-error", editError));
    setTimeout(() => box.focus(), 0);
    return wrap;
  }

  if (message.text) {
    const body = el("div", "body");
    if (message.role === "assistant") setReply(body, message.text);
    else body.textContent = message.text;
    wrap.append(body);
  }

  if (message.files.length) {
    const files = el("div", "files");
    message.files.forEach((name) => files.append(el("span", "chip", name)));
    wrap.append(files);
  }

  if (message.edited || message.editable) {
    const meta = el("div", "msg-meta");
    if (message.edited) meta.append(el("span", "", "edited"));
    if (message.editable && !busy) {
      const edit = el("button", "link", "Edit");
      edit.type = "button";
      edit.onclick = () => { editing = i; editError = ""; render(); };
      meta.append(edit);
    }
    wrap.append(meta);
  }

  return wrap;
}

function renderPendingFiles() {
  pendingList.replaceChildren();
  pendingFiles.forEach((file, i) => {
    const chip = el("span", "chip", file.name);
    const remove = el("button", "", "×");
    remove.type = "button";
    remove.title = "Remove";
    remove.onclick = () => { pendingFiles.splice(i, 1); renderPendingFiles(); };
    chip.append(remove);
    pendingList.append(chip);
  });
}

// Calls a method on the Python Api class (src/api.py)
async function api(name, ...args) {
  const result = await window.pywebview.api[name](...args);
  if (result.error) throw new Error(result.error);
  return result;
}

// Python can't read the browser's File objects, so files are sent as base64 text
function readFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve({ name: file.name, data: reader.result.split(",")[1] });
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

async function send(event) {
  event.preventDefault();
  const text = input.value.trim();
  if (busy || (!text && !pendingFiles.length)) return;

  const files = pendingFiles;

  // Show the message straight away while waiting for the reply
  messages.push({ role: "user", text, files: files.map((f) => f.name), editable: false, edited: false });
  input.value = "";
  autosize();
  pendingFiles = [];
  renderPendingFiles();
  editing = null;
  busy = true;
  sendButton.disabled = true;
  render();

  try {
    const encoded = await Promise.all(files.map(readFile));
    messages = (await api("chat", text, encoded)).messages;
  } catch (err) {
    messages.push({ role: "assistant", text: `Something went wrong: ${err.message}`, files: [], editable: false, edited: false });
  } finally {
    busy = false;
    sendButton.disabled = false;
    render();
    input.focus();
  }
}

async function saveEdit(index, text, button) {
  button.disabled = true;
  try {
    messages = (await api("edit", index, text)).messages;
    editing = null;
    editError = "";
  } catch (err) {
    editError = err.message;
  }
  render();
}

function autosize() {
  input.style.height = "auto";
  input.style.height = `${input.scrollHeight}px`;
}

form.addEventListener("submit", send);

input.addEventListener("input", autosize);
input.addEventListener("keydown", (event) => {
  // Enter sends, Shift+Enter adds a new line
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});

fileInput.addEventListener("change", () => {
  pendingFiles.push(...fileInput.files);
  fileInput.value = "";
  renderPendingFiles();
});

document.getElementById("reset").addEventListener("click", async () => {
  if (busy) return;
  messages = (await api("reset")).messages;
  editing = null;
  render();
});

// pywebview connects the Python side shortly after the page loads
window.addEventListener("pywebviewready", async () => {
  const state = await api("state");
  document.getElementById("model").textContent = state.model;
  fileInput.accept = state.allowed_types.map((t) => `.${t}`).join(",");
  messages = state.messages;
  render();
});

render();
