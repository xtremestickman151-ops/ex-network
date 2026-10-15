"""EX NETWORK - honest WiFi stabilization helper for Windows.
It does NOT increase your connection speed. It reduces drop-outs caused by
adapter power saving, auto-reconnects when the link dies, and runs standard
network repair commands."""
import ctypes, os, re, subprocess, sys, threading, time, queue
import tkinter as tk
from tkinter import ttk, messagebox

APP = "EX NETWORK"
APP_VERSION = "1.2.0"
COPYRIGHT = "\u00a92026 EX Inc."
# JSON manifest: {"version": "x.y.z", "url": "https://.../EX_NETWORK.zip", "notes": "..."}
UPDATE_URL = "https://raw.githubusercontent.com/xtremestickman151-ops/ex-network/main/latest.json"
NOWIN = 0x08000000  # CREATE_NO_WINDOW
# powercfg GUIDs: Wireless Adapter Settings / Power Saving Mode
WL_SUB = "19cbb8fa-5279-450e-9fac-8a3d5fedd0c1"
WL_SET = "12bbebe6-58d6-4636-95bb-3217ef867c1a"
STATE_FILE = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "exwifi_restore.txt")


def run(cmd, timeout=60, ps=False):
    if ps:
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", cmd]
    try:
        si = None
        if os.name == "nt":
            si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        p = subprocess.run(cmd, capture_output=True, timeout=timeout, startupinfo=si,
                           creationflags=NOWIN if os.name == "nt" else 0)
        out = (p.stdout or b"") + (p.stderr or b"")
        return p.returncode, out.decode("utf-8", "replace") if b"\x00" not in out else out.decode("utf-16", "replace")
    except Exception as e:
        return -1, str(e)


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", str(v))[:4]) or (0,)


def check_update():
    """Returns (status, data). status: unconfigured | error | latest | newer"""
    if not UPDATE_URL.strip():
        return "unconfigured", "Update server not configured yet."
    import json, urllib.request
    try:
        req = urllib.request.Request(UPDATE_URL, headers={"User-Agent": APP + "/" + APP_VERSION})
        with urllib.request.urlopen(req, timeout=8) as r:
            m = json.loads(r.read(65536).decode("utf-8"))
        ver, url = str(m["version"]), str(m.get("url", ""))
    except Exception as e:
        return "error", "Could not check for updates (%s)." % (getattr(e, "reason", None) or e)
    if vtuple(ver) > vtuple(APP_VERSION):
        return "newer", {"version": ver, "url": url, "notes": str(m.get("notes", "")), "full_url": str(m.get("full_url", "")), "installer_url": str(m.get("installer_url", ""))}
    return "latest", "You have the latest version (%s)." % APP_VERSION


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


_MUTEX = None


def single_instance():
    """Return True if we should continue. Never shows an error: if another
    instance exists we focus its window; if none is found we just run."""
    global _MUTEX
    if os.name != "nt":
        return True
    try:
        k = ctypes.windll.kernel32
        _MUTEX = k.CreateMutexW(None, False, "Local\\EXWifiEnhance_SingleInstance")
        if k.GetLastError() != 183:  # ERROR_ALREADY_EXISTS
            return True
        u = ctypes.windll.user32
        for _ in range(10):  # previous instance may be closing / elevating
            found = []
            def cb(h, l):
                buf = ctypes.create_unicode_buffer(256)
                u.GetWindowTextW(h, buf, 256)
                if buf.value.startswith(APP) and u.IsWindowVisible(h):
                    found.append(h)
                return True
            u.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(cb), 0)
            if found:
                u.ShowWindow(found[0], 9); u.SetForegroundWindow(found[0])
                return False
            time.sleep(0.3)
        return True  # mutex held but no window: don't block the user
    except Exception:
        return True


def relaunch_admin():
    if _MUTEX:
        ctypes.windll.kernel32.CloseHandle(_MUTEX)
    exe = sys.executable
    params = "" if getattr(sys, "frozen", False) else '"%s"' % os.path.abspath(__file__)
    r = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
    if r > 32:
        os._exit(0)
    return False


