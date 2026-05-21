import customtkinter as ctk
from tkinter import messagebox
import sqlite3
from datetime import datetime, date, timedelta
from tkcalendar import DateEntry

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class FinPulse(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FinPulse — Учёт финансов")
        self.geometry("980x720")
        self.resizable(True, True)
        self.configure(fg_color="#f0f4f8")

        # Полноэкранный режим
        self.bind("<F11>", lambda e: self.attributes("-fullscreen", True))
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        self.db_init()
        self.current_filter = "all"
        self.budget_mode = "month"
        self.budget_limit_week = 5000
        self.budget_limit_month = 20000

        self.setup_ui()
        self.refresh_data()

    def db_init(self):
        self.conn = sqlite3.connect("finpulse.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                streak INTEGER DEFAULT 0,
                done_today INTEGER DEFAULT 0
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        for key, default in [("budget_week", "5000"), ("budget_month", "20000")]:
            self.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            if not self.cursor.fetchone():
                self.cursor.execute("INSERT INTO settings VALUES (?,?)", (key, default))

        self.cursor.execute("SELECT COUNT(*) FROM goals")
        if self.cursor.fetchone()[0] == 0:
            for g in [("Откладывать 10% дохода", 0, 0), ("Вести учёт всех трат", 0, 0)]:
                self.cursor.execute("INSERT INTO goals (text,streak,done_today) VALUES (?,?,?)", g)

        self.conn.commit()

        row = self.cursor.execute("SELECT value FROM settings WHERE key='budget_week'").fetchone()
        self.budget_limit_week = int(row[0])
        row = self.cursor.execute("SELECT value FROM settings WHERE key='budget_month'").fetchone()
        self.budget_limit_month = int(row[0])

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # === ВЕРХ ===
        top = ctk.CTkFrame(self, height=65, corner_radius=0, fg_color="#ffffff")
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)

        ctk.CTkLabel(top, text="FinPulse",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#1e40af").pack(side="left", padx=20, pady=12)

        self.lbl_balance = ctk.CTkLabel(top, text="Баланс: 0 ₽",
                                         font=ctk.CTkFont(size=18, weight="bold"),
                                         text_color="#1e293b")
        self.lbl_balance.pack(side="left", padx=30, pady=12)

        ctk.CTkLabel(top, text=date.today().strftime("%d.%m.%Y"),
                     font=ctk.CTkFont(size=13),
                     text_color="#64748b").pack(side="right", padx=20)

        # === ОСНОВНОЕ ===
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)

        # -- ЛЕВО --
        left = ctk.CTkFrame(main, fg_color="#ffffff", corner_radius=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        lhead = ctk.CTkFrame(left, fg_color="transparent")
        lhead.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 6))
        ctk.CTkLabel(lhead, text="История операций",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#1e293b").pack(side="left")

        fframe = ctk.CTkFrame(lhead, fg_color="transparent")
        fframe.pack(side="right")
        for lbl, fid, i in [("Все", "all", 0), ("Доходы", "income", 1), ("Расходы", "expense", 2)]:
            b = ctk.CTkButton(fframe, text=lbl, width=70 if i > 0 else 55, height=28,
                              fg_color="#3b82f6" if i == 0 else "transparent",
                              text_color="white" if i == 0 else "#3b82f6",
                              border_width=0 if i == 0 else 1, border_color="#3b82f6",
                              font=ctk.CTkFont(size=10, weight="bold"), corner_radius=8,
                              command=lambda f=fid: self.set_filter(f))
            b.pack(side="left", padx=2)
            setattr(self, f"btn_f_{fid}", b)

        self.tx_list = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                               scrollbar_button_color="#cbd5e1",
                                               scrollbar_button_hover_color="#94a3b8")
        self.tx_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)

        # -- ПРАВО --
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.grid_rowconfigure(0, weight=0)
        right.grid_rowconfigure(1, weight=0)
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # ФОРМА
        form = ctk.CTkFrame(right, fg_color="#ffffff", corner_radius=16)
        form.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(form, text="Новая операция",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#1e293b").pack(pady=(14, 8))

        self.type_var = ctk.StringVar(value="expense")
        tframe = ctk.CTkFrame(form, fg_color="transparent")
        tframe.pack(pady=6)
        self.btn_exp = ctk.CTkButton(tframe, text="Расход", width=110, height=34,
                                     fg_color="#ef4444", text_color="white",
                                     font=ctk.CTkFont(weight="bold"), corner_radius=10,
                                     command=lambda: self.set_type("expense"))
        self.btn_exp.pack(side="left", padx=5)
        self.btn_inc = ctk.CTkButton(tframe, text="Доход", width=110, height=34,
                                     fg_color="transparent", text_color="#22c55e",
                                     border_width=2, border_color="#22c55e",
                                     font=ctk.CTkFont(weight="bold"), corner_radius=10,
                                     command=lambda: self.set_type("income"))
        self.btn_inc.pack(side="left", padx=5)

        self.entry_desc = ctk.CTkEntry(form, placeholder_text="Описание...", height=36,
                                       fg_color="#f8fafc", border_color="#e2e8f0",
                                       text_color="#1e293b")
        self.entry_desc.pack(padx=20, pady=(10, 5), fill="x")
        self.entry_amount = ctk.CTkEntry(form, placeholder_text="Сумма...", height=36,
                                         fg_color="#f8fafc", border_color="#e2e8f0",
                                         text_color="#1e293b")
        self.entry_amount.pack(padx=20, pady=5, fill="x")

        rframe = ctk.CTkFrame(form, fg_color="transparent")
        rframe.pack(padx=20, pady=6, fill="x")
        self.combo_cat = ctk.CTkComboBox(rframe,
                                         values=["Еда", "Транспорт", "Жильё",
                                                 "Развлечения", "Здоровье", "Работа", "Другое"],
                                         width=140, height=32, fg_color="#f8fafc",
                                         border_color="#e2e8f0", button_color="#3b82f6",
                                         text_color="#1e293b")
        self.combo_cat.pack(side="left")
        self.cal = DateEntry(rframe, width=12, background='white', foreground='#1e293b',
                             borderwidth=1, date_pattern='dd.mm.yyyy')
        self.cal.pack(side="right")

        ctk.CTkButton(form, text="Добавить", font=ctk.CTkFont(weight="bold", size=13),
                      fg_color="#3b82f6", text_color="white", hover_color="#2563eb",
                      height=40, corner_radius=10,
                      command=self.add_transaction).pack(padx=20, pady=(12, 16), fill="x")

        # БЮДЖЕТ
        bud = ctk.CTkFrame(right, fg_color="#ffffff", corner_radius=16)
        bud.grid(row=1, column=0, sticky="ew", pady=8)
        bhead = ctk.CTkFrame(bud, fg_color="transparent")
        bhead.pack(fill="x", padx=16, pady=(12, 0))
        ctk.CTkLabel(bhead, text="Бюджет",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#1e293b").pack(side="left")
        self.btn_w = ctk.CTkButton(bhead, text="Неделя", width=65, height=26,
                                   fg_color="#e2e8f0", text_color="#64748b",
                                   font=ctk.CTkFont(size=10), corner_radius=6,
                                   command=lambda: self.set_budget_mode("week"))
        self.btn_w.pack(side="right", padx=2)
        self.btn_m = ctk.CTkButton(bhead, text="Месяц", width=65, height=26,
                                   fg_color="#3b82f6", text_color="white",
                                   font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6,
                                   command=lambda: self.set_budget_mode("month"))
        self.btn_m.pack(side="right", padx=2)

        self.lbl_bud = ctk.CTkLabel(bud, text="Потрачено: 0 ₽ из 20 000 ₽",
                                    font=ctk.CTkFont(size=14, weight="bold"),
                                    text_color="#1e293b")
        self.lbl_bud.pack(pady=(8, 2))
        self.prog = ctk.CTkProgressBar(bud, height=16, fg_color="#e2e8f0",
                                       progress_color="#22c55e", corner_radius=8)
        self.prog.pack(padx=16, pady=6, fill="x")
        self.prog.set(0)

        lframe = ctk.CTkFrame(bud, fg_color="transparent")
        lframe.pack(padx=16, pady=(6, 12), fill="x")
        self.entry_lim = ctk.CTkEntry(lframe, placeholder_text="Новый лимит...", height=30,
                                      width=110, fg_color="#f8fafc", border_color="#e2e8f0",
                                      text_color="#1e293b")
        self.entry_lim.pack(side="left")
        ctk.CTkButton(lframe, text="OK", width=32, height=30, fg_color="#3b82f6",
                      text_color="white", corner_radius=8,
                      command=self.change_limit).pack(side="left", padx=6)

        # ЦЕЛИ
        gls = ctk.CTkFrame(right, fg_color="#ffffff", corner_radius=16)
        gls.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        gls.grid_rowconfigure(1, weight=1)
        gls.grid_columnconfigure(0, weight=1)
        ghead = ctk.CTkFrame(gls, fg_color="transparent")
        ghead.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        ctk.CTkLabel(ghead, text="Финансовые цели",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#1e293b").pack(side="left")
        ctk.CTkButton(ghead, text="+", width=30, height=30, fg_color="#3b82f6",
                      text_color="white", corner_radius=8,
                      command=self.add_goal).pack(side="right")
        self.goals_list = ctk.CTkScrollableFrame(gls, fg_color="transparent",
                                                  scrollbar_button_color="#cbd5e1")
        self.goals_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)

    # ====== МЕТОДЫ ======
    def set_type(self, t):
        self.type_var.set(t)
        if t == "expense":
            self.btn_exp.configure(fg_color="#ef4444", text_color="white", border_width=0)
            self.btn_inc.configure(fg_color="transparent", text_color="#22c55e", border_width=2)
        else:
            self.btn_inc.configure(fg_color="#22c55e", text_color="white", border_width=0)
            self.btn_exp.configure(fg_color="transparent", text_color="#ef4444", border_width=2)

    def set_budget_mode(self, m):
        self.budget_mode = m
        if m == "week":
            self.btn_w.configure(fg_color="#3b82f6", text_color="white")
            self.btn_m.configure(fg_color="#e2e8f0", text_color="#64748b")
        else:
            self.btn_m.configure(fg_color="#3b82f6", text_color="white")
            self.btn_w.configure(fg_color="#e2e8f0", text_color="#64748b")
        self.update_budget()

    def change_limit(self):
        try:
            v = int(self.entry_lim.get().strip())
            if v <= 0:
                raise ValueError
            if self.budget_mode == "week":
                self.budget_limit_week = v
                self.cursor.execute("UPDATE settings SET value=? WHERE key='budget_week'", (str(v),))
            else:
                self.budget_limit_month = v
                self.cursor.execute("UPDATE settings SET value=? WHERE key='budget_month'", (str(v),))
            self.conn.commit()
            self.entry_lim.delete(0, 'end')
            self.update_budget()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму!")

    def add_transaction(self):
        d = self.entry_desc.get().strip()
        a = self.entry_amount.get().strip()
        tp = "ДОХОД" if self.type_var.get() == "income" else "РАСХОД"
        cat = self.combo_cat.get()
        dt = self.cal.get()
        if not d or not a:
            messagebox.showerror("Ошибка", "Заполните описание и сумму!")
            return
        try:
            int(a)
        except ValueError:
            messagebox.showerror("Ошибка", "Сумма должна быть числом!")
            return
        self.cursor.execute(
            "INSERT INTO transactions (text,date,type,category) VALUES (?,?,?,?)",
            (f"{tp}|{a}|{d}", dt, tp, cat)
        )
        self.conn.commit()
        self.entry_desc.delete(0, 'end')
        self.entry_amount.delete(0, 'end')
        self.refresh_data()

    def del_tx(self, tid):
        self.cursor.execute("DELETE FROM transactions WHERE id=?", (tid,))
        self.conn.commit()
        self.refresh_data()

    def set_filter(self, f):
        self.current_filter = f
        for fid, btn in [("all", self.btn_f_all), ("income", self.btn_f_income), ("expense", self.btn_f_expense)]:
            if fid == f:
                btn.configure(fg_color="#3b82f6", text_color="white", border_width=0)
            else:
                btn.configure(fg_color="transparent", text_color="#3b82f6", border_width=1)
        self.refresh_data()

    def add_goal(self):
        d = ctk.CTkInputDialog(text="Введите финансовую цель:", title="Новая цель")
        n = d.get_input()
        if n and n.strip():
            self.cursor.execute("INSERT INTO goals (text,streak,done_today) VALUES (?,0,0)", (n.strip(),))
            self.conn.commit()
            self.refresh_data()

    def tog_goal(self, gid, done, streak):
        nd = 0 if done else 1
        ns = streak + 1 if nd else max(0, streak - 1)
        self.cursor.execute("UPDATE goals SET done_today=?, streak=? WHERE id=?", (nd, ns, gid))
        self.conn.commit()
        self.refresh_data()

    def del_goal(self, gid):
        self.cursor.execute("DELETE FROM goals WHERE id=?", (gid,))
        self.conn.commit()
        self.refresh_data()

    def update_budget(self):
        today = date.today()
        if self.budget_mode == "week":
            sd = today - timedelta(days=7)
            lim = self.budget_limit_week
            txt = "за неделю"
        else:
            sd = today.replace(day=1)
            lim = self.budget_limit_month
            txt = "за месяц"
        self.cursor.execute(
            "SELECT text FROM transactions WHERE type='РАСХОД' AND date>=? AND date<=?",
            (sd.strftime("%d.%m.%Y"), today.strftime("%d.%m.%Y"))
        )
        rows = self.cursor.fetchall()
        total = sum(int(r[0].split('|')[1]) for r in rows
                    if len(r[0].split('|')) >= 2 and r[0].split('|')[1].isdigit())
        p = min(total / lim, 1.0) if lim > 0 else 0
        self.prog.set(p)
        self.lbl_bud.configure(text=f"Потрачено {txt}: {total} ₽ из {lim} ₽")
        if p > 0.9:
            self.prog.configure(progress_color="#ef4444")
        elif p > 0.7:
            self.prog.configure(progress_color="#f59e0b")
        else:
            self.prog.configure(progress_color="#22c55e")

    def refresh_data(self):
        for w in self.tx_list.winfo_children():
            w.destroy()

        if self.current_filter == "income":
            self.cursor.execute("SELECT * FROM transactions WHERE type='ДОХОД' ORDER BY id DESC")
        elif self.current_filter == "expense":
            self.cursor.execute("SELECT * FROM transactions WHERE type='РАСХОД' ORDER BY id DESC")
        else:
            self.cursor.execute("SELECT * FROM transactions ORDER BY id DESC")

        rows = self.cursor.fetchall()
        ti, te = 0, 0
        for row in rows:
            tid, txt, dt, tp, cat = row
            parts = txt.split('|')
            amt = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0
            desc = parts[2] if len(parts) >= 3 else ""
            if tp == "ДОХОД":
                ti += amt
            else:
                te += amt
            inc = tp == "ДОХОД"
            card = ctk.CTkFrame(self.tx_list, fg_color="#f0fdf4" if inc else "#fef2f2",
                                corner_radius=10, height=52)
            card.pack(fill="x", pady=3, padx=2)
            ctk.CTkLabel(card, text=f"{'+' if inc else '-'}{amt} ₽",
                         font=ctk.CTkFont(size=16, weight="bold"),
                         text_color="#16a34a" if inc else "#dc2626",
                         width=95).pack(side="left", padx=12, pady=12)
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=12),
                         text_color="#374151").pack(side="left", padx=4)
            ctk.CTkLabel(card, text=f"{cat} | {dt}", font=ctk.CTkFont(size=10),
                         text_color="#6b7280").pack(side="right", padx=8)
            ctk.CTkButton(card, text="X", width=24, height=24, fg_color="transparent",
                          text_color="#9ca3af", hover_color="#fee2e2",
                          command=lambda tid=tid: self.del_tx(tid)).pack(side="right", padx=4)

        bal = ti - te
        self.lbl_balance.configure(text=f"Баланс: {'+' if bal >= 0 else ''}{bal} ₽",
                                   text_color="#16a34a" if bal >= 0 else "#dc2626")

        for w in self.goals_list.winfo_children():
            w.destroy()
        self.cursor.execute("SELECT * FROM goals")
        for gid, gt, gs, gd in self.cursor.fetchall():
            gc = ctk.CTkFrame(self.goals_list, fg_color="#f0fdf4" if gd else "#f8fafc",
                              corner_radius=8, height=40)
            gc.pack(fill="x", pady=2, padx=2)
            ctk.CTkButton(gc, text="V" if gd else "O", width=24, height=24,
                          fg_color="#3b82f6" if gd else "#e2e8f0",
                          text_color="white" if gd else "#64748b",
                          corner_radius=12,
                          command=lambda gid=gid, gd=gd, gs=gs: self.tog_goal(gid, gd, gs)
                          ).pack(side="left", padx=8, pady=8)
            ctk.CTkLabel(gc, text=gt, font=ctk.CTkFont(size=11, overstrike=bool(gd)),
                         text_color="#374151" if not gd else "#9ca3af").pack(side="left", padx=4)
            ctk.CTkLabel(gc, text=f"Дней: {gs}", font=ctk.CTkFont(size=10),
                         text_color="#f59e0b").pack(side="right", padx=6)
            ctk.CTkButton(gc, text="X", width=20, height=20, fg_color="transparent",
                          text_color="#9ca3af",
                          command=lambda gid=gid: self.del_goal(gid)).pack(side="right", padx=2)

        self.update_budget()


if __name__ == "__main__":
    app = FinPulse()
    app.mainloop()