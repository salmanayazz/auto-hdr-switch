"""Tray app: keeps 'Steam HDR' Start Menu shortcuts in sync and exposes HDR options."""
import os
import subprocess
import sys
import threading
import winreg

import pystray
from PIL import Image, ImageDraw

import config
import shortcuts
import steam

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "SteamHDREnabler"
cfg = config.load()
stop = threading.Event()


def run_cmd():
    return f'"{shortcuts.PYTHONW}" "{os.path.abspath(__file__)}"'


def autostart_on():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            return winreg.QueryValueEx(k, RUN_NAME)[0] == run_cmd()
    except FileNotFoundError:
        return False


def toggle_autostart(*_):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if autostart_on():
            winreg.DeleteValue(k, RUN_NAME)
        else:
            winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, run_cmd())


def icon_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, 62, 62), 12, fill=(30, 30, 30, 255), outline=(255, 190, 0, 255), width=4)
    d.text((14, 24), "HDR", fill=(255, 190, 0, 255))
    return img


def setter(key, game=None, field=None):
    def act(icon, item):
        if game:
            cfg["games"].setdefault(game, {})
            cfg["games"][game][field] = not _get(game, field)
        else:
            cfg[key] = not cfg[key]
        config.save(cfg)
    return act


def _get(game, field):
    return config.game(cfg, game)[field]


def sync(*_):
    shortcuts.sync(steam.installed_games(), cfg["hide_steam_shortcuts"])


def toggle_hide(icon, item):
    cfg["hide_steam_shortcuts"] = not cfg["hide_steam_shortcuts"]
    config.save(cfg)
    shortcuts.hide_originals(cfg["hide_steam_shortcuts"])


def game_menu(g):
    a = g["appid"]
    return pystray.MenuItem(g["name"], pystray.Menu(
        pystray.MenuItem("Enable HDR on launch", setter(None, a, "hdr"), checked=lambda i: _get(a, "hdr"))))


def menu():
    games = pystray.Menu(lambda: (game_menu(g) for g in steam.installed_games()))
    return pystray.Menu(
        pystray.MenuItem("Enable HDR on launch (default)", setter("hdr_on_launch"), checked=lambda i: cfg["hdr_on_launch"]),
        pystray.MenuItem("Disable HDR when game quits", setter("hdr_off_on_exit"), checked=lambda i: cfg["hdr_off_on_exit"]),
        pystray.MenuItem("Per-game settings", games),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Hide Steam's own shortcuts", toggle_hide, checked=lambda i: cfg["hide_steam_shortcuts"]),
        pystray.MenuItem("Sync Start Menu shortcuts now", sync),
        pystray.MenuItem("Run at startup", toggle_autostart, checked=lambda i: autostart_on()),
        pystray.MenuItem("Windows HDR settings", lambda *_: os.startfile("ms-settings:display-hdr")),
        pystray.MenuItem("Quit", lambda icon, item: (stop.set(), icon.stop())))


def sync_loop():
    while not stop.is_set():
        try:
            sync()
        except Exception:
            pass
        stop.wait(60)


if __name__ == "__main__":
    threading.Thread(target=sync_loop, daemon=True).start()
    pystray.Icon("hdr-enabler", icon_image(), "Steam HDR Enabler", menu()).run()