def parse_interfaces():
    _, out = run(["netsh", "wlan", "show", "interfaces"], 15)
    d = {}
    for line in out.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            d.setdefault(k.strip().lower(), v.strip())
    g = lambda *ks: next((d[k] for k in ks if k in d), "")
    return {
        "name": g("name"), "state": g("state"), "ssid": g("ssid"), "profile": g("profile"),
        "signal": g("signal"), "rx": g("receive rate (mbps)"), "tx": g("transmit rate (mbps)"),
        "band": g("band"), "channel": g("channel"), "radio": g("radio type"), "desc": g("description"),
    }


def ping(host, n=1, timeout_ms=1000):
    _, out = run(["ping", "-n", str(n), "-w", str(timeout_ms), host], timeout=n * (timeout_ms / 1000 + 1) + 5)
    times = [int(x) for x in re.findall(r"[=<](\d+)\s*ms", out.split("Ping statistics")[0])]
    m = re.search(r"\((\d+)%", out)
    loss = int(m.group(1)) if m else (100 if not times else 0)
    return times, loss


# ---------------------------------------------------------------- UI theme
BG, SIDE, CARD, CARD2 = "#000000", "#0a0a0a", "#1c1c1e", "#2a2a2d"
TEAL, TEAL_D, TXT, MUT = "#e6e6e8", "#3a3a3d", "#f2f2f4", "#9a9aa0"   # TEAL = neutral light accent
GREEN, YEL, RED, GREY = "#30d158", "#ffd60a", "#ff453a", "#3a3a3d"
BORDER, ON = "#3a3a3d", "#30d158"
FONT = "Segoe UI"


def res_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def rrect(c, x1, y1, x2, y2, r, **kw):
    pts = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


class Card(tk.Canvas):
    """Rounded card; put widgets inside .body."""
    def __init__(self, master, title="", height=None, **kw):
        super().__init__(master, bg=BG, highlightthickness=0, height=height or 100, **kw)
        self.title = title
        self.body = tk.Frame(self, bg=CARD)
        self.win = self.create_window(18, 44 if title else 16, window=self.body, anchor="nw")
        self.bind("<Configure>", self._draw)

    def _draw(self, e=None):
        self.delete("bg"); w, h = self.winfo_width(), self.winfo_height()
        rrect(self, 2, 2, w-2, h-2, 18, fill=CARD, outline=BORDER, width=1, tags="bg")
        if self.title:
            self.create_text(18, 22, text=self.title, anchor="w", fill=MUT, font=(FONT, 10, "bold"), tags="bg")
        self.tag_lower("bg"); self.itemconfigure(self.win, width=w-36)


