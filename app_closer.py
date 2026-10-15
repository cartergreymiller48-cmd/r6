"""App Closer - run with:  python app_closer.py   (Windows)
Shows your open apps. Close one, or close them all with one click.
It "clicks the X" on each app, so apps with unsaved work will still ask
you to save instead of losing it."""
import ctypes
import os
import sys
import tkinter as tk
from ctypes import wintypes
from tkinter import messagebox

if sys.platform != "win32":
    sys.exit("App Closer only works on Windows.")

user32 = ctypes.windll.user32
dwm = ctypes.windll.dwmapi
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetWindow.restype = wintypes.HWND
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
dwm.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]

WM_CLOSE, GW_OWNER, GWL_EXSTYLE, WS_EX_TOOLWINDOW, DWMWA_CLOAKED = 0x0010, 4, -20, 0x80, 14
SKIP_CLASSES = {"Progman", "Shell_TrayWnd", "Shell_SecondaryTrayWnd", "WorkerW"}
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def open_apps():
    found = []

    def check(hwnd, _):
        if not user32.IsWindowVisible(hwnd) or user32.GetWindow(hwnd, GW_OWNER):
            return True
        if user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW:
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n == 0:
            return True
        title = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, title, n + 1)
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        if cls.value in SKIP_CLASSES:
            return True
        cloaked = wintypes.DWORD(0)
        dwm.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
        if cloaked.value:
            return True
        pid = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == os.getpid():
            return True
        found.append((hwnd, title.value))
        return True

    user32.EnumWindows(EnumProc(check), 0)
    return found


def x_out(hwnd):
    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)  # same as clicking the X


root = tk.Tk()
root.title("App Closer")
root.geometry("420x440")
tk.Label(root, text="Open apps", font=("Segoe UI", 14, "bold")).pack(pady=(12, 4))
box = tk.Listbox(root, font=("Segoe UI", 10), selectmode="extended", activestyle="none")
box.pack(fill="both", expand=True, padx=12, pady=4)
status = tk.Label(root, text="", fg="#555")
apps = []


def refresh():
    global apps
    apps = open_apps()
    box.delete(0, "end")
    for _, title in apps:
        box.insert("end", title)
    status.config(text=f"{len(apps)} open app(s)")


def close_selected():
    for i in box.curselection():
        x_out(apps[i][0])
    root.after(800, refresh)


def close_all():
    refresh()
    if not apps:
        return
    if messagebox.askyesno("Close all apps",
                           f"Close all {len(apps)} open apps?\nSave your work first. Apps with unsaved work will ask you to save."):
        for hwnd, _ in apps:
            x_out(hwnd)
        root.after(1200, refresh)


bar = tk.Frame(root)
bar.pack(fill="x", padx=12, pady=(0, 4))
tk.Button(bar, text="Refresh", command=refresh).pack(side="left")
tk.Button(bar, text="Close selected", command=close_selected).pack(side="left", padx=6)
tk.Button(root, text="X  Close ALL apps", bg="#d9423a", fg="white", font=("Segoe UI", 12, "bold"), bd=0,
          command=close_all).pack(fill="x", padx=12, pady=6, ipady=8)
status.pack(pady=(0, 8))
refresh()
root.mainloop()
