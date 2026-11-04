"""Locate Steam libraries and installed games."""
import os
import re
import winreg

SKIP = re.compile(r"steamworks|redistributable|proton|steam linux runtime|steamvr|soundtrack|dedicated server|sdk", re.I)
_KV = re.compile(r'"([^"]+)"\s+"([^"]*)"')


def steam_path():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
        return os.path.normpath(winreg.QueryValueEx(k, "SteamPath")[0])


def library_dirs():
    root = steam_path()
    libs = [os.path.join(root, "steamapps")]
    try:
        text = open(os.path.join(root, "steamapps", "libraryfolders.vdf"), encoding="utf-8").read()
        for m in re.finditer(r'"path"\s+"([^"]+)"', text):
            p = os.path.join(os.path.normpath(m.group(1).replace("\\\\", "\\")), "steamapps")
            if p not in libs and os.path.isdir(p):
                libs.append(p)
    except OSError:
        pass
    return libs


def installed_games():
    """List of dicts: appid, name, dir (absolute install dir)."""
    games = {}
    for lib in library_dirs():
        for f in os.listdir(lib):
            if not (f.startswith("appmanifest_") and f.endswith(".acf")):
                continue
            kv = dict(_KV.findall(open(os.path.join(lib, f), encoding="utf-8", errors="ignore").read()))
            name, appid, inst = kv.get("name"), kv.get("appid"), kv.get("installdir")
            if not (name and appid and inst) or SKIP.search(name):
                continue
            d = os.path.join(lib, "common", inst)
            if os.path.isdir(d):
                games[appid] = {"appid": appid, "name": name, "dir": d}
    return sorted(games.values(), key=lambda g: g["name"].lower())


if __name__ == "__main__":
    for g in installed_games():
        print(g["appid"], g["name"], g["dir"])