class PillButton(tk.Canvas):
    def __init__(self, master, text, cmd, w=200, h=38, fill=TEAL, fg="#04131f", bg=CARD):
        super().__init__(master, width=w, height=h, bg=bg, highlightthickness=0, cursor="hand2")
        self.cmd, self.fill, self.text, self.fg = cmd, fill, text, fg
        self.bind("<Button-1>", lambda e: cmd()); self.bind("<Enter>", lambda e: self.draw(True)); self.bind("<Leave>", lambda e: self.draw())
        self.draw()

    def draw(self, hover=False):
        self.delete("all"); w, h = int(self["width"]), int(self["height"])
        f = self.fill if not hover else ("#ffffff" if self.fill == TEAL else "#3a3a3d")
        rrect(self, 1, 1, w-1, h-1, h//2, fill=f, outline=BORDER)
        self.create_text(w//2, h//2, text=self.text, fill=self.fg, font=(FONT, 10, "bold"))


class NoticeBox(tk.Canvas):
    """Small rounded bordered box with centered text (copyright notice)."""
    def __init__(self, master, text, bg, w=160, h=28, size=8):
        super().__init__(master, width=w, height=h, bg=bg, highlightthickness=0)
        rrect(self, 1, 1, w-1, h-1, 9, fill="#1c1c1e", outline="#3a3a3d", width=1)
        self.create_text(w//2, h//2, text=text, fill="#c7c7cc", font=(FONT, size))


class Toggle(tk.Canvas):
    def __init__(self, master, var, cmd=None, bg=CARD):
        super().__init__(master, width=48, height=26, bg=bg, highlightthickness=0, cursor="hand2")
        self.var, self.cmd = var, cmd
        self.bind("<Button-1>", self.flip); var.trace_add("write", lambda *a: self.draw()); self.draw()

    def flip(self, e=None):
        self.var.set(not self.var.get())
        if self.cmd: self.cmd()

    def draw(self):
        self.delete("all"); on = self.var.get()
        rrect(self, 1, 1, 47, 25, 12, fill=ON if on else GREY, outline="")
        x = 34 if on else 14
        self.create_oval(x-9, 4, x+9, 22, fill="white", outline="")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP + ("  [Administrator]" if is_admin() else ""))
        try:
            self.iconbitmap(default=res_path("logo.ico"))
        except Exception:
            pass
        try:
            self._icon = tk.PhotoImage(file=res_path("logo256.png")); self.iconphoto(True, self._icon)
        except Exception:
            pass
        self.geometry("900x640"); self.minsize(820, 600); self.configure(bg=BG)
        self.q = queue.Queue(); self.watch = False; self.fails = 0; self.busy = False
        self.stab = os.path.exists(STATE_FILE); self.signal = 0; self.pulse = 0
        self.wvar = tk.BooleanVar(); self.wsock = tk.BooleanVar(); self.autostart_watch = tk.BooleanVar(value=True)

        side = tk.Frame(self, bg=SIDE, width=200); side.pack(side="left", fill="y"); side.pack_propagate(False)
        logo = tk.Canvas(side, width=200, height=90, bg=SIDE, highlightthickness=0); logo.pack()
        logo.create_oval(20, 28, 52, 60, outline="#8e8e93", width=2)
        for r in (6, 11): logo.create_arc(36-r, 44-r, 36+r, 44+r, start=45, extent=90, style="arc", outline=ON, width=2)
        logo.create_text(62, 36, text="EX", anchor="w", fill=TXT, font=(FONT, 15, "bold"))
        logo.create_text(62, 54, text="NETWORK", anchor="w", fill=MUT, font=(FONT, 9, "bold"))
        self.navs = {}; self.pages = {}
        main = tk.Frame(self, bg=BG); main.pack(side="left", fill="both", expand=True)
        if not is_admin():
            bar = tk.Frame(main, bg="#2a1a1a", highlightbackground="#5a2a2a", highlightthickness=1); bar.pack(fill="x", padx=20, pady=(16, 0))
            tk.Label(bar, text="⚠  Standard user: Stabilize, Release/Renew and Winsock reset need administrator rights.",
                     bg="#2a1a1a", fg="#ff9f99", font=(FONT, 9)).pack(side="left", padx=10, pady=8)
            PillButton(bar, "Restart as admin", relaunch_admin, w=140, h=30, fill=TEAL, bg="#2a1a1a").pack(side="right", padx=8, pady=4)
        self.content = tk.Frame(main, bg=BG); self.content.pack(fill="both", expand=True, padx=20, pady=16)
        for name, icon in (("Home", "⌂"), ("Tools", "⚒"), ("Log", "☰"), ("Settings", "⚙")):
            l = tk.Label(side, text=f"  {icon}   {name}", anchor="w", bg=SIDE, fg=MUT, font=(FONT, 11), cursor="hand2", padx=14, pady=10)
            l.pack(fill="x", padx=12, pady=2); l.bind("<Button-1>", lambda e, n=name: self.show(n)); self.navs[name] = l
            self.pages[name] = tk.Frame(self.content, bg=BG)
        tk.Frame(side, bg=BORDER, height=1).pack(fill="x", padx=24, pady=8)
        up = tk.Label(side, text="  ⟳   Check for updates", anchor="w", bg=SIDE, fg=MUT, font=(FONT, 11), cursor="hand2", padx=14, pady=10)
        up.pack(fill="x", padx=12, pady=2); up.bind("<Button-1>", lambda e: self.update_click(popup=True))
        up.bind("<Enter>", lambda e: up.configure(bg=CARD2, fg=TXT)); up.bind("<Leave>", lambda e: up.configure(bg=SIDE, fg=MUT))
        NoticeBox(side, COPYRIGHT, SIDE, w=160, h=28).pack(side="bottom", pady=(4, 14))
        tk.Label(side, text="Honest tool: reduces drop-outs,\ndoes not raise your plan's speed.",
                 bg=SIDE, fg=MUT, font=(FONT, 8), justify="left").pack(side="bottom", anchor="w", padx=20, pady=(4, 2))
        self.build_home(); self.build_tools(); self.build_log(); self.build_settings()
        self.show("Home")
        self.after(200, self.pump); self.after(100, self.refresh); self.after(50, self.animate)

    def show(self, name):
        for n, p in self.pages.items():
            p.pack_forget(); self.navs[n].configure(bg=SIDE, fg=MUT)
        self.pages[name].pack(fill="both", expand=True); self.navs[name].configure(bg=CARD2, fg=TXT)

    # ---------------- pages
    def build_home(self):
        p = self.pages["Home"]
        left = tk.Frame(p, bg=BG); left.pack(side="left", fill="both", expand=True)
        self.pw = tk.Canvas(left, bg=BG, highlightthickness=0, width=360, height=380, cursor="hand2"); self.pw.pack(pady=(4, 0))
        self.pw.bind("<Button-1>", lambda e: self.power_click())
        self.stat_txt = tk.Label(left, bg=BG, font=(FONT, 20, "bold")); self.stat_txt.pack()
        self.stat_sub = tk.Label(left, bg=BG, fg=MUT, font=(FONT, 10), wraplength=360); self.stat_sub.pack(pady=4)
        right = tk.Frame(p, bg=BG, width=280); right.pack(side="right", fill="y"); right.pack_propagate(False)
        c = Card(right, "CONNECTION", height=250); c.pack(fill="x")
        self.bars = tk.Canvas(c.body, width=120, height=64, bg=CARD, highlightthickness=0); self.bars.pack(anchor="w")
        self.ssid_l = tk.Label(c.body, bg=CARD, fg=TXT, font=(FONT, 15, "bold"), anchor="w"); self.ssid_l.pack(fill="x", pady=(6, 0))
        self.band_l = tk.Label(c.body, bg=CARD, fg=TEAL, font=(FONT, 10), anchor="w"); self.band_l.pack(fill="x")
        self.rate_l = tk.Label(c.body, bg=CARD, fg=MUT, font=(FONT, 9), anchor="w", justify="left"); self.rate_l.pack(fill="x", pady=(8, 0))
        w = Card(right, "AUTO-RECONNECT WATCHDOG", height=130); w.pack(fill="x", pady=14)
        row = tk.Frame(w.body, bg=CARD); row.pack(fill="x")
        tk.Label(row, text="Reconnect after 3\nfailed pings (1.1.1.1 / 8.8.8.8)", bg=CARD, fg=TXT, font=(FONT, 9), justify="left").pack(side="left")
        Toggle(row, self.wvar, self.toggle_watch).pack(side="right")
        self.wd_l = tk.Label(w.body, text="Off", bg=CARD, fg=MUT, font=(FONT, 9), anchor="w"); self.wd_l.pack(fill="x", pady=(6, 0))
        self.draw_status()

    def build_tools(self):
        p = self.pages["Tools"]
        r = Card(p, "ONE-CLICK REPAIR", height=170); r.pack(fill="x")
        tk.Label(r.body, text="Flush DNS, release and renew the IP address. Briefly disconnects you.",
                 bg=CARD, fg=TXT, font=(FONT, 10)).pack(anchor="w")
        row = tk.Frame(r.body, bg=CARD); row.pack(fill="x", pady=8)
        Toggle(row, self.wsock).pack(side="left")
        tk.Label(row, text="  Also reset Winsock (admin, needs a REBOOT to take effect)", bg=CARD, fg=YEL, font=(FONT, 9)).pack(side="left")
        PillButton(r.body, "Run Repair", self.repair_click, w=160).pack(anchor="w")
        t = Card(p, "PING / LATENCY TEST", height=230); t.pack(fill="x", pady=14)
        row = tk.Frame(t.body, bg=CARD); row.pack(fill="x")
        self.host = tk.StringVar(value="1.1.1.1"); self.cnt = tk.StringVar(value="20")
        for lbl, var, wd in (("Host", self.host, 18), ("Count", self.cnt, 5)):
            tk.Label(row, text=lbl, bg=CARD, fg=MUT, font=(FONT, 9)).pack(side="left", padx=(0, 6))
            tk.Entry(row, textvariable=var, width=wd, bg=CARD2, fg=TXT, insertbackground=TXT, relief="flat",
                     font=(FONT, 10)).pack(side="left", ipady=5, padx=(0, 14))
        PillButton(row, "Run test", lambda: self.bg(self.ping_test), w=110, h=32).pack(side="left")
        res = tk.Frame(t.body, bg=CARD); res.pack(fill="x", pady=16)
        self.pv = {}
        for k in ("Average", "Min / Max", "Packet loss"):
            f = tk.Frame(res, bg=CARD2); f.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(f, text=k, bg=CARD2, fg=MUT, font=(FONT, 9)).pack(pady=(8, 0))
            v = tk.StringVar(value="—"); self.pv[k] = v
            tk.Label(f, textvariable=v, bg=CARD2, fg=TEAL, font=(FONT, 16, "bold")).pack(pady=(0, 8))
        self.pres = tk.StringVar(value=""); tk.Label(t.body, textvariable=self.pres, bg=CARD, fg=MUT, font=(FONT, 9)).pack(anchor="w")

    def build_log(self):
        c = Card(self.pages["Log"], "EVENT LOG", height=500); c.pack(fill="both", expand=True)
        self.log = tk.Text(c.body, height=24, bg=CARD, fg=TXT, relief="flat", font=("Consolas", 9), state="disabled",
                           insertbackground=TXT, highlightthickness=0)
        self.log.pack(fill="both", expand=True)
        PillButton(c.body, "Clear", lambda: (self.log.configure(state="normal"), self.log.delete("1.0", "end"),
                   self.log.configure(state="disabled")), w=90, h=30, fill=CARD2, fg=TXT).pack(anchor="e", pady=6)

    def build_settings(self):
        p = self.pages["Settings"]
        s = Card(p, "STABILIZE DETAILS", height=210); s.pack(fill="x")
        tk.Label(s.body, justify="left", wraplength=560, bg=CARD, fg=TXT, font=(FONT, 10), text=
                 "Stabilize turns off the WiFi adapter's power-saving features and sets the Windows power plan's "
                 "'Wireless Adapter Settings' to Maximum Performance (AC and battery). This can reduce drop-outs and "
                 "latency spikes. It does NOT increase your internet speed.\n\nYour previous power-plan values are saved "
                 "and put back when you switch Stabilize off.").pack(anchor="w")
        PillButton(s.body, "Restore Windows defaults", lambda: self.bg(self.stabilize, False), w=210, fill=CARD2, fg=TXT).pack(anchor="w", pady=10)
        u = Card(p, "ABOUT & UPDATES", height=170); u.pack(fill="x", pady=(14, 0))
        tk.Label(u.body, text="%s  version %s" % (APP, APP_VERSION), bg=CARD, fg=TXT, font=(FONT, 11, "bold")).pack(anchor="w")
        NoticeBox(u.body, COPYRIGHT, CARD, w=170, h=30, size=9).pack(anchor="w", pady=(6, 0))
        row = tk.Frame(u.body, bg=CARD); row.pack(fill="x", pady=8)
        PillButton(row, "Check for updates", self.update_click, w=180, fill=CARD2, fg=TXT).pack(side="left")
        self.upd = tk.StringVar(value=""); tk.Label(row, textvariable=self.upd, bg=CARD, fg=MUT, font=(FONT, 9)).pack(side="left", padx=12)
        a = Card(p, "ACCOUNT", height=120); a.pack(fill="x", pady=14)
        adm = is_admin()
        tk.Label(a.body, text=("Running as administrator" if adm else "Running as standard user"), bg=CARD,
                 fg=GREEN if adm else YEL, font=(FONT, 11, "bold")).pack(anchor="w")
        if not adm:
            PillButton(a.body, "Restart as administrator", relaunch_admin, w=210).pack(anchor="w", pady=8)

    # ---------------- drawing
    def animate(self):
        self.pulse = (self.pulse + 1) % 60; self.draw_power(); self.after(50, self.animate)

    def draw_power(self):
        import math
        c = self.pw; c.delete("all"); cx, cy = 180, 185
        on = self.stab; col = ON if on else "#8e8e93"
        k = (math.sin(self.pulse / 60 * 2 * math.pi) + 1) / 2
        if on:  # soft glow: concentric rings fading from green to black
            for i in range(8):
                r = 118 + i * 5 + k * 4; t = 1 - i / 8
                g = "#%02x%02x%02x" % (int(0x30 * t * .5), int(0xd1 * t * .5), int(0x58 * t * .5))
                c.create_oval(cx-r, cy-r, cx+r, cy+r, outline=g, width=3)
        for i in range(12):  # vertical-ish gradient disc
            r = 115 - i * 2; v = 0x1c + i * 2
            c.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#%02x%02x%02x" % (v, v, v + 2), outline="")
        c.create_oval(cx-115, cy-115, cx+115, cy+115, outline=BORDER, width=1)
        c.create_oval(cx-92, cy-92, cx+92, cy+92, fill=CARD, outline="#48484a", width=1)
        if self.busy:
            c.create_arc(cx-128, cy-128, cx+128, cy+128, start=self.pulse * 12, extent=90, style="arc", outline="#e6e6e8", width=3)
        c.create_arc(cx-40, cy-40, cx+40, cy+40, start=120, extent=300, style="arc", outline=col, width=7)
        c.create_line(cx, cy-52, cx, cy-6, fill=col, width=7, capstyle="round")
        c.create_text(cx, cy+66, text="ON" if on else "OFF", fill=col, font=(FONT, 11, "bold"))

    def draw_status(self):
        if self.stab:
            self.stat_txt.configure(text="Protected", fg=ON)
            self.stat_sub.configure(text="Power saving disabled on your WiFi adapter. Tap to restore.")
        else:
            self.stat_txt.configure(text="Not stabilized", fg=TXT)
            self.stat_sub.configure(text="Tap the button to stop Windows from putting your WiFi adapter to sleep.")

    def draw_bars(self, sig, connected):
        c = self.bars; c.delete("all")
        col = GREEN if sig >= 70 else YEL if sig >= 40 else RED
        lit = 0 if not connected else max(1, min(5, (sig + 19) // 20))
        for i in range(5):
            h = 12 + i * 12; x = 6 + i * 20
            rrect(c, x, 64 - h, x + 13, 62, 4, fill=col if i < lit else GREY, outline="")

    # ---------------- plumbing
    def emit(self, msg, which=1):
        self.q.put((1, time.strftime("%H:%M:%S  ") + msg))

    def pump(self):
        while not self.q.empty():
            kind, v = self.q.get()
            if kind == "status":
                conn = v["state"].lower() == "connected"
                try: sig = int(v["signal"].rstrip("%"))
                except ValueError: sig = 0
                self.draw_bars(sig, conn)
                self.ssid_l.configure(text=v["ssid"] if conn else ("Disconnected" if v["name"] else "No WiFi adapter"))
                bc = " · ".join(x for x in (v["band"], ("Channel " + v["channel"]) if v["channel"] else "", v["radio"]) if x)
                self.band_l.configure(text=bc or "—")
                self.rate_l.configure(text=f"Signal {v['signal'] or '—'}   ↓ {v['rx'] or '—'} Mbps   ↑ {v['tx'] or '—'} Mbps\n{v['desc']}")
            elif kind == "ping":
                for k, val in v.items(): self.pv[k].set(val)
            elif kind == "pres": self.pres.set(v)
            elif kind == "wd": self.wd_l.configure(text=v)
            elif kind == "stab":
                self.stab = v; self.busy = False; self.draw_status()
            else:
                self.log.configure(state="normal"); self.log.insert("end", v + "\n"); self.log.see("end"); self.log.configure(state="disabled")
        self.after(200, self.pump)

    def bg(self, fn, *a):
        threading.Thread(target=fn, args=a, daemon=True).start()

    def need_admin(self):
        if is_admin(): return True
        if messagebox.askyesno(APP, "This action needs administrator rights.\nRestart as administrator now?"):
            relaunch_admin()
        return False

    def refresh(self):
        self.bg(lambda: self.q.put(("status", parse_interfaces()))); self.after(3000, self.refresh)

    def power_click(self):
        if self.busy: return
        if not self.need_admin(): return
        self.busy = True; self.bg(self.stabilize, not self.stab)

    def update_click(self, popup=False):
        self.upd.set("Checking…")
        def job():
            st, d = check_update()
            self.after(0, lambda: self.update_result(st, d, popup))
        self.bg(job)

    def update_result(self, st, d, popup=False):
        if st != "newer":
            self.upd.set(d); self.emit("Update check: " + d)
            if popup:
                (messagebox.showinfo if st == "latest" else messagebox.showwarning)(APP, d)
            return
        self.upd.set("Version %s available" % d["version"]); self.emit("Update available: " + d["version"])
        msg = "Version %s is available (you have %s).\n\n%s" % (d["version"], APP_VERSION, d["notes"] or "")
        link = d.get("installer_url") or d["url"]
        if d.get("installer_url"):
            msg += "\n\nUpdate: download and run the installer (close the app first). Your settings are kept."
        else:
            msg += "\n\nUpdate: extract the downloaded zip over your existing 'EX NETWORK' folder (close the app first)."
        if link.lower().startswith(("https://", "http://")):
            if messagebox.askyesno(APP, msg + "\n\nOpen the download in your browser?"):
                import webbrowser; webbrowser.open(link)
        else:
            messagebox.showinfo(APP, msg)

    # ---------------- features (unchanged logic)
    def stabilize(self, on):
        try:
            if not is_admin():
                self.after(0, self.need_admin); return
            name = parse_interfaces()["name"]
            if not name:
                self.emit("No WiFi interface found."); return
            n = name.replace("'", "''")
            if on:
                _, prev = run(["powercfg", "/query", "SCHEME_CURRENT", WL_SUB, WL_SET])
                m = re.findall(r"0x([0-9a-fA-F]+)", prev)
                with open(STATE_FILE, "w") as f:
                    if len(m) >= 2: f.write("%d %d" % (int(m[-2], 16), int(m[-1], 16)))
                rc, out = run("Disable-NetAdapterPowerManagement -Name '%s' -ErrorAction Stop; "
                              "Set-NetAdapterPowerManagement -Name '%s' -AllowComputerToTurnOffDevice Disabled -ErrorAction SilentlyContinue" % (n, n), ps=True)
                self.emit("Adapter power management disabled." if rc == 0 else "Adapter power mgmt: " + out.strip()[:300])
                for flag in ("/setacvalueindex", "/setdcvalueindex"):
                    run(["powercfg", flag, "SCHEME_CURRENT", WL_SUB, WL_SET, "0"])
                run(["powercfg", "/setactive", "SCHEME_CURRENT"])
                self.emit("Power plan: wireless adapter set to Maximum Performance (AC & battery).")
            else:
                rc, out = run("Enable-NetAdapterPowerManagement -Name '%s' -ErrorAction Stop; "
                              "Set-NetAdapterPowerManagement -Name '%s' -AllowComputerToTurnOffDevice Enabled -ErrorAction SilentlyContinue" % (n, n), ps=True)
                self.emit("Adapter power management re-enabled." if rc == 0 else "Restore adapter: " + out.strip()[:300])
                ac, dc = 0, 3
                try: ac, dc = map(int, open(STATE_FILE).read().split())
                except Exception: pass
                try: os.remove(STATE_FILE)
                except Exception: pass
                run(["powercfg", "/setacvalueindex", "SCHEME_CURRENT", WL_SUB, WL_SET, str(ac)])
                run(["powercfg", "/setdcvalueindex", "SCHEME_CURRENT", WL_SUB, WL_SET, str(dc)])
                run(["powercfg", "/setactive", "SCHEME_CURRENT"])
                self.emit("Power plan wireless setting restored (AC=%d, DC=%d)." % (ac, dc))
        finally:
            self.q.put(("stab", os.path.exists(STATE_FILE)))

    def toggle_watch(self):
        self.watch = self.wvar.get()
        self.emit("Watchdog " + ("started." if self.watch else "stopped."))
        self.q.put(("wd", "Monitoring…" if self.watch else "Off"))
        if self.watch: self.bg(self.watch_loop)

    def watch_loop(self):
        self.fails = 0
        profile = parse_interfaces()["profile"] or parse_interfaces()["ssid"]
        while self.watch:
            ok = any(ping(h, 1, 1500)[1] < 100 for h in ("1.1.1.1", "8.8.8.8"))
            p = parse_interfaces()["profile"]
            if p: profile = p
            if ok:
                if self.fails >= 3: self.emit("Connection restored.")
                self.fails = 0; self.q.put(("wd", "Online · last check " + time.strftime("%H:%M:%S")))
            else:
                self.fails += 1; self.emit("Ping failed (%d consecutive)." % self.fails)
                self.q.put(("wd", "Offline · %d failed checks" % self.fails))
                if self.fails == 3 or (self.fails > 3 and self.fails % 6 == 0):
                    if profile:
                        rc, out = run(["netsh", "wlan", "connect", "name=" + profile])
                        self.emit("Reconnect to '%s': %s" % (profile, out.strip()[:200]))
                    else:
                        self.emit("No known profile to reconnect to.")
            for _ in range(10):
                if not self.watch: return
                time.sleep(0.5)

    def repair_click(self):
        if self.wsock.get() and not is_admin():
            self.need_admin(); return
        if not is_admin() and not messagebox.askyesno(APP, "Not admin: release/renew may fail. Continue anyway (flushdns works)?"):
            return
        self.emit("Repair started (see Log)."); self.bg(self.repair, self.wsock.get())

    def repair(self, ws):
        steps = [["ipconfig", "/flushdns"], ["ipconfig", "/release"], ["ipconfig", "/renew"]]
        if ws: steps.append(["netsh", "winsock", "reset"])
        for s in steps:
            self.emit("Running: " + " ".join(s))
            rc, out = run(s, 120)
            self.emit(("OK" if rc == 0 else "Exit %d" % rc) + ": " + " ".join(out.split())[:250])
        if ws: self.emit("Winsock reset done. Please REBOOT your PC.")
        self.emit("Repair finished.")
        self.after(0, lambda: messagebox.showinfo(APP, "Repair finished." + (" Please reboot your PC." if ws else "")))

    def ping_test(self):
        h = self.host.get().strip() or "1.1.1.1"
        try: n = max(1, min(100, int(self.cnt.get())))
        except ValueError: n = 20
        self.q.put(("pres", "Testing %s ×%d …" % (h, n)))
        times, loss = ping(h, n, 1000)
        self.q.put(("ping", {"Average": "%.0f ms" % (sum(times) / len(times)) if times else "n/a",
                             "Min / Max": "%d / %d" % (min(times), max(times)) if times else "—",
                             "Packet loss": "%d%%" % loss}))
        self.q.put(("pres", "Last test: %s, %d packets" % (h, n)))
        self.emit("Ping %s: %d replies, loss %d%%" % (h, len(times), loss))


if __name__ == "__main__":
    if single_instance():
        App().mainloop()
