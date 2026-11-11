"""Pin the 'Steam HDR' Start Menu shortcuts to Start by driving Explorer's right-click menu.

Windows 11 rejects programmatic pinning (E_ACCESSDENIED), so this opens the folder in
Explorer and clicks 'Pin to Start' for each shortcut that is not pinned yet. It takes over
keyboard focus for a few seconds, so it is only run on demand.
"""
import os
import time

from pywinauto import Desktop
from pywinauto.keyboard import send_keys

import shortcuts

TITLE = "Steam HDR.*"


def _window():
    return Desktop(backend="uia").window(title_re=TITLE, class_name="CabinetWClass")


def _open_folder():
    win = _window()
    if not win.exists():
        os.startfile(shortcuts.FOLDER)
    win.wait("visible", timeout=15)
    win.set_focus()
    return win


def _menu_buttons(win):
    """Context-menu buttons; the menu is part of the Explorer window's UIA tree."""
    return {b.window_text(): b for b in win.descendants(control_type="MenuItem")}


def pin_all():
    """Pin every shortcut not yet pinned. Returns (pinned, already_pinned)."""
    win = _open_folder()
    count = sum(f.endswith(".lnk") for f in os.listdir(shortcuts.FOLDER))
    items = win.descendants(control_type="ListItem")
    pinned = skipped = 0
    if not items:
        return pinned, skipped
    items[0].click_input()
    send_keys("{HOME}")
    for n in range(count):
        if n:
            send_keys("{DOWN}")
        time.sleep(0.15)
        send_keys("+{F10}")
        time.sleep(0.6)
        buttons = _menu_buttons(win)
        if "Pin to Start" in buttons:
            buttons["Pin to Start"].invoke()
            pinned += 1
            time.sleep(0.4)
        else:
            skipped += 1
            send_keys("{ESC}")
            time.sleep(0.2)
    return pinned, skipped


if __name__ == "__main__":
    print(pin_all())
