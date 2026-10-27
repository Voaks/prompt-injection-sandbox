import ctypes
from pathlib import Path

import webview

from src.api import Api

WEB_DIR = Path(__file__).parent / "web"

# Smallest the window can be resized to (also used by the resize handles in window.js)
MIN_SIZE = (560, 480)

# Win32 constants
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_DONOTROUND = 1
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010


def window_handle():
    return webview.windows[0].native.Handle.ToInt32()


def make_corners_sharp():
    """Windows 11 rounds every window's corners by default. Ask it not to for this one."""
    preference = ctypes.c_int(DWMWCP_DONOTROUND)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        window_handle(), DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(preference), ctypes.sizeof(preference)
    )


class DesktopApi(Api):
    """The chat API plus the window controls a frameless window needs."""

    def minimize(self):
        webview.windows[0].minimize()

    def close(self):
        webview.windows[0].destroy()

    def set_bounds(self, x, y, width, height):
        """Move and resize in one step, so dragging the left or top edge doesn't flicker.

        The page sends logical pixels; Windows wants physical ones.
        """
        hwnd = window_handle()
        scale = ctypes.windll.user32.GetDpiForWindow(hwnd) / 96
        width = max(width, MIN_SIZE[0])
        height = max(height, MIN_SIZE[1])
        ctypes.windll.user32.SetWindowPos(
            hwnd, None,
            round(x * scale), round(y * scale), round(width * scale), round(height * scale),
            SWP_NOZORDER | SWP_NOACTIVATE,
        )


def main():
    window = webview.create_window(
        "Sandbox",
        str(WEB_DIR / "index.html"),
        width=900,
        height=720,
        min_size=MIN_SIZE,
        frameless=True,
        easy_drag=False,
        background_color="#0f0f0f",
        js_api=DesktopApi(),
    )
    window.events.shown += make_corners_sharp
    webview.start()


if __name__ == "__main__":
    main()
