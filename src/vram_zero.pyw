#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRAM Zero — by MEXAGORA
-----------------------
Utility for monitoring and releasing NVIDIA GPU memory (VRAM)
used by local AI models and other applications.

License: MIT License
Copyright (c) 2026 MEXAGORA

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import subprocess
import sys
import os
import re
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

APP_NAME = "VRAM Zero"
VERSION = "2.0.1"
AUTHOR = "MEXAGORA"
AUTO_REFRESH_MS = 3000
KILL_TIMEOUT_S = 10

# Evite le clignotement d'une console a chaque appel de nvidia-smi / taskkill
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

# ---------------------------------------------------------------------------
# Appearance — coder base + light pop-art accents
# ---------------------------------------------------------------------------
BG        = "#0d1117"
FG        = "#e6edf3"
ACCENT    = "#58a6ff"
POP_PINK  = "#f778ba"
POP_CYAN  = "#39c5cf"
POP_YELLOW= "#d2a8ff"
GREEN     = "#3fb950"
ORANGE    = "#ffa657"
RED       = "#ff7b72"
BORDER    = "#30363d"
SELECT_BG = "#1f6feb"
DIM       = "#8b949e"
GREY      = "#8b949e"
MONO      = ("Consolas", 10) if sys.platform == "win32" else ("DejaVu Sans Mono", 10)
MONO_BOLD = ("Consolas", 10, "bold") if sys.platform == "win32" else ("DejaVu Sans Mono", 10, "bold")
TITLE_FONT= ("Consolas", 12, "bold") if sys.platform == "win32" else ("DejaVu Sans Mono", 12, "bold")

# Mots-cles IA : cherches dans le chemin complet du processus.
# Les mots de 4 lettres ou moins doivent former un "mot entier" (ex. rvc, bark).
AI_KEYWORDS = [
    "ollama", "lm studio", "lmstudio", "comfyui", "comfy", "text-generation",
    "oobabooga", "stable-diffusion", "automatic1111", "a1111", "invokeai",
    "koboldcpp", "kobold", "llama.cpp", "llama-server", "vllm", "exllama",
    "tabbyapi", "tabby", "fooocus", "sd.webui", "webui", "diffusers",
    "transformers", "torch", "llama", "mistral", "phi", "gemma", "qwen",
    "whisper", "bark", "rvc", "sillytavern", "faraday", "gpt4all",
    "privategpt", "localai", "jan.exe", "lm-studio", "textgen", "tgw",
    "llamafile", "open-webui", "openwebui"
]

# Applications non essentielles / critiques : comparees au NOM de l'executable
# (sans chemin ni .exe). Mot long : debut du nom ; mot court (<= 4) : mot entier
# eventuellement suivi de chiffres (ex. obs64).
ORANGE_KEYWORDS = [
    "chrome", "msedge", "edge", "firefox", "opera", "brave", "vivaldi",
    "discord", "steam", "epicgames", "epic", "origin", "uplay", "ubisoft",
    "obs", "streamlabs", "nvidia share", "geforce", "spotify", "slack",
    "teams", "zoom", "telegram", "whatsapp", "signal", "blender",
    "davinci", "premiere", "afterfx", "photoshop", "illustrator",
    "unity", "unreal", "godot", "vscode", "cursor", "code",
    "claude", "wallpaper", "msedgewebview", "webview2",
    "docker", "vmmem", "wslhost", "webwallpaper", "nvidia overlay",
    "vlc", "photos"
]

# Jamais inclus dans "Terminer les IA" ni "Terminer tout" (liste fixe, dans le code).
# Ils restent affiches et peuvent etre selectionnes a la main, avec avertissement.
NEVER_PROPOSE = ["claude", "docker", "vmmem", "wslhost"]

RED_KEYWORDS = [
    "dwm", "csrss", "winlogon", "explorer", "searchapp", "searchui",
    "shellexperience", "startmenuexperience", "runtimebroker",
    "nvidia container", "nvcontainer", "audiodg", "system",
    "smss", "services", "lsass", "svchost", "wininit", "fontdrvhost",
    "sihost", "taskhostw", "ctfmon", "securityhealth", "avast", "avg",
    "avgui", "avgsvc", "defender", "msmpeng", "smartscreen", "conhost",
    "searchhost", "textinputhost", "lockapp", "applicationframehost",
    "shellhost", "widgetboard", "crossdeviceresume", "phoneexperiencehost"
]

_SHORT = 4


def _kw_regex(k):
    return re.compile(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])")


_AI_LONG = [k for k in AI_KEYWORDS if len(k) > _SHORT]
_AI_SHORT = [_kw_regex(k) for k in AI_KEYWORDS if len(k) <= _SHORT]


def _exe_stem(name: str) -> str:
    base = name.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return base[:-4] if base.endswith(".exe") else base


