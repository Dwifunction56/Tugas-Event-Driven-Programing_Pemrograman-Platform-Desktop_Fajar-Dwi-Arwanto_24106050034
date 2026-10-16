"""
Quiz Interaktif - Tugas Akhir Event Driven Fajar Dwi Arwanto (24106050034)
=============================
Fitur wajib:
  1. Multiple choice dengan Radiobutton
  2. Timer countdown per soal (bar + angka)
  3. Real-time skor + progress bar (kemajuan quiz & skor)
  4. Validasi jawaban sebelum lanjut
  5. Animasi feedback benar/salah (fade, pulse, shake)
  6. Keyboard shortcut: Enter = submit/lanjut, Esc = skip,
     1-4 / A-D = pilih jawaban, panah atas/bawah = pindah pilihan
  7. State management: progress disimpan ke quiz_progress.json

Fitur variasi tambahan:
  - Efek hover pada opsi (event <Enter> / <Leave>)
  - Confetti (Canvas) di layar hasil jika nilai >= 70%
  - High score (5 besar) tersimpan ke quiz_data.json
  - Tema gelap/terang (tombol di pojok atau tekan T), pilihan tema tersimpan
"""

import json
import math
import os
import random
import time
import tkinter as tk
from tkinter import messagebox, ttk

# ----------------------------------------------------------------- konstanta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROGRESS_FILE = os.path.join(BASE_DIR, "quiz_progress.json")
DATA_FILE = os.path.join(BASE_DIR, "quiz_data.json")   # tema + high score
TIME_PER_QUESTION = 30      # detik
POINTS_CORRECT = 10         # poin dasar jawaban benar
MAX_TIME_BONUS = 5          # bonus kecepatan maksimum
MAX_HIGHSCORES = 5
CONFETTI_THRESHOLD = 70     # persen benar minimum untuk confetti
BTN_FG = "#fefefe"          # teks tombol (sengaja bukan #ffffff agar tidak ikut
                            # terkonversi saat ganti tema)

# ------------------------------------------------------------------- tema
THEMES = {
    "light": dict(BG="#f4f6fb", CARD="#ffffff", TEXT="#1f2a44",
                  MUTED="#6b7490", PRIMARY="#4a6cf7", BORDER="#dfe3ee",
                  GOOD="#2e9e5b", GOOD_BG="#d4f5dd", BAD="#d64545",
                  BAD_BG="#fbd9d9", WARN="#e08a00"),
    "dark": dict(BG="#14182a", CARD="#1f2540", TEXT="#e8ecff",
                 MUTED="#9aa3c7", PRIMARY="#6d8bff", BORDER="#323a5e",
                 GOOD="#4cc983", GOOD_BG="#1d4a35", BAD="#ff6b6b",
                 BAD_BG="#58252b", WARN="#f5a623"),
}
THEME_KEYS = list(THEMES["light"].keys())
COLOR_OPTIONS = ("bg", "fg", "activebackground", "activeforeground",
                 "highlightbackground", "highlightcolor", "selectcolor",
                 "disabledforeground", "troughcolor")

# nilai awal (diganti oleh set_theme saat tema berubah)
globals().update(THEMES["light"])


def set_theme(name):
    """Perbarui konstanta warna global sesuai nama tema."""
    globals().update(THEMES[name])


