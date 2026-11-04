"""Launched by Start Menu shortcuts: HDR on -> start game via Steam -> wait -> HDR off."""
import logging
import os
import sys
import time
import traceback
import winreg

import psutil

import config
import hdr
import steam

os.makedirs(config.DIR, exist_ok=True)
logging.basicConfig(filename=os.path.join(config.DIR, "launcher.log"), level=logging.INFO,
                    format="%(asctime)s %(message)s")
log = logging.info

def game_procs(gdir):
    gdir = gdir.lower() + os.sep
    out = []
    for p in psutil.process_iter(["exe"]):
        try:
            if (p.info["exe"] or "").lower().startswith(gdir):
                out.append(p)
        except psutil.Error:
            pass
    return out


def steam_running(appid):
    """Steam records the running game in the registry; works even for elevated/anti-cheat processes."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            if str(winreg.QueryValueEx(k, "RunningAppID")[0]) == appid:
                return True
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"Software\Valve\Steam\Apps\{appid}") as k:
            return winreg.QueryValueEx(k, "Running")[0] == 1
    except OSError:
        return False


def main(appid):
    cfg = config.load()
    g = next((x for x in steam.installed_games() if x["appid"] == appid), None)
    opts = config.game(cfg, appid)
    log("launch %s found=%s opts=%s supported=%s enabled=%s", appid, bool(g), opts, hdr.is_supported(), hdr.is_enabled())
    we_enabled = False
    if g and opts["hdr"] and hdr.is_supported() and not hdr.is_enabled():
        we_enabled = hdr.set_hdr(True)
        log("hdr on -> %s", we_enabled)
        time.sleep(1.5)
    os.startfile(f"steam://rungameid/{appid}")
    if not g:
        return
    deadline = time.time() + 180
    while time.time() < deadline and not (steam_running(appid) or game_procs(g["dir"])):
        time.sleep(2)
    log("game running: steam=%s procs=%s", steam_running(appid), bool(game_procs(g["dir"])))
    quiet = 0
    while quiet < 10:  # tolerate launcher -> game handoffs
        quiet = 0 if (steam_running(appid) or game_procs(g["dir"])) else quiet + 2
        time.sleep(2)
    if we_enabled and cfg["hdr_off_on_exit"]:
        hdr.set_hdr(False)
        log("hdr off")
    log("done")


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except Exception:
        log(traceback.format_exc())
        raise
