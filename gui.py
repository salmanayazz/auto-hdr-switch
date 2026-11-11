"""Settings window that stays open while options are toggled (tray menus close on every click)."""
import threading
import tkinter as tk
from tkinter import ttk

import config


class Settings:
    def __init__(self, root, cfg, games, actions):
        """actions: dict of callables - hide, sync, pin, autostart_on, toggle_autostart."""
        self.root, self.cfg, self.games, self.act = root, cfg, games, actions
        self.win = None

    def show(self):
        if self.win is None or not self.win.winfo_exists():
            self._build()
        self._fill_games()
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()

    # -- construction -----------------------------------------------------
    def _build(self):
        w = self.win = tk.Toplevel(self.root)
        w.title("Steam HDR Enabler")
        w.geometry("360x520")
        w.protocol("WM_DELETE_WINDOW", w.withdraw)
        pad = {"padx": 10, "pady": 2, "anchor": "w"}

        self.vars = {}
        for key, text in (("hdr_on_launch", "Enable HDR on launch (default)"),
                          ("hdr_off_on_exit", "Disable HDR when game quits"),
                          ("hide_steam_shortcuts", "Hide Steam's own shortcuts")):
            v = tk.BooleanVar(value=self.cfg[key])
            self.vars[key] = v
            ttk.Checkbutton(w, text=text, variable=v,
                            command=lambda k=key: self._toggle(k)).pack(**pad)
        self.auto = tk.BooleanVar(value=self.act["autostart_on"]())
        ttk.Checkbutton(w, text="Run at startup", variable=self.auto,
                        command=self.act["toggle_autostart"]).pack(**pad)

        ttk.Label(w, text="Enable HDR per game").pack(padx=10, pady=(10, 2), anchor="w")
        box = ttk.Frame(w)
        box.pack(fill="both", expand=True, padx=10)
        canvas = tk.Canvas(box, highlightthickness=0)
        bar = ttk.Scrollbar(box, orient="vertical", command=canvas.yview)
        self.list = ttk.Frame(canvas)
        self.list.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.list, anchor="nw")
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-e.delta // 120, "units"))

        row = ttk.Frame(w)
        row.pack(fill="x", padx=10, pady=8)
        for text, fn in (("Sync shortcuts", self.act["sync"]),
                         ("Pin to Start", self.act["pin"]),
                         ("Windows HDR settings", self.act["hdr_settings"])):
            ttk.Button(row, text=text, command=fn).pack(side="left", padx=2)

    def _fill_games(self):
        for child in self.list.winfo_children():
            child.destroy()
        for g in sorted(self.games(), key=lambda g: g["name"].lower()):
            a = g["appid"]
            v = tk.BooleanVar(value=config.game(self.cfg, a)["hdr"])
            ttk.Checkbutton(self.list, text=g["name"], variable=v,
                            command=lambda a=a, v=v: self._toggle_game(a, v)).pack(anchor="w")
        for key, v in self.vars.items():
            v.set(self.cfg[key])
        self.auto.set(self.act["autostart_on"]())

    # -- handlers ---------------------------------------------------------
    def _toggle(self, key):
        self.cfg[key] = self.vars[key].get()
        config.save(self.cfg)
        if key == "hide_steam_shortcuts":
            threading.Thread(target=self.act["hide"], args=(self.cfg[key],), daemon=True).start()

    def _toggle_game(self, appid, var):
        self.cfg["games"].setdefault(str(appid), {})["hdr"] = var.get()
        config.save(self.cfg)