def blend(c1, c2, t):
    """Campur dua warna hex (t = 0..1). Dipakai untuk fade & hover."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    mixed = [int(a[i] + (b[i] - a[i]) * t) for i in range(3)]
    return "#%02x%02x%02x" % tuple(mixed)


class QuizApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Quiz Interaktif - Tugas Akhir")
        self.window.geometry("720x700")
        self.window.minsize(680, 660)
        self._ready = False            # shortcut aktif setelah UI selesai dibangun

        # ---------------- Data persisten (tema + high score) ----------------
        self.data = self.load_data()
        self.theme_name = self.data["theme"]
        set_theme(self.theme_name)
        self.window.configure(bg=BG)

        # ---------------- Data quiz (bank soal) ----------------
        self.bank = [
            {
                "question": "Apa itu event-driven programming?",
                "options": ["Program yang berjalan berurutan",
                            "Program yang merespons kejadian",
                            "Program tanpa GUI",
                            "Program berbasis web"],
                "correct": 1,
            },
            {
                "question": "Method Tkinter apa yang memulai event loop utama?",
                "options": ["window.run()", "window.start()",
                            "window.mainloop()", "window.loop()"],
                "correct": 2,
            },
            {
                "question": "Fungsi Tkinter untuk menjadwalkan callback setelah "
                            "jeda tertentu tanpa membekukan GUI adalah...",
                "options": ["after()", "sleep()", "wait()", "delay()"],
                "correct": 0,
            },
            {
                "question": "String event yang benar untuk menangkap tombol "
                            "Enter pada keyboard adalah...",
                "options": ["<Enter>", "<Return>", "<Submit>", "<Key-Enter>"],
                "correct": 1,
            },
            {
                "question": "Variabel Tkinter apa yang cocok untuk menyimpan "
                            "pilihan Radiobutton bertipe angka?",
                "options": ["IntVar", "list Python", "dict Python", "Label"],
                "correct": 0,
            },
            {
                "question": "Layout manager mana yang menempatkan widget "
                            "dalam baris dan kolom?",
                "options": ["pack()", "grid()", "place()", "attach()"],
                "correct": 1,
            },
            {
                "question": "Apa yang dimaksud dengan fungsi callback?",
                "options": ["Fungsi yang selalu dipanggil di awal program",
                            "Fungsi untuk menutup jendela",
                            "Fungsi yang dipanggil ketika suatu event terjadi",
                            "Fungsi untuk menggambar widget"],
                "correct": 2,
            },
            {
                "question": "Mengapa time.sleep() sebaiknya dihindari di "
                            "aplikasi GUI Tkinter?",
                "options": ["Karena membekukan event loop sehingga GUI "
                            "tidak responsif",
                            "Karena tidak tersedia di Python",
                            "Karena membuat program lebih cepat",
                            "Karena hanya bisa dipakai di web"],
                "correct": 0,
            },
            {
                "question": "Method apa yang dipakai untuk mengikat event "
                            "keyboard/mouse ke sebuah widget?",
                "options": ["widget.connect()", "widget.listen()",
                            "widget.bind()", "widget.attach()"],
                "correct": 2,
            },
            {
                "question": "Widget ttk mana yang dipakai untuk menampilkan "
                            "kemajuan suatu proses?",
                "options": ["ttk.Scale", "ttk.Progressbar",
                            "ttk.Spinbox", "ttk.Notebook"],
                "correct": 1,
            },
        ]
        self.total = len(self.bank)

        # ---------------- State management ----------------
        self.quiz = []                 # soal yang sudah diacak
        self.session_order = []        # [[index_bank, permutasi_opsi], ...]
        self.current_question = 0
        self.score = 0
        self.correct_count = 0
        self.time_left = TIME_PER_QUESTION
        self.selected_answer = tk.IntVar(value=-1)
        self.answers = []              # riwayat jawaban
        self.mode = "quiz"             # "quiz" | "result"
        self.locked = False            # True setelah soal dijawab
        self.deadline = 0.0
        self.timer_id = None
        self.next_id = None
        self._after_ids = []
        self.option_widgets = []
        self.hover_index = None        # opsi yang sedang di-hover mouse
        self.new_record = False
        self.last_ts = None            # penanda entri high score run ini

        self._configure_styles()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self._bind_keys()

        if not self._try_resume():
            self.new_session()

        self._build_topbar()
        self.buat_interface()
        self.load_question()

        self._ready = True
        self.window.after(200, self._grab_focus)

    # ================================================================ setup
    def _configure_styles(self):
        style = ttk.Style(self.window)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Progress.Horizontal.TProgressbar",
                        troughcolor=BORDER, background=PRIMARY,
                        bordercolor=BORDER, lightcolor=PRIMARY,
                        darkcolor=PRIMARY, thickness=12)
        style.configure("Score.Horizontal.TProgressbar",
                        troughcolor=BORDER, background=GOOD,
                        bordercolor=BORDER, lightcolor=GOOD,
                        darkcolor=GOOD, thickness=12)
        style.configure("Vertical.TScrollbar", background=BORDER,
                        troughcolor=CARD, bordercolor=CARD,
                        arrowcolor=TEXT)

    def _bind_keys(self):
        # bind_all + satu handler: tetap jalan walau fokus ada di widget anak
        self.window.bind_all("<Key>", self._on_key)

    def _on_key(self, event):
        if not self._ready:
            return
        # abaikan tombol yang ditekan di jendela lain (mis. dialog messagebox)
        try:
            if event.widget.winfo_toplevel() is not self.window:
                return
        except (AttributeError, KeyError, tk.TclError):
            pass

        k = event.keysym
        if k in ("Return", "KP_Enter"):
            self.submit_answer()
        elif k == "Escape":
            self.skip_question()
        elif k == "Up":
            if self.mode == "quiz":
                self._move_selection(-1)
        elif k == "Down":
            if self.mode == "quiz":
                self._move_selection(1)
        elif len(k) == 1 and k.lower() == "t":
            self.toggle_theme()
        elif len(k) == 1 and k in "1234":
            self.select_option(int(k) - 1)
        elif len(k) == 1 and k.lower() in "abcd":
            self.select_option("abcd".index(k.lower()))

    def _grab_focus(self):
        """Pastikan jendela memegang fokus keyboard."""
        try:
            self.window.lift()
            self.window.focus_force()
        except tk.TclError:
            pass

    # ------------------------------------------------ helper animasi / after
    def _after(self, ms, fn):
        aid = self.window.after(ms, fn)
        self._after_ids.append(aid)
        return aid

    def _cancel_afters(self):
        for aid in self._after_ids:
            try:
                self.window.after_cancel(aid)
            except tk.TclError:
                pass
        self._after_ids.clear()
        self.stop_timer()
        if self.next_id:
            try:
                self.window.after_cancel(self.next_id)
            except tk.TclError:
                pass
            self.next_id = None

    # ================================================ data persisten (JSON)
    def load_data(self):
        data = {"theme": "light", "highscores": []}
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                raw = json.load(f)
            if raw.get("theme") in THEMES:
                data["theme"] = raw["theme"]
            keys = ("score", "correct", "total", "date", "ts")
            data["highscores"] = [h for h in raw.get("highscores", [])
                                  if isinstance(h, dict)
                                  and all(k in h for k in keys)][:MAX_HIGHSCORES]
        except (OSError, ValueError, AttributeError):
            pass
        return data

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _record_highscore(self):
        """Masukkan hasil run ini ke daftar 5 besar (jika skor > 0)."""
        self.new_record = False
        self.last_ts = None
        if self.score <= 0:
            return
        scores = self.data["highscores"]
        prev_best = max((h["score"] for h in scores), default=0)
        entry = {"score": self.score, "correct": self.correct_count,
                 "total": self.total, "ts": time.time(),
                 "date": time.strftime("%d/%m/%Y %H:%M")}
        scores.append(entry)
        scores.sort(key=lambda h: (-h["score"], -h["correct"], h["ts"]))
        del scores[MAX_HIGHSCORES:]
        if entry in scores:
            self.last_ts = entry["ts"]
            self.new_record = self.score > prev_best
        self.save_data()

    # ======================================================== state / session
    def _build_item(self, bank_index, perm):
        item = self.bank[bank_index]
        return {
            "question": item["question"],
            "options": [item["options"][p] for p in perm],
            "correct": perm.index(item["correct"]),
        }

    def new_session(self):
        """Mulai quiz baru: acak urutan soal dan opsi."""
        idx = list(range(self.total))
        random.shuffle(idx)
        self.session_order = []
        self.quiz = []
        for i in idx:
            perm = list(range(len(self.bank[i]["options"])))
            random.shuffle(perm)
            self.session_order.append([i, perm])
            self.quiz.append(self._build_item(i, perm))
        self.current_question = 0
        self.score = 0
        self.correct_count = 0
        self.answers = []
        self.mode = "quiz"
        self.locked = False
        self.hover_index = None
        self.new_record = False
        self.last_ts = None
        self.selected_answer.set(-1)

    def save_progress(self):
        """Simpan progress; indeks yang disimpan adalah soal berikutnya."""
        data = {
            "order": self.session_order,
            "current_question": self.current_question + 1,
            "score": self.score,
            "correct_count": self.correct_count,
            "answers": self.answers,
        }
        try:
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass  # gagal menyimpan tidak boleh merusak quiz

    def clear_progress(self):
        try:
            os.remove(PROGRESS_FILE)
        except OSError:
            pass

    def _try_resume(self):
        """Muat progress tersimpan (jika ada dan valid)."""
        if not os.path.exists(PROGRESS_FILE):
            return False
        try:
            with open(PROGRESS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            order = data["order"]
            cur = int(data["current_question"])
            if len(order) != self.total or not (0 < cur < self.total):
                raise ValueError
            quiz = [self._build_item(i, perm) for i, perm in order]
            answers = list(data["answers"])
            score = int(data["score"])
            correct = int(data["correct_count"])
        except (OSError, ValueError, KeyError, TypeError, IndexError):
            self.clear_progress()
            return False

        if not messagebox.askyesno(
                "Lanjutkan Quiz?",
                f"Ditemukan progress tersimpan (soal {cur + 1} dari "
                f"{self.total}, skor {score}).\n\nLanjutkan quiz sebelumnya?"):
            self.clear_progress()
            return False

        self.session_order, self.quiz = order, quiz
        self.current_question, self.answers = cur, answers
        self.score, self.correct_count = score, correct
        return True

    # ============================================================== interface
    def _button(self, parent, text, command, primary=False, width=14):
        return tk.Button(parent, text=text, width=width, command=command,
                         bg=PRIMARY if primary else BORDER,
                         fg=BTN_FG if primary else TEXT,
                         activebackground=PRIMARY if primary else BORDER,
                         activeforeground=BTN_FG if primary else TEXT,
                         relief="flat", cursor="hand2", takefocus=0,
                         font=("Segoe UI", 11, "bold" if primary else "normal"))

    def _build_topbar(self):
        """Bar atas permanen: judul + tombol ganti tema."""
        self.topbar = tk.Frame(self.window, bg=BG)
        self.topbar.pack(fill="x", padx=24, pady=(10, 0))
        tk.Label(self.topbar, text="🧠 Quiz Interaktif", bg=BG, fg=MUTED,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        self.theme_btn = tk.Button(self.topbar, command=self.toggle_theme,
                                   bg=BORDER, fg=TEXT, relief="flat",
                                   activebackground=BORDER, activeforeground=TEXT,
                                   cursor="hand2", takefocus=0,
                                   font=("Segoe UI", 9))
        self.theme_btn.pack(side="right", ipadx=6)
        self._update_theme_btn()

    def _update_theme_btn(self):
        text = "☀ Tema Terang (T)" if self.theme_name == "dark" \
            else "🌙 Tema Gelap (T)"
        self.theme_btn.config(text=text)

    def buat_interface(self):
        self.quiz_frame = tk.Frame(self.window, bg=BG)
        self.quiz_frame.pack(fill="both", expand=True)
        qf = self.quiz_frame

        # ---- Header: nomor soal & skor
        header = tk.Frame(qf, bg=BG)
        header.pack(fill="x", padx=24, pady=(10, 4))
        self.counter_label = tk.Label(header, text="", bg=BG, fg=TEXT,
                                      font=("Segoe UI", 12, "bold"))
        self.counter_label.pack(side="left")
        self.score_label = tk.Label(header, text="", bg=BG, fg=GOOD,
                                    font=("Segoe UI", 12, "bold"))
        self.score_label.pack(side="right")

        # ---- Progress bar kemajuan quiz & skor
        self.progress_var = tk.DoubleVar(value=0)
        self.score_var = tk.DoubleVar(value=0)
        bars = tk.Frame(qf, bg=BG)
        bars.pack(fill="x", padx=24)
        tk.Label(bars, text="Kemajuan", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        ttk.Progressbar(bars, variable=self.progress_var, maximum=100,
                        style="Progress.Horizontal.TProgressbar"
                        ).grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=2)
        tk.Label(bars, text="Skor", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w")
        ttk.Progressbar(bars, variable=self.score_var, maximum=100,
                        style="Score.Horizontal.TProgressbar"
                        ).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=2)
        bars.columnconfigure(1, weight=1)

        # ---- Timer
        timer_box = tk.Frame(qf, bg=BG)
        timer_box.pack(fill="x", padx=24, pady=(10, 0))
        self.timer_label = tk.Label(timer_box, text="", bg=BG, fg=TEXT,
                                    font=("Segoe UI", 11, "bold"))
        self.timer_label.pack(anchor="e")
        self.timer_canvas = tk.Canvas(timer_box, height=12, bg=BORDER,
                                      highlightthickness=0)
        self.timer_canvas.pack(fill="x")
        self.timer_canvas.bind("<Configure>",
                               lambda e: self.draw_timer(self.time_left))

        # ---- Kartu soal
        card = tk.Frame(qf, bg=CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", padx=24, pady=(12, 6))
        self.question_label = tk.Label(card, text="", bg=CARD, fg=TEXT,
                                       font=("Segoe UI", 14, "bold"),
                                       wraplength=620, justify="left",
                                       anchor="w")
        self.question_label.pack(fill="x", padx=18, pady=16)

        # ---- Opsi (Radiobutton) + event hover
        self.options_frame = tk.Frame(qf, bg=BG)
        self.options_frame.pack(fill="x", padx=24)
        self.option_widgets = []
        for i in range(4):
            frame = tk.Frame(self.options_frame, bg=CARD, highlightthickness=2,
                             highlightbackground=BORDER, cursor="hand2")
            frame.pack(fill="x", pady=4)
            rb = tk.Radiobutton(frame, variable=self.selected_answer, value=i,
                                command=self.on_select, bg=CARD,
                                activebackground=CARD, fg=TEXT,
                                selectcolor=CARD, disabledforeground=TEXT,
                                font=("Segoe UI", 12), anchor="w",
                                justify="left", wraplength=580,
                                takefocus=0, cursor="hand2")
            rb.pack(fill="x", padx=10, pady=8)
            frame.bind("<Button-1>", lambda e, n=i: self.select_option(n))
            for widget in (frame, rb):                      # event mouse hover
                widget.bind("<Enter>", lambda e, n=i: self._hover(n))
                widget.bind("<Leave>", lambda e, n=i: self._unhover(n))
            self.option_widgets.append((frame, rb))

        # ---- Feedback
        self.feedback_label = tk.Label(qf, text="", bg=BG, fg=TEXT,
                                       font=("Segoe UI", 13, "bold"))
        self.feedback_label.pack(pady=(10, 4))

        # ---- Tombol
        btns = tk.Frame(qf, bg=BG)
        btns.pack(pady=4)
        self.skip_btn = self._button(btns, "Skip (Esc)", self.skip_question)
        self.skip_btn.pack(side="left", padx=6, ipady=4)
        self.submit_btn = self._button(btns, "Submit (Enter)",
                                       self.submit_answer, primary=True,
                                       width=16)
        self.submit_btn.pack(side="left", padx=6, ipady=4)

        tk.Label(qf, text="Shortcut: 1-4 / A-D pilih jawaban  •  ↑ ↓ pindah  •  "
                          "Enter submit  •  Esc skip  •  T ganti tema",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(pady=(6, 0))

    # =========================================================== load / status
    def update_status(self):
        done = len(self.answers)
        max_points = self.total * (POINTS_CORRECT + MAX_TIME_BONUS)
        self.counter_label.config(
            text=f"Soal {min(self.current_question + 1, self.total)} / {self.total}")
        self.score_label.config(
            text=f"Skor: {self.score}  •  Benar: {self.correct_count}/{done}")
        self.progress_var.set(done / self.total * 100)
        self.score_var.set(self.score / max_points * 100)

    def _set_option_style(self, i, bg, border):
        frame, rb = self.option_widgets[i]
        frame.config(bg=bg, highlightbackground=border)
        rb.config(bg=bg, activebackground=bg, selectcolor=bg)

    def _refresh_option(self, i):
        """Tentukan tampilan opsi: terpilih > hover > normal."""
        if self.locked:
            return
        if i == self.selected_answer.get():
            self._set_option_style(i, blend(CARD, PRIMARY, 0.06), PRIMARY)
        elif i == self.hover_index:
            self._set_option_style(i, blend(CARD, PRIMARY, 0.12),
                                   blend(BORDER, PRIMARY, 0.55))
        else:
            self._set_option_style(i, CARD, BORDER)

    def _refresh_all_options(self):
        for i in range(len(self.option_widgets)):
            self._refresh_option(i)

    def _hover(self, i):
        """Event <Enter>: mouse masuk ke opsi."""
        if self.mode != "quiz" or self.locked:
            return
        self.hover_index = i
        self._refresh_all_options()

    def _unhover(self, i):
        """Event <Leave>: abaikan jika mouse hanya pindah ke widget anak."""
        if self.mode != "quiz":
            return
        x, y = self.window.winfo_pointerxy()
        under = self.window.winfo_containing(x, y)
        if under in self.option_widgets[i]:
            return
        if self.hover_index == i:
            self.hover_index = None
        self._refresh_all_options()

    def on_select(self):
        """Dipanggil saat radiobutton berubah: beri highlight pilihan."""
        if self.locked:
            return
        self._refresh_all_options()
        self.feedback_label.config(text="")

    def select_option(self, i):
        if self.mode != "quiz" or self.locked:
            return
        self.selected_answer.set(i)
        self.on_select()

    def _move_selection(self, step):
        cur = self.selected_answer.get()
        n = len(self.option_widgets)
        self.select_option(0 if cur == -1 else (cur + step) % n)

    def load_question(self):
        self.locked = False
        self.mode = "quiz"
        self.hover_index = None
        q = self.quiz[self.current_question]
        self.selected_answer.set(-1)
        self.question_label.config(
            text=f"{self.current_question + 1}. {q['question']}")
        for i, (frame, rb) in enumerate(self.option_widgets):
            rb.config(text=f"{chr(65 + i)}.  {q['options'][i]}", state="normal")
        self._refresh_all_options()
        self.feedback_label.config(text="")
        self.submit_btn.config(text="Submit (Enter)", state="normal")
        self.skip_btn.config(state="normal")
        self.update_status()
        self.start_timer()

    # ================================================================== timer
    def start_timer(self):
        self.stop_timer()
        self.time_left = TIME_PER_QUESTION
        self.deadline = time.time() + TIME_PER_QUESTION
        self.draw_timer(self.time_left)
        self._tick()

    def stop_timer(self):
        if self.timer_id:
            try:
                self.window.after_cancel(self.timer_id)
            except tk.TclError:
                pass
            self.timer_id = None

    def _tick(self):
        if self.mode != "quiz" or self.locked:
            return
        remaining = self.deadline - time.time()
        if remaining <= 0:
            self.time_left = 0
            self.draw_timer(0)
            self.timer_id = None
            self._resolve(None, "timeout")
            return
        self.time_left = remaining
        self.draw_timer(remaining)
        self.timer_id = self.window.after(100, self._tick)

    def draw_timer(self, remaining):
        c = self.timer_canvas
        ratio = max(0.0, min(1.0, remaining / TIME_PER_QUESTION))
        color = GOOD if ratio > 0.5 else (WARN if ratio > 0.2 else BAD)
        width = max(c.winfo_width(), 1)
        c.delete("all")
        c.create_rectangle(0, 0, width * ratio, 14, fill=color, width=0)
        self.timer_label.config(text=f"⏱ {math.ceil(remaining)} detik", fg=color)

    # ============================================================== animasi
    def fade_feedback(self, text, color, steps=8):
        self.feedback_label.config(text=text, fg=BG)

        def step(n):
            self.feedback_label.config(fg=blend(BG, color, n / steps))
            if n < steps:
                self._after(30, lambda: step(n + 1))
        step(1)

    def pulse_option(self, i, bg, border, times=3):
        def step(n):
            if n % 2 == 0:
                self._set_option_style(i, bg, border)
            else:
                self._set_option_style(i, CARD, border)
            if n < times * 2:
                self._after(120, lambda: step(n + 1))
            else:
                self._set_option_style(i, bg, border)
        step(0)

    def shake(self, widget, base=24):
        offsets = [12, -12, 9, -9, 6, -6, 3, -3, 0]

        def step(n):
            off = offsets[n]
            widget.pack_configure(padx=(base + off, base - off))
            if n < len(offsets) - 1:
                self._after(35, lambda: step(n + 1))
        step(0)

    def _start_confetti(self, canvas, width, height, duration=4.5):
        """Confetti: potongan warna jatuh dengan goyangan sinus di Canvas."""
        colors = [PRIMARY, GOOD, WARN, BAD, "#b84cf7", "#f7c948"]
        parts = []
        for _ in range(90):
            p = {"x": random.uniform(0, width),
                 "y": random.uniform(-height, 0),
                 "vy": random.uniform(2.0, 5.0),
                 "vx": random.uniform(-1.0, 1.0),
                 "size": random.randint(4, 8),
                 "phase": random.uniform(0, 6.28),
                 "done": False}
            color = random.choice(colors)
            make = canvas.create_rectangle if random.random() < 0.5 \
                else canvas.create_oval
            p["id"] = make(0, 0, 0, 0, fill=color, width=0)
            parts.append(p)
        start = time.time()

        def step():
            if not canvas.winfo_exists():
                return
            elapsed = time.time() - start
            alive = False
            for p in parts:
                if p["done"]:
                    continue
                p["y"] += p["vy"]
                p["phase"] += 0.15
                p["x"] += p["vx"] + math.sin(p["phase"]) * 1.2
                if p["y"] > height + 10:
                    if elapsed < duration:          # daur ulang dari atas
                        p["y"] = random.uniform(-40, -5)
                        p["x"] = random.uniform(0, width)
                    else:
                        canvas.itemconfigure(p["id"], state="hidden")
                        p["done"] = True
                        continue
                alive = True
                s = p["size"]
                canvas.coords(p["id"], p["x"] - s, p["y"] - s * 0.6,
                              p["x"] + s, p["y"] + s * 0.6)
            if alive:
                self._after(33, step)
        step()

    # ================================================================== tema
    def _recolor(self, widget, mapping):
        """Ganti warna lama -> baru pada widget dan seluruh anaknya."""
        for opt in COLOR_OPTIONS:
            try:
                cur = str(widget.cget(opt)).lower()
            except tk.TclError:
                continue
            if cur in mapping:
                try:
                    widget.configure(**{opt: mapping[cur]})
                except tk.TclError:
                    pass
        for child in widget.winfo_children():
            self._recolor(child, mapping)

    def toggle_theme(self, event=None):
        old = THEMES[self.theme_name]
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        new = THEMES[self.theme_name]
        mapping = {old[k].lower(): new[k] for k in THEME_KEYS}
        set_theme(self.theme_name)

        self._recolor(self.window, mapping)
        self._configure_styles()
        self._update_theme_btn()

        if self.mode == "result":
            self._cancel_afters()
            self.quiz_frame.destroy()
            self._render_result(confetti=False)
        else:
            self.draw_timer(self.time_left)
            self._refresh_all_options()

        self.data["theme"] = self.theme_name
        self.save_data()

    # ====================================================== validasi & submit
    def submit_answer(self, event=None):
        """Enter / tombol Submit. Jika soal sudah dijawab -> lanjut."""
        if self.mode == "result":
            self.restart()
            return
        if self.locked:                       # sudah dinilai -> langsung lanjut
            self.go_next()
            return
        sel = self.selected_answer.get()
        if sel == -1:                         # VALIDASI: harus memilih dulu
            self.fade_feedback("⚠ Pilih salah satu jawaban terlebih dahulu!", WARN)
            self.shake(self.options_frame)
            return
        self._resolve(sel, "answered")

    def skip_question(self, event=None):
        if self.mode != "quiz" or self.locked:
            return
        self._resolve(None, "skipped")

    def _resolve(self, sel, status):
        """Nilai jawaban, jalankan animasi, simpan state."""
        if self.locked:
            return
        self.locked = True
        self.hover_index = None
        self.stop_timer()
        q = self.quiz[self.current_question]
        correct = q["correct"]
        points = 0

        if sel is not None and sel == correct:
            status = "correct"
            bonus = min(MAX_TIME_BONUS,
                        int(self.time_left // (TIME_PER_QUESTION / (MAX_TIME_BONUS + 1))))
            points = POINTS_CORRECT + bonus
            self.score += points
            self.correct_count += 1
        elif sel is not None:
            status = "wrong"

        # Kunci input
        for _, rb in self.option_widgets:
            rb.config(state="disabled")
        self.skip_btn.config(state="disabled")
        last = self.current_question + 1 >= self.total
        self.submit_btn.config(text="Lihat Hasil ▶" if last else "Lanjut ▶ (Enter)")

        # Feedback visual
        for i in range(len(self.option_widgets)):      # hapus sisa highlight
            self._set_option_style(i, CARD, BORDER)
        if status == "correct":
            self.pulse_option(correct, GOOD_BG, GOOD)
            self.fade_feedback(f"✓ Benar!  +{points} poin", GOOD)
        elif status == "wrong":
            self._set_option_style(sel, BAD_BG, BAD)
            self.pulse_option(correct, GOOD_BG, GOOD)
            self.shake(self.options_frame)
            self.fade_feedback("✗ Salah! Jawaban benar ditandai hijau.", BAD)
        elif status == "timeout":
            self.pulse_option(correct, GOOD_BG, GOOD)
            self.shake(self.options_frame)
            self.fade_feedback("⏰ Waktu habis!", BAD)
        else:  # skipped
            self.pulse_option(correct, GOOD_BG, GOOD)
            self.fade_feedback("⏭ Soal dilewati.", MUTED)

        self.answers.append({
            "question": q["question"],
            "chosen": None if sel is None else q["options"][sel],
            "correct": q["options"][correct],
            "status": status,
            "points": points,
        })
        self.update_status()
        self.save_progress()

        delay = 1800 if status in ("correct", "wrong") else 1400
        self.next_id = self.window.after(delay, self.go_next)

    def go_next(self):
        if self.mode != "quiz" or not self.locked:
            return
        if self.next_id:
            try:
                self.window.after_cancel(self.next_id)
            except tk.TclError:
                pass
            self.next_id = None
        self.current_question += 1
        if self.current_question >= self.total:
            self.show_result()
        else:
            self.load_question()

    # ================================================================== hasil
    def show_result(self):
        self._cancel_afters()
        self.mode = "result"
        self.clear_progress()
        self.quiz_frame.destroy()
        self._record_highscore()
        self._render_result(confetti=True)

    def _render_result(self, confetti):
        rf = tk.Frame(self.window, bg=BG)
        rf.pack(fill="both", expand=True)
        self.quiz_frame = rf

        percent = self.correct_count / self.total * 100
        if percent >= 90:
            grade, color = "Luar Biasa! 🏆", GOOD
        elif percent >= 70:
            grade, color = "Bagus! 👍", PRIMARY
        elif percent >= 50:
            grade, color = "Cukup 🙂", WARN
        else:
            grade, color = "Perlu belajar lagi 📚", BAD

        # ---- Banner (Canvas): teks hasil + confetti
        banner_h = 150
        banner = tk.Canvas(rf, height=banner_h, bg=BG, highlightthickness=0)
        banner.pack(fill="x")
        self.window.update_idletasks()
        width = max(banner.winfo_width(), 700)
        if confetti and percent >= CONFETTI_THRESHOLD:
            self._start_confetti(banner, width, banner_h)

        t_title = banner.create_text(width / 2, 30, text="Hasil Quiz", fill=TEXT,
                                     font=("Segoe UI", 20, "bold"))
        t_grade = banner.create_text(width / 2, 66, text=grade, fill=color,
                                     font=("Segoe UI", 16, "bold"))
        t_sum = banner.create_text(
            width / 2, 100,
            text=f"Skor: {self.score}   •   Benar: {self.correct_count}/"
                 f"{self.total} ({percent:.0f}%)",
            fill=TEXT, font=("Segoe UI", 12))
        t_rec = banner.create_text(
            width / 2, 128, fill=WARN, font=("Segoe UI", 11, "bold"),
            text="🎉 Rekor baru!" if self.new_record else "")

        def recenter(event):
            for t in (t_title, t_grade, t_sum, t_rec):
                x, y = banner.coords(t)
                banner.coords(t, event.width / 2, y)
        banner.bind("<Configure>", recenter)

        # ---- Isi: review (kiri) + high score (kanan)
        body = tk.Frame(rf, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 6))

        hs = tk.Frame(body, bg=CARD, highlightthickness=1,
                      highlightbackground=BORDER, width=210)
        hs.pack(side="right", fill="y", padx=(10, 0))
        hs.pack_propagate(False)
        tk.Label(hs, text="🏆 Skor Tertinggi", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(pady=(10, 6))
        scores = self.data["highscores"]
        if not scores:
            tk.Label(hs, text="Belum ada data.", bg=CARD, fg=MUTED,
                     font=("Segoe UI", 10)).pack()
        for rank, h in enumerate(scores, 1):
            mine = self.last_ts is not None and h["ts"] == self.last_ts
            row = tk.Frame(hs, bg=CARD)
            row.pack(fill="x", padx=10, pady=3)
            tk.Label(row, bg=CARD, fg=GOOD if mine else TEXT, anchor="w",
                     justify="left",
                     font=("Segoe UI", 10, "bold" if mine else "normal"),
                     text=f"{rank}. {h['score']} poin "
                          f"({h['correct']}/{h['total']})"
                          f"{'  ◀ kamu' if mine else ''}").pack(fill="x")
            tk.Label(row, text=h["date"], bg=CARD, fg=MUTED, anchor="w",
                     font=("Segoe UI", 8)).pack(fill="x")
        if self.last_ts is None:
            tk.Label(hs, bg=CARD, fg=MUTED, wraplength=180, justify="left",
                     font=("Segoe UI", 9),
                     text=f"Skor kamu ({self.score}) belum masuk "
                          f"{MAX_HIGHSCORES} besar." if self.score > 0
                     else "Skor 0 tidak dicatat.").pack(padx=10, pady=(8, 0))

        box = tk.Frame(body, bg=CARD, highlightthickness=1,
                       highlightbackground=BORDER)
        box.pack(side="left", fill="both", expand=True)
        text = tk.Text(box, wrap="word", bg=CARD, fg=TEXT, relief="flat",
                       font=("Segoe UI", 10), padx=12, pady=8,
                       highlightthickness=0, takefocus=0)
        scroll = ttk.Scrollbar(box, command=text.yview)
        text.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.tag_config("title", font=("Segoe UI", 10, "bold"))
        text.tag_config("correct", foreground=GOOD)
        text.tag_config("wrong", foreground=BAD)
        text.tag_config("muted", foreground=MUTED)

        labels = {"correct": ("✓ Benar", "correct"),
                  "wrong": ("✗ Salah", "wrong"),
                  "timeout": ("⏰ Waktu habis", "wrong"),
                  "skipped": ("⏭ Dilewati", "muted")}
        for n, a in enumerate(self.answers, 1):
            label, tag = labels.get(a["status"], ("", "muted"))
            text.insert("end", f"{n}. {a['question']}\n", "title")
            text.insert("end", f"   {label}", tag)
            if a["status"] == "correct":
                text.insert("end", f"  (+{a['points']} poin)\n\n", "muted")
            else:
                if a["chosen"]:
                    text.insert("end", f"  — jawabanmu: {a['chosen']}", "muted")
                text.insert("end", f"\n   Jawaban benar: {a['correct']}\n\n", "muted")
        text.config(state="disabled")

        btns = tk.Frame(rf, bg=BG)
        btns.pack(pady=(4, 14))
        self._button(btns, "Ulangi Quiz (Enter)", self.restart, primary=True,
                     width=20).pack(side="left", padx=6, ipady=4)
        self._button(btns, "Keluar", self.window.destroy,
                     width=12).pack(side="left", padx=6, ipady=4)
        self.window.after(50, self._grab_focus)

    def restart(self):
        self._cancel_afters()
        self.quiz_frame.destroy()
        self.new_session()
        self.buat_interface()
        self.load_question()
        self.window.after(50, self._grab_focus)

    # ================================================================ lainnya
    def on_close(self):
        if self.mode == "quiz" and self.answers:
            if not messagebox.askokcancel(
                    "Keluar", "Keluar dari quiz?\nProgress kamu sudah tersimpan "
                              "dan bisa dilanjutkan nanti."):
                return
        self._cancel_afters()
        self.window.destroy()

    def jalankan(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = QuizApp()
    app.jalankan()t