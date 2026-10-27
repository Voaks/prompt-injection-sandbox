// Minimize and close buttons for the frameless desktop window
document.querySelectorAll("[data-window]").forEach((button) => {
  button.addEventListener("click", () => {
    if (window.pywebview) window.pywebview.api[button.dataset.window]();
  });
});

// Invisible grab areas on the edges and corners, since a frameless window has no
// border of its own to resize from. Keep in sync with MIN_SIZE in desktop.py.
const MIN_WIDTH = 560;
const MIN_HEIGHT = 480;

["n", "s", "e", "w", "ne", "nw", "se", "sw"].forEach((edge) => {
  const handle = document.createElement("div");
  handle.className = `resize resize-${edge}`;
  handle.addEventListener("mousedown", (event) => startResize(event, edge));
  document.body.append(handle);
});

function startResize(event, edge) {
  if (!window.pywebview || event.button !== 0) return;
  event.preventDefault();

  const start = {
    x: event.screenX,
    y: event.screenY,
    left: window.screenX,
    top: window.screenY,
    width: window.outerWidth,
    height: window.outerHeight,
  };
  let latest = event;
  let frame = null;

  function apply() {
    frame = null;
    const dx = latest.screenX - start.x;
    const dy = latest.screenY - start.y;
    let { left, top, width, height } = start;

    if (edge.includes("e")) width = Math.max(MIN_WIDTH, start.width + dx);
    if (edge.includes("s")) height = Math.max(MIN_HEIGHT, start.height + dy);
    if (edge.includes("w")) {
      width = Math.max(MIN_WIDTH, start.width - dx);
      left = start.left + start.width - width;
    }
    if (edge.includes("n")) {
      height = Math.max(MIN_HEIGHT, start.height - dy);
      top = start.top + start.height - height;
    }
    window.pywebview.api.set_bounds(left, top, width, height);
  }

  // At most one resize per screen refresh, however fast the mouse moves
  function onMove(moveEvent) {
    latest = moveEvent;
    if (!frame) frame = requestAnimationFrame(apply);
  }

  function onUp() {
    window.removeEventListener("mousemove", onMove);
    window.removeEventListener("mouseup", onUp);
  }

  window.addEventListener("mousemove", onMove);
  window.addEventListener("mouseup", onUp);
}