def _stem_match(stem: str, keys) -> bool:
    tokens = [t for t in re.split(r"[^a-z0-9]+", stem) if t]
    for k in keys:
        if len(k) > _SHORT:
            if stem.startswith(k) or any(t.startswith(k) for t in tokens):
                return True
        elif any(re.fullmatch(re.escape(k) + r"\d*", t) for t in tokens):
            return True
    return False


def classify(name: str) -> str:
    """Niveaux : red (critique), green (IA reconnue), orange (non essentiel),
    unknown (nom lisible mais non reconnu), noid (nom illisible : droits insuffisants)."""
    if not name.strip() or name.strip().startswith("["):
        return "noid"
    stem = _exe_stem(name)
    if _stem_match(stem, RED_KEYWORDS):  # les noms systeme critiques passent en premier
        return "red"
    path = name.lower().replace("/", "\\")
    if any(k in path for k in _AI_LONG) or any(r.search(path) for r in _AI_SHORT):
        return "green"
    if _stem_match(stem, ORANGE_KEYWORDS):
        return "orange"
    return "unknown"


def is_protected(name: str) -> bool:
    return _stem_match(_exe_stem(name), NEVER_PROPOSE)


def short_name(name: str) -> str:
    return name.replace("\\", "/").rsplit("/", 1)[-1] or name


def run_cmd(args):
    """Execute une commande sans fenetre ; renvoie stdout ou None en cas d'echec."""
    try:
        r = subprocess.run(
            args, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=8,
            creationflags=CREATE_NO_WINDOW
        )
        if r.returncode != 0:
            return None
        return r.stdout or ""
    except Exception:
        return None


def get_gpu_stats():
    """Totaux VRAM sur toutes les cartes NVIDIA ; None si nvidia-smi est indisponible."""
    out = run_cmd([
        "nvidia-smi",
        "--query-gpu=memory.total,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits"
    ])
    if not out:
        return None
    rows = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        try:
            rows.append([int(float(x)) for x in parts[:4]])
        except ValueError:
            continue
    if not rows or any(len(r) < 4 for r in rows):
        return None
    return {
        "total": sum(r[0] for r in rows),
        "used":  sum(r[1] for r in rows),
        "free":  sum(r[2] for r in rows),
        "util":  round(sum(r[3] for r in rows) / len(rows)),
        "gpus":  len(rows),
    }


def get_gpu_processes():
    out = run_cmd([
        "nvidia-smi",
        "--query-compute-apps=pid,process_name,used_memory",
        "--format=csv,noheader,nounits"
    ])
    if out is None:
        return None  # echec de la collecte (different de "aucun processus")
    if not out.strip() or "No running processes" in out:
        return []
    merged = {}
    for line in out.strip().splitlines():
        # le nom du processus peut contenir des virgules : pid au debut, memoire a la fin
        try:
            head, mem_raw = line.rsplit(",", 1)
            pid_raw, name = head.split(",", 1)
            pid = int(pid_raw.strip())
        except ValueError:
            continue
        name = name.strip()
        mem_raw = mem_raw.strip()
        try:
            mem_val = None if (not mem_raw or "N/A" in mem_raw.upper() or "[" in mem_raw) \
                else int(float(mem_raw))
        except ValueError:
            mem_val = None
        if pid in merged:  # meme PID sur plusieurs cartes : on additionne
            old = merged[pid]["memory_val"]
            if mem_val is not None:
                merged[pid]["memory_val"] = (old or 0) + mem_val
        else:
            merged[pid] = {"pid": pid, "name": name, "memory_val": mem_val,
                           "level": classify(name), "protected": is_protected(name)}
    procs = list(merged.values())
    for p in procs:
        p["memory"] = "N/A" if p["memory_val"] is None else str(p["memory_val"])
    # Known memory first (desc), then N/A
    procs.sort(key=lambda p: (p["memory_val"] is None, -(p["memory_val"] or 0)))
    return procs


def kill_pid(pid: int):
    """Ferme un processus. Renvoie (ok, raison) ; raison : '', 'denied', 'gone', 'timeout', 'failed'."""
    try:
        if sys.platform == "win32":
            r = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True, text=True, errors="replace",
                creationflags=CREATE_NO_WINDOW, timeout=KILL_TIMEOUT_S
            )
            if r.returncode == 0:
                return True, ""
            msg = ((r.stdout or "") + (r.stderr or "")).lower()
            if "denied" in msg or "refus" in msg:
                return False, "denied"
            if "not found" in msg or "introuvable" in msg or "no running instance" in msg:
                return False, "gone"
            return False, "failed"
        os.kill(pid, 9)
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except PermissionError:
        return False, "denied"
    except Exception:
        return False, "failed"


