"""Manage the 'Steam HDR' Start Menu folder of launcher shortcuts."""
import os
import re
import shutil
import subprocess
import sys

import config
import steam

START = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs")
FOLDER = os.path.join(START, "Steam HDR")
STEAM_FOLDER = os.path.join(START, "Steam")
# Kept outside the Start Menu so search does not index the backups.
BACKUP = os.path.join(config.DIR, "steam-shortcuts-backup")
HERE = os.path.dirname(os.path.abspath(__file__))
PYTHONW = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")


def _safe(name):
    return re.sub(r'[<>:"/\\|?*™®]', "", name).strip()


def _icon(appid):
    """Icon path from Steam's own .url shortcut, if it exists."""
    for d in (STEAM_FOLDER, BACKUP):
        try:
            for f in os.listdir(d):
                if f.endswith(".url"):
                    t = open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()
                    if f"rungameid/{appid}\n" in t.replace("\r", "") + "\n":
                        m = re.search(r"IconFile=(.+)", t)
                        return m.group(1).strip() if m else None
        except OSError:
            pass
    return None


def _move_urls(src, dst):
    os.makedirs(dst, exist_ok=True)
    try:
        names = os.listdir(src)
    except OSError:
        return
    for f in names:
        if f.endswith(".url"):
            shutil.move(os.path.join(src, f), os.path.join(dst, f))


def hide_originals(hide):
    """Move Steam's own .url shortcuts out of the Start Menu (or back when hide is False)."""
    if hide:
        _move_urls(STEAM_FOLDER, BACKUP)
    else:
        _move_urls(BACKUP, STEAM_FOLDER)


def sync(games, hide=False):
    """Create missing shortcuts, remove ones for uninstalled games."""
    os.makedirs(FOLDER, exist_ok=True)
    want = {_safe(g["name"]) + ".lnk": g for g in games}
    for f in os.listdir(FOLDER):
        if f.endswith(".lnk") and f not in want:
            os.remove(os.path.join(FOLDER, f))
    lines = ["$s = New-Object -ComObject WScript.Shell"]
    for f, g in want.items():
        p = os.path.join(FOLDER, f)
        if os.path.exists(p):
            continue
        icon = _icon(g["appid"])
        lines += [f"$l = $s.CreateShortcut('{p.replace(chr(39), chr(39) * 2)}')",
                  f"$l.TargetPath = '{PYTHONW}'",
                  f"$l.Arguments = '\"{os.path.join(HERE, 'launcher.py')}\" {g['appid']}'",
                  f"$l.WorkingDirectory = '{HERE}'"]
        if icon:
            lines.append(f"$l.IconLocation = '{icon.replace(chr(39), chr(39) * 2)}'")
        lines.append("$l.Save()")
    if len(lines) > 1:
        subprocess.run(["powershell", "-NoProfile", "-Command", "\n".join(lines)],
                       creationflags=0x08000000, check=False)
    if hide:  # after icons were read from the originals
        hide_originals(True)


if __name__ == "__main__":
    sync(steam.installed_games())
