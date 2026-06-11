#!/usr/bin/env python3
"""
Interview Copilot — Real-time AI interview assistant
Similar to LockedIn AI but open-source and runs locally.

Quick Start:
  1. pip install -r requirements.txt
  2. cp .env.example .env        (then fill in ANTHROPIC_API_KEY)
  3. python copilot.py

All settings are loaded from the .env file in the same directory.
See .env.example for the full list of available variables.
"""

import os
import json
import re
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext
from difflib import SequenceMatcher
import urllib.request

try:
    from pynput import keyboard as _kb
    _HAS_PYNPUT = True
except ImportError:
    _HAS_PYNPUT = False

# Load .env from the project root before reading any os.getenv() calls
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass  # python-dotenv is optional; env vars can be set in the shell instead

JOB_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "job_config.json")

# Web app API base URL — set COPILOT_API_URL to point at prod
_API_BASE = os.getenv("COPILOT_API_URL", "http://localhost:4001")


def load_job_config() -> dict:
    """Fetch active job from the web app API; fall back to local job_config.json."""
    try:
        url = f"{_API_BASE}/api/jobs/active"
        with urllib.request.urlopen(url, timeout=3) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        pass
    # Fallback: local file written by the old job_setup.py
    if os.path.exists(JOB_CONFIG_FILE):
        try:
            with open(JOB_CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def build_job_context(job: dict) -> str:
    if not job or not job.get("role"):
        return ""
    lines = [
        "\n=== TARGET JOB ===",
        f"Role applying for: {job.get('role', '')}",
        f"Company: {job.get('company', '')}",
    ]
    if job.get("location"):
        lines.append(f"Location: {job.get('location', '')}")
    if job.get("job_description"):
        desc = job["job_description"][:3000]
        lines.append(f"\nJob Description:\n{desc}")
    lines.append("=== END TARGET JOB ===\n")
    lines.append(
        "IMPORTANT: Tailor every answer to highlight the parts of Niraj's background "
        "that are most relevant to this specific role and company. Reference the job "
        "description requirements when choosing which experience to emphasize."
    )
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION — all values come from .env (see .env.example)
# ══════════════════════════════════════════════════════════════
def _bool(val: str) -> bool:
    return val.strip().lower() in ("1", "true", "yes")

CONFIG = {
    "api_key":          os.getenv("ANTHROPIC_API_KEY", ""),
    "model":            os.getenv("COPILOT_MODEL",            "claude-haiku-4-5-20251001"),
    "role":             os.getenv("COPILOT_ROLE",             "Principal Software Engineer"),
    "language":         os.getenv("COPILOT_LANGUAGE",         "en-US"),
    "energy_threshold": int(os.getenv("COPILOT_ENERGY_THRESHOLD", "300")),
    "pause_threshold":  float(os.getenv("COPILOT_PAUSE_THRESHOLD", "1.2")),
    "opacity":          float(os.getenv("COPILOT_OPACITY",    "0.94")),
    "width":            int(os.getenv("COPILOT_WIDTH",        "500")),
    "height":           int(os.getenv("COPILOT_HEIGHT",       "420")),
    "font_size":        int(os.getenv("COPILOT_FONT_SIZE",    "11")),
    "theme":            os.getenv("COPILOT_THEME",            "dark"),
    "always_on_top":    _bool(os.getenv("COPILOT_ALWAYS_ON_TOP", "true")),
}

# Coaching prompt — pre-loaded with Niraj Byanjankar's resume
SYSTEM_PROMPT = """You are Niraj Byanjankar. You are in a live job interview right now.
Your job is to give me the exact words to say — natural spoken English, first person, confident but not arrogant.

HARD RULES:
- Output ONLY what I should say out loud. No headers. No labels. No bullet points. No markdown.
- 3–5 sentences max. Tight, direct, easy to read while talking.
- Sound like a real person — not a resume, not a chatbot. Use contractions. Vary sentence length.
- Pick the ONE most relevant story or fact from my background. Do not dump everything.
- Every answer must use a DIFFERENT example or angle. Never repeat a story already used this session.
- Never use these words: "leverage", "passionate", "stakeholder", "synergy", "utilize", "circle back", "deep dive", "at the end of the day".
- If the question is vague, anchor it immediately to one specific real thing I built or solved.
- For behavioral questions, give a quick concrete story: what the situation was, what I did, what changed.
- For technical questions, lead with the technology or approach, then a real example.

MY BACKGROUND (draw from this, but pick selectively — not all at once):

17+ years in software engineering. Most recently Principal Engineer – Data Governance at Verizon (2021–2025),
where I owned the enterprise data governance program: BigQuery Data Catalog, metadata lineage across 200+ pipelines,
a self-service catalog portal shipped in 2 weeks, AI/ML governance, and a 30% reduction in data quality incidents
through automated DQ rules. I also built the Application Data Classification system covering GDPR, CPRA, CCPA, CPNI.

Before that: BI Manager at Verizon (2019–2020) — ran a team of analysts, built Logstash/Splunk pipelines,
trigger-based alerting. DevOps Principal Engineer at Verizon (2017–2018) — Jenkins/GitLab CI, Python REST APIs,
ETL automation. Senior Web Dev at Verizon (2015–2017) — full-stack portal ownership.

Earlier: LRN Corporation (e-learning, Zend/PHP, Agile), Olympus (lead dev, SAP integration, JDE/AS400),
Auction.com (portals, email/SMS), Golfsmith (internal retail site, Oracle/MySQL, Pentaho migrations).

Tech I actually use: Python, SQL, GCP/BigQuery, Airflow, Docker, GitLab CI, Flask, ReactJS,
IBM ICP4D, Collibra, CyberArk/PAM, Fortify, BlackDuck, Splunk, Tableau.

Education: MS Computer Information Systems (Bellevue University), BS MIS (NW Missouri State).
Certs: Google Cloud Associate Cloud Engineer, Google Generative AI Leader.

Current target role: {role}

TONE EXAMPLES — write responses that sound like this:
- "Yeah, at Verizon I owned the full data governance program — everything from metadata lineage to the classification system for GDPR and CCPA compliance. The one I'm most proud of is the self-service catalog portal we shipped in two weeks. Teams went from filing tickets to finding their datasets themselves."
- "Honestly data quality was one of the harder problems. We had incidents constantly until I built automated DQ rules with anomaly detection on top. That cut incidents by about 30% and gave the data stewards something concrete to act on."
- "My DevOps background covers both sides — I've built the pipelines and I've also been the one on-call when they break. At Verizon I ran Jenkins and GitLab CI for production deployments, and before that I was writing the ETL shell scripts myself."

Now respond to what the interviewer just said."""
# ══════════════════════════════════════════════════════════════


# ─── Colour palettes ──────────────────────────────────────────
DARK = {
    "bg": "#12121f",
    "panel": "#1c1c2e",
    "header": "#0d0d1a",
    "text": "#e8e8f0",
    "dim": "#6b6b88",
    "green": "#00d4aa",
    "yellow": "#f5c518",
    "red": "#ff5f57",
    "blue": "#4fc3f7",
    "border": "#2a2a42",
    "btn_fg": "#000000",
}
LIGHT = {
    "bg": "#f0f0f5",
    "panel": "#ffffff",
    "header": "#e0e0ea",
    "text": "#111122",
    "dim": "#777788",
    "green": "#009977",
    "yellow": "#b8860b",
    "red": "#cc3333",
    "blue": "#0077bb",
    "border": "#ccccdd",
    "btn_fg": "#ffffff",
}
# ─────────────────────────────────────────────────────────────


def get_ai_response(question: str, config: dict, on_chunk=None) -> str:
    """Call Claude API. Streams text via on_chunk(text) if provided, else returns full string."""
    api_key = config.get("api_key", "")
    if not api_key:
        msg = (
            "⚠  API key missing.\n\n"
            "Set it in one of two ways:\n\n"
            "  Option 1 — Environment variable:\n"
            "    Mac/Linux:  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "    Windows:    set ANTHROPIC_API_KEY=sk-ant-...\n\n"
            "  Option 2 — Edit CONFIG['api_key'] at the top of copilot.py"
        )
        if on_chunk:
            on_chunk(msg)
        return msg
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        job = load_job_config()
        job_context = build_job_context(job)
        target_role = job.get("role") or config.get("role", "professional")
        prompt = SYSTEM_PROMPT.format(role=target_role)
        if job_context:
            prompt = prompt.replace("=== END RESUME ===", f"=== END RESUME ===\n{job_context}")
        kwargs = dict(
            model=config["model"],
            max_tokens=400,
            system=prompt,
            messages=[{"role": "user", "content": f'Interviewer said: "{question}"'}],
        )
        if on_chunk:
            with client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    on_chunk(text)
            return ""
        else:
            msg = client.messages.create(**kwargs)
            return msg.content[0].text.strip()
    except ImportError:
        err = "❌  'anthropic' package not found.\n\nRun:  pip install anthropic"
        if on_chunk:
            on_chunk(err)
        return err
    except Exception as exc:
        err = f"❌  Error: {exc}"
        if on_chunk:
            on_chunk(err)
        return err


# ─── Audio listener ───────────────────────────────────────────
class AudioListener:
    """Captures mic audio and pushes transcripts to a queue."""

    def __init__(self, out_q: queue.Queue, config: dict):
        self.q = out_q
        self.cfg = config
        self._running = False
        self._paused = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def _loop(self):
        try:
            import speech_recognition as sr
        except ImportError:
            self.q.put(("error", "speech_recognition not installed. Run: pip install SpeechRecognition pyaudio"))
            return

        r = sr.Recognizer()
        r.energy_threshold = self.cfg["energy_threshold"]
        r.pause_threshold = self.cfg["pause_threshold"]
        r.dynamic_energy_threshold = True

        try:
            mic = sr.Microphone()
        except Exception as e:
            self.q.put(("error", f"Microphone error: {e}\nUse 'Type Question' instead."))
            return

        with mic as source:
            r.adjust_for_ambient_noise(source, duration=1.0)
            while self._running:
                try:
                    audio = r.listen(source, timeout=5, phrase_time_limit=20)
                    text = r.recognize_google(audio, language=self.cfg["language"])
                    if text.strip() and not self._paused:
                        self.q.put(("transcript", text.strip()))
                except Exception:
                    # WaitTimeoutError, UnknownValueError — normal, keep going
                    pass


# ─── Question detection ───────────────────────────────────────
# Matches question phrases anywhere in the sentence (handles openers like
# "let's move on...", "so...", "I'd like to know..." before the actual ask).
_QUESTION_ANYWHERE = re.compile(
    r"\b("
    r"how (would|do|did|can|could|should|might|will|are|is)|"
    r"what (would|do|did|can|could|should|is|are|was|were|have|has)|"
    r"why (did|do|would|is|are|was|were|don't|doesn't)|"
    r"when (did|do|would|will|have|has)|"
    r"where (do|did|would|have|has|is|are)|"
    r"who (is|are|was|were|would|did|do)|"
    r"which (is|are|would|do|did)|"
    r"can you|could you|would you|should you|will you|"
    r"do you|did you|have you|had you|"
    r"is there|are there|was there|were there|"
    r"tell me|explain|describe|walk me|walk us|"
    r"give me|give us|talk (me|us) through|share (with|your)|"
    r"help me understand|help us understand|"
    r"what('s| is) your"
    r")",
    re.IGNORECASE,
)

def _is_question(text: str) -> bool:
    t = text.strip()
    if len(t.split()) < 4:      # too short — noise or filler
        return False
    if "?" in t:
        return True
    if _QUESTION_ANYWHERE.search(t):   # search, not match — works anywhere in sentence
        return True
    return False


# ─── AI worker ────────────────────────────────────────────────
class AIWorker:
    """Reads transcripts, calls AI, pushes responses."""

    def __init__(self, in_q: queue.Queue, out_q: queue.Queue, config: dict):
        self.iq = in_q
        self.oq = out_q
        self.cfg = config
        self._running = False
        self._thread = None
        self._last_question = ""

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _is_new_question(self, text: str) -> bool:
        if not self._last_question:
            return True
        ratio = SequenceMatcher(None, self._last_question.lower(), text.lower()).ratio()
        return ratio < 0.75

    def _loop(self):
        while self._running:
            try:
                kind, content = self.iq.get(timeout=1)
                if kind == "transcript":
                    if not _is_question(content):
                        self.oq.put(("not_question", content))
                        continue
                    if not self._is_new_question(content):
                        continue
                    self._last_question = content
                    self.oq.put(("stream_start", content))
                    get_ai_response(content, self.cfg, on_chunk=lambda t: self.oq.put(("chunk", t)))
                    self.oq.put(("stream_done", None))
                elif kind == "error":
                    self.oq.put(("error", content))
            except queue.Empty:
                pass


# ─── Overlay Window ───────────────────────────────────────────
class CopilotOverlay:

    def __init__(self, config: dict):
        self.cfg = config
        self.c = DARK if config.get("theme", "dark") == "dark" else LIGHT

        # Thread communication queues
        self.transcript_q: queue.Queue = queue.Queue()   # AudioListener → AIWorker
        self.response_q:   queue.Queue = queue.Queue()   # AIWorker → UI

        self.listener  = AudioListener(self.transcript_q, config)
        self.ai_worker = AIWorker(self.transcript_q, self.response_q, config)
        self._listening = False

        # Drag state
        self._drag_x = 0
        self._drag_y = 0

        self._kb_listener = None

        self._build_ui()
        self._start_keyboard_listener()

    # ── Build UI ──────────────────────────────────────────────
    def _build_ui(self):
        c = self.c

        root = tk.Tk()
        self.root = root
        root.title("Interview Copilot")

        # Size: 1/3 screen width, 85% screen height, centered
        # withdraw first so the window doesn't flash at the wrong position
        root.withdraw()
        root.update_idletasks()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        w = sw // 3
        h = sh - 60          # full height minus taskbar gap
        x = (sw - w) // 2   # centered horizontally
        y = 0                # pinned to top
        root.geometry(f"{w}x{h}+{x}+{y}")
        root.deiconify()

        root.configure(bg=c["bg"])
        root.wm_attributes("-topmost", self.cfg["always_on_top"])
        root.wm_attributes("-alpha", self.cfg["opacity"])
        root.resizable(True, True)
        root.protocol("WM_DELETE_WINDOW", self._quit)

        # ── Header ──
        hdr = tk.Frame(root, bg=c["header"], height=36)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        for widget in (hdr,):
            widget.bind("<Button-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_move)

        tk.Label(hdr, text="🎯  Interview Copilot",
                 bg=c["header"], fg=c["text"],
                 font=("Helvetica", 12, "bold")).pack(side="left", padx=10, pady=6)

        role_lbl = tk.Label(hdr, text=f"[ {self.cfg['role']} ]",
                            bg=c["header"], fg=c["dim"],
                            font=("Helvetica", 9))
        role_lbl.pack(side="left")

        # Window controls
        for txt, fg, cmd in [("✕", c["red"], self._quit),
                              ("—", c["dim"], lambda: root.iconify())]:
            tk.Button(hdr, text=txt, bg=c["header"], fg=fg, bd=0,
                      font=("Helvetica", 13), cursor="hand2",
                      activebackground=c["header"],
                      command=cmd).pack(side="right", padx=4)

        # ── Status bar ──
        sb = tk.Frame(root, bg=c["panel"], pady=3)
        sb.pack(fill="x", padx=4, pady=(3, 0))

        self.dot   = tk.Label(sb, text="●", fg=c["dim"], bg=c["panel"],
                              font=("Helvetica", 13))
        self.dot.pack(side="left", padx=(8, 3))
        self.status_lbl = tk.Label(sb, text="Ready — press Start or type a question",
                                   fg=c["dim"], bg=c["panel"],
                                   font=("Helvetica", 9))
        self.status_lbl.pack(side="left")

        # ── "Heard" label ──
        tk.Label(root, text="HEARD:", bg=c["bg"], fg=c["dim"],
                 font=("Helvetica", 8, "bold")).pack(anchor="w", padx=8, pady=(6, 0))

        self.heard_txt = tk.Text(root, height=2, bg=c["panel"], fg=c["blue"],
                                  font=("Helvetica", self.cfg["font_size"] - 1),
                                  bd=0, padx=6, pady=4, wrap="word",
                                  state="disabled", relief="flat")
        self.heard_txt.pack(fill="x", padx=4)

        # ── "AI Answer" label ──
        tk.Label(root, text="AI ANSWER:", bg=c["bg"], fg=c["green"],
                 font=("Helvetica", 8, "bold")).pack(anchor="w", padx=8, pady=(6, 0))

        self.answer_txt = scrolledtext.ScrolledText(
            root,
            bg=c["panel"], fg=c["text"],
            font=("Helvetica", self.cfg["font_size"]),
            bd=0, padx=8, pady=6, wrap="word",
            state="disabled", relief="flat",
        )
        self.answer_txt.pack(fill="both", expand=True, padx=4, pady=(0, 2))

        # ── Controls ──
        ctrl = tk.Frame(root, bg=c["bg"], pady=5)
        ctrl.pack(fill="x", padx=4, pady=(0, 5))

        self.listen_btn = tk.Button(
            ctrl, text="▶  Start Listening",
            bg=c["green"], fg=c["btn_fg"],
            font=("Helvetica", 10, "bold"),
            bd=0, padx=14, pady=6, cursor="hand2",
            activebackground=c["green"],
            command=self._toggle_listen,
        )
        self.listen_btn.pack(side="left", padx=(0, 6))

        tk.Button(ctrl, text="✎  Type Question",
                  bg=c["panel"], fg=c["text"],
                  font=("Helvetica", 10),
                  bd=1, padx=12, pady=6, cursor="hand2",
                  relief="flat",
                  command=self._type_question).pack(side="left", padx=4)

        tk.Button(ctrl, text="🗑",
                  bg=c["panel"], fg=c["dim"],
                  font=("Helvetica", 10),
                  bd=0, padx=8, pady=6, cursor="hand2",
                  command=self._clear).pack(side="right")

        tk.Button(ctrl, text="⚙",
                  bg=c["panel"], fg=c["dim"],
                  font=("Helvetica", 10),
                  bd=0, padx=8, pady=6, cursor="hand2",
                  command=self._settings).pack(side="right", padx=4)

    # ── Drag support ──────────────────────────────────────────
    def _drag_start(self, e):
        self._drag_x, self._drag_y = e.x, e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ── Listening toggle ──────────────────────────────────────
    def _toggle_listen(self):
        if not self._listening:
            self._listening = True
            self.listen_btn.config(text="⏹  Stop Listening", bg=self.c["red"])
            self._set_status("🎤  Listening…", "green")
            self.listener.start()
            self.ai_worker.start()
            self._poll()
        else:
            self._listening = False
            self.listen_btn.config(text="▶  Start Listening", bg=self.c["green"])
            self._set_status("Paused — press any key to listen again", "yellow")
            self.listener.stop()
            self.ai_worker.stop()

    # ── Manual input ──────────────────────────────────────────
    def _type_question(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Type Interview Question")
        dlg.geometry("440x110")
        dlg.configure(bg=self.c["bg"])
        dlg.wm_attributes("-topmost", True)
        dlg.grab_set()

        tk.Label(dlg, text="Paste or type what the interviewer just said:",
                 bg=self.c["bg"], fg=self.c["text"],
                 font=("Helvetica", 10)).pack(padx=12, pady=(12, 4), anchor="w")

        entry = tk.Entry(dlg, bg=self.c["panel"], fg=self.c["text"],
                          font=("Helvetica", 11), bd=1, relief="solid",
                          insertbackground=self.c["text"])
        entry.pack(fill="x", padx=12)
        entry.focus_set()

        def submit(_=None):
            txt = entry.get().strip()
            dlg.destroy()
            if txt:
                self._handle_manual(txt)

        entry.bind("<Return>", submit)
        tk.Button(dlg, text="Get Answer  ↵",
                  bg=self.c["green"], fg=self.c["btn_fg"],
                  font=("Helvetica", 10, "bold"),
                  bd=0, padx=14, pady=4, cursor="hand2",
                  command=submit).pack(pady=8)

    def _handle_manual(self, text: str):
        self._set_heard(text)
        self._set_status("🤔  Thinking…", "yellow")
        threading.Thread(target=self._run_manual_ai, args=(text,), daemon=True).start()

    def _run_manual_ai(self, text: str):
        self.response_q.put(("stream_clear", None))
        self.root.after(0, self._drain_once)

        def on_chunk(chunk):
            self.response_q.put(("chunk", chunk))
            self.root.after(0, self._drain_once)

        get_ai_response(text, self.cfg, on_chunk=on_chunk)
        self.response_q.put(("stream_done", None))
        self.root.after(0, self._drain_once)

    # ── Queue polling ─────────────────────────────────────────
    def _poll(self):
        self._drain_once()
        if self._listening:
            self.root.after(50, self._poll)

    def _drain_once(self):
        try:
            while True:
                kind, payload = self.response_q.get_nowait()
                if kind == "stream_start":
                    self._set_heard(payload)
                    self._set_answer("")
                    self._set_status("🤔  Thinking…", "yellow")
                elif kind == "stream_clear":
                    self._set_answer("")
                elif kind == "chunk":
                    self._append_answer(payload)
                elif kind == "not_question":
                    self._set_heard(payload)
                    self._set_status("🎤  Listening…", "green")
                elif kind == "stream_done":
                    self._pause_after_answer()
                elif kind == "status" and payload == "thinking":
                    self._set_status("🤔  Thinking…", "yellow")
                elif kind == "error":
                    self._set_answer(f"⚠  {payload}")
                    self._set_status("Error — see answer panel", "red")
        except queue.Empty:
            pass

    # ── UI helpers ────────────────────────────────────────────
    def _set_status(self, text: str, color: str = "dim"):
        fg = {"green": self.c["green"], "yellow": self.c["yellow"],
              "red": self.c["red"], "dim": self.c["dim"]}.get(color, self.c["dim"])
        self.dot.config(fg=fg)
        self.status_lbl.config(text=text, fg=fg)

    def _set_heard(self, text: str):
        self.heard_txt.config(state="normal")
        self.heard_txt.delete("1.0", "end")
        self.heard_txt.insert("end", text)
        self.heard_txt.config(state="disabled")

    def _set_answer(self, text: str):
        self.answer_txt.config(state="normal")
        self.answer_txt.delete("1.0", "end")
        self.answer_txt.insert("end", text)
        self.answer_txt.config(state="disabled")

    def _append_answer(self, text: str):
        self.answer_txt.config(state="normal")
        self.answer_txt.insert("end", text)
        self.answer_txt.see("end")
        self.answer_txt.config(state="disabled")

    def _clear(self):
        self._set_heard("")
        self._set_answer("")
        self._set_status("Ready — press Start or type a question", "dim")

    # ── Settings dialog ───────────────────────────────────────
    def _settings(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Settings")
        dlg.geometry("380x260")
        dlg.configure(bg=self.c["bg"])
        dlg.wm_attributes("-topmost", True)
        dlg.grab_set()

        fields = [
            ("Role",       "role",       self.cfg.get("role", "")),
            ("Model",      "model",      self.cfg.get("model", "")),
            ("Language",   "language",   self.cfg.get("language", "")),
            ("API Key",    "api_key",    self.cfg.get("api_key", "")),
        ]
        entries = {}
        for row, (label, key, value) in enumerate(fields):
            tk.Label(dlg, text=label + ":", bg=self.c["bg"], fg=self.c["text"],
                     font=("Helvetica", 10), width=10, anchor="e").grid(
                row=row, column=0, padx=(12, 6), pady=6, sticky="e")
            e = tk.Entry(dlg, bg=self.c["panel"], fg=self.c["text"],
                          font=("Helvetica", 10), bd=1, relief="solid",
                          insertbackground=self.c["text"],
                          show="*" if key == "api_key" else "")
            e.insert(0, value)
            e.grid(row=row, column=1, padx=(0, 12), pady=6, sticky="ew")
            entries[key] = e

        dlg.columnconfigure(1, weight=1)

        def save():
            for key, entry in entries.items():
                self.cfg[key] = entry.get().strip()
            # Update role display
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and "[ " in str(child.cget("text")):
                            child.config(text=f"[ {self.cfg['role']} ]")
            dlg.destroy()

        tk.Button(dlg, text="Save", bg=self.c["green"], fg=self.c["btn_fg"],
                  font=("Helvetica", 10, "bold"), bd=0, padx=20, pady=5,
                  cursor="hand2", command=save).grid(
            row=len(fields), column=0, columnspan=2, pady=12)

    # ── Stop mic after answer; keyboard resumes ───────────────
    def _pause_after_answer(self):
        self._listening = False
        self.listener.stop()
        self.ai_worker.stop()
        self.listen_btn.config(text="▶  Start Listening", bg=self.c["green"])
        self._set_status("✅  Answer ready — press any key to listen again", "green")

    # ── Global keyboard toggle + 8s kill switch ───────────────
    def _start_keyboard_listener(self):
        if not _HAS_PYNPUT:
            return

        _held = set()
        _hold_timer = [None]    # list so the nested functions can rebind it

        def _key_id(key):
            try:
                return key.char or str(key)
            except AttributeError:
                return str(key)

        def _fire_shutdown():
            self.root.after(0, self._shutdown_all)

        def _on_press(key):
            kid = _key_id(key)
            if kid in _held:
                return              # key-repeat — ignore
            _held.add(kid)
            # Start the 8-second kill-switch timer
            t = threading.Timer(8.0, _fire_shutdown)
            t.daemon = True
            t.start()
            _hold_timer[0] = t
            self.root.after(0, self._keyboard_toggle)

        def _on_release(key):
            _held.discard(_key_id(key))
            if _hold_timer[0]:
                _hold_timer[0].cancel()
                _hold_timer[0] = None

        self._kb_listener = _kb.Listener(
            on_press=_on_press, on_release=_on_release, daemon=True
        )
        self._kb_listener.start()

    def _shutdown_all(self):
        """Kill switch: stop docker services, launcher, and this window."""
        self._set_status("Shutting down everything…", "red")
        self.root.update()

        # 1. Stop docker compose (takes down ports 4002 + 4001)
        try:
            subprocess.Popen(
                ["docker", "compose", "stop"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

        # 2. Signal launcher to exit (takes down port 4004)
        try:
            launcher_port = os.getenv("LAUNCHER_PORT", "4004")
            req = urllib.request.Request(
                f"http://localhost:{launcher_port}/shutdown",
                data=b"",
                method="POST",
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass

        # 3. Close this window
        self._quit()

    def _keyboard_toggle(self):
        # Don't toggle while a dialog (Toplevel) is open — user may be typing
        for w in self.root.winfo_children():
            if isinstance(w, tk.Toplevel) and w.winfo_exists():
                return
        self._set_heard("")
        self._set_answer("")
        self._toggle_listen()

    # ── Lifecycle ─────────────────────────────────────────────
    def _quit(self):
        if self._kb_listener:
            self._kb_listener.stop()
        self.listener.stop()
        self.ai_worker.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ─── Entry point ──────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  🎯  Interview Copilot — starting up")
    print("=" * 55)

    job = load_job_config()
    if job and job.get("role"):
        print(f"\n  ✓ Job loaded:  {job.get('role')}", end="")
        if job.get("company"):
            print(f"  at  {job.get('company')}", end="")
        if job.get("location"):
            print(f"  ({job.get('location')})", end="")
        print()
        CONFIG["role"] = job["role"]
    else:
        print("\n  ℹ  No job configured. Run job_setup.py to set your target role.")

    if not CONFIG["api_key"]:
        print("\n⚠   ANTHROPIC_API_KEY is not set.")
        print("    You can still use 'Type Question' mode.")
        print("    Set it with:  export ANTHROPIC_API_KEY=sk-ant-...\n")

    try:
        import speech_recognition as _sr_check; del _sr_check
    except ImportError:
        print("⚠   speech_recognition not found — voice mode disabled.")
        print("    Run:  pip install SpeechRecognition pyaudio\n")

    app = CopilotOverlay(CONFIG)
    app.run()


if __name__ == "__main__":
    main()