def safe_kill(targets, lister=None, killer=None):
    """Ferme les cibles apres reverification de l'identite (PID + nom).
    Renvoie une liste de (processus, statut) ; statuts : closed, gone, changed,
    unverified, denied, timeout, failed."""
    lister = lister or get_gpu_processes
    killer = killer or kill_pid
    current = lister()
    if current is None:  # impossible de verifier : on ne ferme rien
        return [(p, "unverified") for p in targets]
    names = {c["pid"]: c["name"] for c in current}
    results = []
    for p in targets:
        if p["pid"] not in names:
            results.append((p, "gone"))
        elif names[p["pid"]] != p["name"]:
            results.append((p, "changed"))  # le PID a ete reattribue a un autre programme
        else:
            ok, why = killer(p["pid"])
            results.append((p, "closed" if ok else why))
    return results


def mem_label(p, total=None):
    if p["memory"] == "N/A" or p["memory_val"] is None:
        return "N/A", "—"
    mib = f"{p['memory_val']} MiB"
    if total and total > 0:
        pct = round(p["memory_val"] / total * 100, 1)
        return mib, f"{pct} %"
    return mib, "—"


def find_resource(name):
    """Cherche un fichier d'assets : EXE (PyInstaller), dossier assets/ ou dossier du script."""
    dirs = []
    if getattr(sys, "frozen", False):
        dirs.append(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
        dirs.append(os.path.dirname(sys.executable))
    here = os.path.dirname(os.path.abspath(__file__))
    dirs += [os.path.join(here, "..", "assets"), here]
    for d in dirs:
        p = os.path.abspath(os.path.join(d, name))
        if os.path.isfile(p):
            return p
    return None


class VRAMZeroApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  v{VERSION}  —  by {AUTHOR}")
        self.configure(bg=BG)
        self.geometry("780x580")
        self.minsize(680, 480)
        self.resizable(True, True)
        self._try_set_icon()

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 390
        y = (self.winfo_screenheight() // 2) - 290
        self.geometry(f"+{x}+{y}")

        self.processes = []
        self.gpu_total = None
        self.show_critical = False
        self._auto_job = None
        self._poll_job = None
        self._busy = False
        self._again = False
        self._rows = None
        self._results = queue.Queue()
        self._kill_results = queue.Queue()
        self._killing = False
        self.last_stats = None
        self.last_when = None
        self.state = "init"
        self._build_ui()
        self._poll_results()
        self._auto_tick()

    def _try_set_icon(self):
        """Charge l'icone fenetre / barre des taches si presente."""
        path = find_resource("vram_zero.ico")
        if not path:
            return
        try:
            self.iconbitmap(default=path)
            self.iconbitmap(path)
        except Exception:
            pass

    def _build_ui(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=12, pady=(10, 2))

        title_frame = tk.Frame(header, bg=BG)
        title_frame.pack(side="left")
        tk.Label(title_frame, text=f"{APP_NAME}  v{VERSION}", font=TITLE_FONT,
                 bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(title_frame, text=f"  ·  {AUTHOR}", font=MONO,
                 bg=BG, fg=DIM).pack(side="left")

        right = tk.Frame(header, bg=BG)
        right.pack(side="right")

        self.filter_btn = tk.Button(
            right, text="⊞", command=self.toggle_filter,
            font=("Segoe UI Symbol", 11) if sys.platform == "win32" else MONO_BOLD,
            bg=BORDER, fg=POP_CYAN,
            activebackground=SELECT_BG, activeforeground="#fff",
            relief="flat", bd=0, padx=8, pady=3, cursor="hand2"
        )
        self.filter_btn.pack(side="left", padx=(0, 6))
        self._tooltip(self.filter_btn, "Afficher ou masquer les processus critiques")

        for txt, cmd in (("[ À propos ]", self.show_about), ("[ Aide ]", self.show_help)):
            tk.Button(
                right, text=txt, command=cmd,
                font=MONO, bg=BORDER, fg=ACCENT,
                activebackground=SELECT_BG, activeforeground="#fff",
                relief="flat", bd=0, padx=9, pady=3, cursor="hand2"
            ).pack(side="left", padx=(6, 0))

        self.status_var = tk.StringVar(value="Prêt")
        tk.Label(header, textvariable=self.status_var, font=MONO,
                 bg=BG, fg=POP_YELLOW).pack(side="right", padx=(0, 10))

        # Stats
        stats_frame = tk.Frame(self, bg=BG)
        stats_frame.pack(fill="x", padx=14, pady=(8, 2))
        self.vram_var = tk.StringVar(value="VRAM  — / — MiB   (— %)")
        self.util_var = tk.StringVar(value="GPU   — %")
        tk.Label(stats_frame, textvariable=self.vram_var, font=MONO_BOLD,
                 bg=BG, fg=FG, anchor="w").pack(side="left")
        tk.Label(stats_frame, textvariable=self.util_var, font=MONO_BOLD,
                 bg=BG, fg=POP_CYAN, anchor="e").pack(side="right")

        # Modern gradient + mosaic bar
        bar_frame = tk.Frame(self, bg=BG)
        bar_frame.pack(fill="x", padx=14, pady=(4, 8))
        self.bar_canvas = tk.Canvas(
            bar_frame, height=10, bg=BORDER,
            highlightthickness=0, bd=0
        )
        self.bar_canvas.pack(fill="x")
        self.bar_canvas.bind("<Configure>", lambda e: self._redraw_bar())

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=12, pady=2)

        legend = tk.Frame(self, bg=BG)
        legend.pack(fill="x", padx=14, pady=(2, 4))

        def leg(color, text):
            f = tk.Frame(legend, bg=BG)
            f.pack(side="left", padx=(0, 14))
            tk.Label(f, text="●", font=MONO_BOLD, bg=BG, fg=color).pack(side="left")
            tk.Label(f, text=text, font=MONO, bg=BG, fg=DIM).pack(side="left", padx=(3, 0))

        leg(GREEN, "IA locale")
        leg(ORANGE, "Non essentiel")
        leg(RED, "Critique")
        leg(GREY, "Inconnu / non identifiable")
        self.filter_label = tk.Label(
            legend, text="Filtre : critiques masqués",
            font=MONO, bg=BG, fg=DIM
        )
        self.filter_label.pack(side="right")

        # Table
        list_frame = tk.Frame(self, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=12, pady=4)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
            background=BG, foreground=FG, fieldbackground=BG,
            borderwidth=0, font=MONO, rowheight=26)
        style.configure("Dark.Treeview.Heading",
            background="#161b22", foreground=POP_CYAN,
            font=MONO_BOLD, borderwidth=0, relief="flat")
        style.map("Dark.Treeview",
            background=[("selected", SELECT_BG)],
            foreground=[("selected", "#ffffff")])
        style.layout("Dark.Treeview", [("Dark.Treeview.treearea", {"sticky": "nswe"})])

        cols = ("dot", "pid", "memory", "share", "name")
        self.tree = ttk.Treeview(
            list_frame, columns=cols, show="headings",
            style="Dark.Treeview", selectmode="extended"
        )
        self.tree.heading("dot", text="", anchor="center")
        self.tree.heading("pid", text="PID", anchor="w")
        self.tree.heading("memory", text="VRAM", anchor="e")
        self.tree.heading("share", text="Part", anchor="e")
        self.tree.heading("name", text="Processus", anchor="w")
        self.tree.column("dot", width=28, minwidth=28, stretch=False, anchor="center")
        self.tree.column("pid", width=72, minwidth=56, stretch=False, anchor="w")
        self.tree.column("memory", width=100, minwidth=80, stretch=False, anchor="e")
        self.tree.column("share", width=64, minwidth=50, stretch=False, anchor="e")
        self.tree.column("name", width=460, minwidth=200, stretch=True, anchor="w")

        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.tag_configure("green", foreground=GREEN)
        self.tree.tag_configure("orange", foreground=ORANGE)
        self.tree.tag_configure("red", foreground=RED)
        self.tree.tag_configure("unknown", foreground=GREY)
        self.tree.tag_configure("noid", foreground=GREY)

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(fill="x", padx=12, pady=(8, 6))

        def btn(text, cmd, color=ACCENT):
            b = tk.Button(
                btn_frame, text=text, command=cmd,
                font=MONO_BOLD, bg=BORDER, fg=color,
                activebackground=SELECT_BG, activeforeground="#fff",
                relief="flat", bd=0, padx=11, pady=6, cursor="hand2"
            )
            b.pack(side="left", padx=(0, 7))
            return b

        btn("[ Actualiser ]", self.refresh)
        btn("[ Terminer la sélection ]", self.kill_selected, RED)
        btn("[ Terminer les IA ]", self.kill_ai, GREEN)
        btn("[ Terminer tout ]", self.kill_all, ORANGE)

        copy_btn = tk.Button(
            btn_frame, text="⧉", command=self.copy_all,
            font=("Segoe UI Symbol", 12) if sys.platform == "win32" else MONO,
            bg=BORDER, fg=POP_CYAN,
            activebackground=SELECT_BG, activeforeground="#fff",
            relief="flat", bd=0, padx=10, pady=4, cursor="hand2"
        )
        copy_btn.pack(side="right")
        self._tooltip(copy_btn, "Copier le rapport dans le presse-papiers")

        self.info_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.info_var, font=MONO,
                 bg=BG, fg=DIM, anchor="w").pack(fill="x", padx=14, pady=(0, 8))

        self._bar_pct = 0

    def _tooltip(self, widget, text):
        def enter(e): self.info_var.set(text)
        def leave(e): self._update_info()
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def set_status(self, msg):
        self.status_var.set(msg)

    def _update_info(self):
        if self.state in ("down", "partial"):
            return  # le message d'etat reste affiche
        visible = self._visible_processes()
        if not visible:
            self.info_var.set("Aucun processus à afficher avec le filtre actuel.")
            return
        cnt = {k: sum(1 for p in visible if p["level"] == k)
               for k in ("green", "orange", "red", "unknown", "noid")}
        hidden = len(self.processes) - len(visible)
        extra = f"  ·  {hidden} critiques masqués" if hidden else ""
        unk = cnt["unknown"] + cnt["noid"]
        self.info_var.set(
            f"● {cnt['green']} IA   ● {cnt['orange']} non essentiel   "
            f"● {cnt['red']} critique   ● {unk} inconnu{extra}")

    def _visible_processes(self):
        if self.show_critical:
            return self.processes
        return [p for p in self.processes if p["level"] != "red"]

    def toggle_filter(self):
        if self.show_critical:
            self.show_critical = False
            self.filter_label.config(text="Filtre : critiques masqués")
            self.set_status("Processus critiques masqués")
            self._rebuild_tree(force=True)
            self._update_info()
            return
        ok = messagebox.askyesno(
            "Affichage des processus critiques",
            "Vous êtes sur le point d'afficher les processus système et critiques.\n\n"
            "Ces processus ne doivent en principe pas être terminés.\n"
            "Ils sont masqués par défaut afin de limiter les risques.\n\n"
            "Confirmez-vous l'affichage des processus critiques ?",
            icon="warning"
        )
        if not ok:
            return
        self.show_critical = True
        self.filter_label.config(text="Filtre : tous les processus")
        self.set_status("Processus critiques visibles")
        self._rebuild_tree(force=True)
        self._update_info()

    def _redraw_bar(self):
        """Barre VRAM sobre, style codeur moderne."""
        c = self.bar_canvas
        c.delete("all")
        w = max(c.winfo_width(), 10)
        h = max(c.winfo_height(), 10)
        pct = getattr(self, "_bar_pct", 0)
        fill_w = max(0, int(w * pct / 100.0))

        # Track
        c.create_rectangle(0, 0, w, h, fill="#21262d", outline="")

        if fill_w <= 0:
            return

        # Couleur unique selon seuil (pas de rainbow)
        if pct < 50:
            color = "#238636"
        elif pct < 80:
            color = "#9e6a03"
        else:
            color = "#da3633"

        # Remplissage plein
        c.create_rectangle(0, 0, fill_w, h, fill=color, outline="")

        # Léger dégradé horizontal (plus sombre → couleur)
        steps = max(8, fill_w // 8)
        for i in range(steps):
            t = i / max(steps - 1, 1)
            x0 = int(fill_w * t)
            x1 = int(fill_w * (t + 1 / steps)) + 1
            # Assombrir légèrement le début
            factor = 0.55 + 0.45 * t
            r = int(int(color[1:3], 16) * factor)
            g = int(int(color[3:5], 16) * factor)
            b = int(int(color[5:7], 16) * factor)
            col = f"#{r:02x}{g:02x}{b:02x}"
            c.create_rectangle(x0, 0, min(x1, fill_w), h, fill=col, outline="")

        # Ligne de bord droite nette
        if fill_w > 1:
            c.create_line(fill_w - 1, 0, fill_w - 1, h, fill="#e6edf3", width=1)

    def _update_stats_bar(self, stats):
        if not stats:
            self.vram_var.set("VRAM  — / — MiB   (— %)")
            self.util_var.set("GPU   — %")
            self._bar_pct = 0
            self.gpu_total = None
            self._redraw_bar()
            return
        total = stats["total"]
        used = stats["used"]
        pct = round(used / total * 100) if total else 0
        self.gpu_total = total
        gpus = f"   [{stats['gpus']} GPU]" if stats.get("gpus", 1) > 1 else ""
        self.vram_var.set(f"VRAM  {used} / {total} MiB   ({pct} %){gpus}")
        self.util_var.set(f"GPU   {stats['util']} %")
        self._bar_pct = pct
        self._redraw_bar()

    def _rebuild_tree(self, force=False):
        """Reconstruit le tableau seulement si les donnees changent, en gardant la selection."""
        visible = self._visible_processes()
        rows = [(p["pid"], *mem_label(p, self.gpu_total), p["name"], p["level"])
                for p in visible]
        if not force and rows == self._rows:
            return
        self._rows = rows
        selected = set()
        for item in self.tree.selection():
            vals = self.tree.item(item, "values")
            if vals:
                selected.add(int(vals[1]))
        top = self.tree.yview()[0]
        self.tree.delete(*self.tree.get_children())
        keep = []
        for pid, mib, share, name, level in rows:
            iid = self.tree.insert("", "end",
                values=("●", pid, mib, share, name), tags=(level,))
            if pid in selected:
                keep.append(iid)
        if keep:
            self.tree.selection_set(keep)
        self.tree.yview_moveto(top)

    # -- Actualisation en arriere-plan (l'interface ne se bloque plus) --------

    def refresh(self):
        if self._busy:
            self._again = True  # une actualisation sera relancee des que possible
            return
        self._busy = True
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        stats = procs = None
        try:
            stats = get_gpu_stats()
            if stats:
                procs = get_gpu_processes()  # None = echec, [] = aucun processus signale
        except Exception:
            pass
        finally:
            self._results.put((stats, procs, datetime.now()))

    def _poll_results(self):
        try:
            stats, procs, when = self._results.get_nowait()
        except queue.Empty:
            pass
        else:
            self._busy = False
            self._apply(stats, procs, when)
            if self._again:
                self._again = False
                self.refresh()
        try:
            res = self._kill_results.get_nowait()
        except queue.Empty:
            pass
        else:
            self._killing = False
            self._show_kill_result(res)
        self._poll_job = self.after(100, self._poll_results)

    def _apply(self, stats, procs, when=None):
        self.last_stats = stats
        self.last_when = when
        self._update_stats_bar(stats)
        if stats is None:
            self.state = "down"
            self.processes = []
            self._rebuild_tree()
            self.set_status("Données indisponibles")
            self.info_var.set("nvidia-smi est introuvable ou en erreur : rien n'est connu de la VRAM. "
                              "Ne pas en conclure qu'elle est libre.")
            return
        if procs is None:
            self.state = "partial"
            self.processes = []
            self._rebuild_tree()
            self.set_status("Liste des processus indisponible")
            self.info_var.set("Le total VRAM est lu, mais la liste des processus n'a pas pu l'être. "
                              "Ne pas en conclure qu'aucun processus n'utilise le GPU.")
            return

        self.state = "ok"
        self.processes = procs
        self._rebuild_tree()

        if not self.processes:
            self.set_status("Aucun processus signalé")
            self.info_var.set("nvidia-smi ne signale aucun processus GPU "
                              "(certaines applications peuvent ne pas y figurer).")
            return

        self.set_status(f"{len(self._visible_processes())} processus affichés")
        self._update_info()
        noid = [p for p in self._visible_processes() if p["level"] == "noid"]
        if noid:
            self.info_var.set(self.info_var.get() +
                              "  ·  « [Insufficient Permissions] » : nom illisible (droits insuffisants)")

    def _auto_tick(self):
        self.refresh()
        self._auto_job = self.after(AUTO_REFRESH_MS, self._auto_tick)

    def _stop_auto_refresh(self):
        for attr in ("_auto_job", "_poll_job"):
            job = getattr(self, attr)
            if job:
                self.after_cancel(job)
                setattr(self, attr, None)

    def _selected(self):
        out = []
        for item in self.tree.selection():
            vals = self.tree.item(item, "values")
            if vals:
                pid = int(vals[1])
                for p in self.processes:
                    if p["pid"] == pid:
                        out.append(p)
                        break
        return out

    def _kill(self, targets, label):
        if self._killing:
            return
        if not targets:
            messagebox.showinfo(APP_NAME, "Aucun processus à terminer.")
            return

        def risky(p):
            return p["level"] in ("red", "unknown", "noid") or p.get("protected")

        flagged = [p for p in targets if risky(p)]
        others = [p for p in targets if not risky(p)]

        if flagged:
            names = "\n".join(f"  • {short_name(p['name'])}  (PID {p['pid']})" for p in flagged[:8])
            if len(flagged) > 8:
                names += f"\n  … et {len(flagged) - 8} autre(s)"
            if not messagebox.askyesno(
                "Avertissement — processus sensibles",
                f"{len(flagged)} processus critique(s), non identifié(s) ou protégé(s) "
                f"ont été sélectionné(s) :\n\n{names}\n\n"
                "La terminaison de ces processus peut entraîner une instabilité "
                "du système ou l'arrêt inattendu d'autres applications.\n\n"
                "Souhaitez-vous poursuivre ?",
                icon="warning"
            ):
                targets = others
                if not targets:
                    self.set_status("Opération annulée")
                    return

        if not targets:
            return

        summary = "\n".join(
            f"  • {short_name(p['name'])}  (PID {p['pid']}, {mem_label(p, self.gpu_total)[0]})"
            for p in targets[:8]
        )
        if len(targets) > 8:
            summary += f"\n  … et {len(targets) - 8} autre(s)"

        if not messagebox.askyesno(
            "Confirmation de terminaison",
            f"{len(targets)} processus vont être terminés :\n\n{summary}\n\n"
            "Avant la fermeture, l'identité de chaque processus (PID et nom) est revérifiée.\n"
            "Veuillez enregistrer vos données éventuelles avant de confirmer.\n\n"
            "Confirmez-vous la terminaison ?"
        ):
            self.set_status("Opération annulée")
            return

        self._killing = True
        self.set_status("Fermeture en cours…")
        threading.Thread(target=self._kill_worker, args=(list(targets),), daemon=True).start()

    def _kill_worker(self, targets):
        res = None
        try:
            res = safe_kill(targets)
        except Exception:
            res = [(p, "failed") for p in targets]
        finally:
            self._kill_results.put(res if res is not None else [(p, "failed") for p in targets])

    def _show_kill_result(self, res):
        count = {}
        for _, st in res:
            count[st] = count.get(st, 0) + 1
        closed = count.get("closed", 0)
        self.set_status(f"{closed} / {len(res)} processus fermé(s)")
        notes = []
        if count.get("gone"):
            notes.append(f"{count['gone']} déjà terminé(s)")
        if count.get("changed"):
            notes.append(f"{count['changed']} ignoré(s) : le PID appartient maintenant à un autre programme")
        if count.get("unverified"):
            notes.append("aucun processus fermé : la liste n'a pas pu être revérifiée (nvidia-smi indisponible)")
        if count.get("denied"):
            notes.append(f"{count['denied']} refusé(s) par Windows (droits insuffisants : "
                         "relancer VRAM Zero en administrateur si c'est voulu)")
        if count.get("timeout"):
            notes.append(f"{count['timeout']} sans réponse dans le délai de {KILL_TIMEOUT_S} s")
        if count.get("failed"):
            notes.append(f"{count['failed']} en échec")
        if notes:
            messagebox.showwarning(APP_NAME, "Résultat de la fermeture :\n\n  • " + "\n  • ".join(notes))
        self.after(600, self.refresh)

    def kill_selected(self):
        self._kill(self._selected(), "sélection")

    def kill_ai(self):
        self._kill([p for p in self.processes
                    if p["level"] == "green" and not p.get("protected")], "IA locales")

    def kill_all(self):
        self._kill([p for p in self._visible_processes()
                    if p["level"] in ("green", "orange") and not p.get("protected")],
                   "processus visibles")

    def copy_all(self):
        stats = self.last_stats  # derniere collecte : pas d'appel a nvidia-smi dans l'interface
        when = self.last_when or datetime.now()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        etat = {"ok": "valide", "partial": "partielle (liste des processus indisponible)",
                "down": "indisponible", "init": "pas encore effectuée"}.get(self.state, self.state)
        lines = [
            "=" * 60,
            f"{APP_NAME.upper()} — by {AUTHOR}",
            "Rapport d'occupation GPU",
            "=" * 60,
            f"Date du rapport     : {now}",
        f"Collecte            : {etat} — {when.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Version             : {APP_NAME} v{VERSION}",
            "Source des données  : nvidia-smi (outil officiel NVIDIA)",
            "Commandes utilisées :",
            "  - nvidia-smi --query-gpu=memory.total,memory.used,memory.free,utilization.gpu",
            "  - nvidia-smi --query-compute-apps=pid,process_name,used_memory",
            "",
            "Légende des niveaux :",
            "  VERT   (green)  = outil IA reconnu — fermer peut interrompre son activité",
            "  ORANGE (orange) = Application non essentielle — à surveiller",
            "  ROUGE  (red)    = Processus critique ou système — ne pas terminer sans précaution",
        "  GRIS   (inconnu)= Nom non reconnu ou illisible — jamais inclus dans Terminer tout",
            "",
        ]
        filt = "tous les processus" if self.show_critical else "tous sauf les critiques (masqués)"
        lines.append(f"Filtre actif        : {filt}")
        lines.append("")
        if stats:
            pct = round(stats["used"] / stats["total"] * 100) if stats["total"] else 0
            lines.append(f"Occupation VRAM     : {stats['used']} / {stats['total']} MiB  ({pct} %)")
            lines.append(f"Utilisation GPU     : {stats['util']} %")
            lines.append(f"VRAM disponible     : {stats['free']} MiB")
        else:
            lines.append("Occupation VRAM     : données indisponibles")
        lines.append("")
        lines.append("-" * 60)
        visible = self._visible_processes()
        if not visible:
            lines.append("Aucun processus à afficher avec le filtre actuel.")
        else:
            lines.append(f"{'PID':<8} {'VRAM':<12} {'PART':<8} PROCESSUS")
            lines.append("-" * 60)
            for p in visible:
                mib, share = mem_label(p, self.gpu_total)
                lines.append(f"{p['pid']:<8} {mib:<12} {share:<8} {p['name']}")
        lines.append("-" * 60)
        lines.append(f"Processus affichés  : {len(visible)}   |   Total détectés : {len(self.processes)}")
        lines.append("=" * 60)

        self.clipboard_clear()
        self.clipboard_append("\n".join(lines))
        self.set_status("Rapport copié")
        self.info_var.set("Le rapport a été copié dans le presse-papiers.")

    def show_help(self):
        content = (
            "PRESENTATION\n"
            f"{APP_NAME} permet de surveiller l'occupation de la mémoire vidéo\n"
            "(VRAM) d'une carte graphique NVIDIA et de terminer les processus\n"
            "qui l'utilisent, en particulier les modèles d'intelligence\n"
            "artificielle exécutés localement.\n\n"
            "FILTRE D'AFFICHAGE\n"
            "Par défaut, tout est affiché sauf les processus critiques (rouge),\n"
            "masqués pour réduire le risque d'accident. Les programmes non\n"
            "reconnus (gris) restent visibles : ils ne sont jamais inclus dans\n"
            "« Terminer les IA » ni « Terminer tout ».\n"
            "Le bouton ⊞ permet d'afficher ou de masquer les processus critiques\n"
            "après confirmation.\n\n"
            "COLONNES DU TABLEAU\n"
            "  PID      Identifiant du processus\n"
            "  VRAM     Mémoire vidéo utilisée (MiB) lorsque disponible\n"
            "  Part     Pourcentage de la VRAM totale\n"
            "  Processus  Nom du programme\n\n"
            "Les valeurs N/A indiquent que le pilote Windows n'expose pas\n"
            "la consommation individuelle (limitation WDDM fréquente).\n"
            "Les statistiques globales en haut restent fiables.\n\n"
            "ACTIONS\n"
            "  [ Actualiser ]              Actualise les données\n"
            "  [ Terminer la sélection ]   Termine les processus sélectionnés\n"
            "  [ Terminer les IA ]         Termine uniquement les IA locales\n"
            "  [ Terminer tout ]           Termine les IA et applications non essentielles\n"
            "                              (jamais Claude, Docker ni les inconnus)\n"
            "  ⧉                           Copie un rapport détaillé\n\n"
            "Actualisation automatique toutes les 3 secondes."
        )
        self._text_window("Aide", content)

    def show_about(self):
        content = (
            f"{APP_NAME}  version {VERSION}\n"
            f"by {AUTHOR}\n\n"
            "DESCRIPTION\n"
            f"{APP_NAME} est un utilitaire léger destiné à faciliter la gestion\n"
            "de la mémoire vidéo (VRAM) sur les systèmes équipés d'une carte\n"
            "graphique NVIDIA. Il s'adresse principalement aux utilisateurs\n"
            "exécutant des modèles d'intelligence artificielle en local.\n\n"
            "CARACTÉRISTIQUES\n"
            "  • Surveillance en temps réel de l'occupation VRAM et GPU\n"
            "  • Identification et classification des processus\n"
            "  • Terminaison contrôlée des processus sélectionnés\n"
            "  • Filtre de sécurité masquant les processus critiques\n"
            "  • Export de rapports détaillés\n"
            "  • L'application ne se connecte à aucun réseau et n'enregistre rien\n\n"
            "TECHNOLOGIE\n"
            "L'application s'appuie exclusivement sur nvidia-smi (outil officiel\n"
            "NVIDIA) et sur les modules standard de Python.\n\n"
            "LICENCE\n"
            "MIT License — utilisation, modification et redistribution libres.\n"
            "Le logiciel est fourni « en l'état », sans garantie d'aucune sorte.\n\n"
            "RESPONSABILITÉ\n"
            "L'utilisateur demeure responsable des processus qu'il choisit de\n"
            "terminer. La terminaison de processus système peut entraîner une\n"
            "instabilité du système d'exploitation."
        )
        self._text_window("À propos", content, image="vram_zero_popart.png")

    def _text_window(self, title, content, image=None):
        photo = None
        if image:
            path = find_resource(image)
            if path:
                try:
                    photo = tk.PhotoImage(file=path).subsample(2)  # 256 px -> 128 px
                except Exception:
                    photo = None

        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=BG)
        win.geometry("540x" + ("700" if photo else "540"))
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        win.update_idletasks()
        win.geometry(f"+{self.winfo_x() + 80}+{self.winfo_y() + 10}")

        tk.Label(win, text=title, font=TITLE_FONT,
                 bg=BG, fg=ACCENT).pack(anchor="w", padx=16, pady=(14, 8))
        if photo:
            lbl = tk.Label(win, image=photo, bg=BG, bd=0)
            lbl.image = photo  # garder la reference
            lbl.pack(pady=(0, 6))
        txt = tk.Text(
            win, font=MONO, bg=BG, fg=FG, relief="flat",
            wrap="word", highlightthickness=0, padx=4, pady=4
        )
        txt.pack(fill="both", expand=True, padx=12)
        txt.insert("1.0", content)
        txt.configure(state="disabled")
        tk.Button(win, text="[ Fermer ]", command=win.destroy,
                  font=MONO_BOLD, bg=BORDER, fg=ACCENT,
                  activebackground=SELECT_BG, activeforeground="#fff",
                  relief="flat", bd=0, padx=16, pady=6, cursor="hand2"
        ).pack(pady=(8, 14))

    def destroy(self):
        self._stop_auto_refresh()
        super().destroy()


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(
                ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except Exception:
            pass
    VRAMZeroApp().mainloop()
