"""Settings stored in the user APPDATA folder (hdr-enabler/config.json)."""
import json
import os

DIR = os.path.join(os.environ["APPDATA"], "hdr-enabler")
PATH = os.path.join(DIR, "config.json")
DEFAULTS = {"hdr_on_launch": False, "hdr_off_on_exit": True, "hide_steam_shortcuts": True, "games": {}}


def load():
    try:
        cfg = json.load(open(PATH, encoding="utf-8"))
    except (OSError, ValueError):
        cfg = {}
    return {**DEFAULTS, **cfg}


def save(cfg):
    os.makedirs(DIR, exist_ok=True)
    json.dump(cfg, open(PATH, "w", encoding="utf-8"), indent=2)


def game(cfg, appid):
    """Effective per-game settings; None values fall back to the global ones."""
    g = cfg["games"].get(str(appid), {})
    return {"hdr": g.get("hdr", cfg["hdr_on_launch"])}
