import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# --- DATABASE SETUP ---
DB_NAME = "study_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            last_studied TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---
def get_precise_time_ago(last_studied_str):
    if not last_studied_str:
        return "Never studied", "", float('inf')
    
    last_studied = datetime.fromisoformat(last_studied_str)
    exact_time_format = last_studied.strftime("%Y-%m-%d %H:%M:%S")
    
    delta = datetime.now() - last_studied
    seconds = int(delta.total_seconds())

    if seconds < 0:
        return "Just now", exact_time_format, 0
    if seconds < 60:
        return f"{seconds}s ago", exact_time_format, seconds

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s ago")

    time_ago_str = " ".join(parts)
    return time_ago_str, exact_time_format, seconds

# --- GUI APPLICATION ---
class StudyTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Subject Tracker")
        self.root.geometry("560x650")
        self.root.configure(bg="#F4F5F7")

        init_db()

        # UI Header & Add Subject Frame
        header_frame = tk.Frame(self.root, bg="#F4F5F7", pady=15)
        header_frame.pack(fill="x", padx=20)

        title = tk.Label(header_frame, text="Subject Tracker", font=("Segoe UI", 16, "bold"), bg="#F4F5F7", fg="#172B4D")
        title.pack(anchor="w", pady=(0, 10))

        add_frame = tk.Frame(header_frame, bg="#F4F5F7")
        add_frame.pack(fill="x")

        self.subject_entry = ttk.Entry(add_frame, font=("Segoe UI", 11))
        self.subject_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.subject_entry.bind("<Return>", lambda e: self.add_subject())

        add_btn = tk.Button(
            add_frame, 
            text="➕ Add Subject", 
            command=self.add_subject,
            font=("Segoe UI", 10, "bold"),
            bg="#0052CC", 
            fg="white", 
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2"
        )
        add_btn.pack(side="right")

        # Scrollable Canvas for Subject Cards
        container = tk.Frame(self.root, bg="#F4F5F7")
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = tk.Canvas(container, bg="#F4F5F7", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="#F4F5F7")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.refresh_subject_list()

    def add_subject(self):
        name = self.subject_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Subject name cannot be empty.")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO subjects (name, last_studied) VALUES (?, NULL)", (name,))
            conn.commit()
            self.subject_entry.delete(0, tk.END)
            self.refresh_subject_list()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"'{name}' is already in your study list.")
        finally:
            conn.close()

    def log_study(self, subject_id):
        now_str = datetime.now().isoformat()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE subjects SET last_studied = ? WHERE id = ?", (now_str, subject_id))
        conn.commit()
        conn.close()
        self.refresh_subject_list()

    def delete_subject(self, subject_id):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        conn.commit()
        conn.close()
        self.refresh_subject_list()

    def refresh_subject_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, last_studied FROM subjects")
        rows = cursor.fetchall()
        conn.close()

        processed_subjects = []
        for s_id, name, last_studied in rows:
            time_ago_str, exact_time_format, elapsed_seconds = get_precise_time_ago(last_studied)
            processed_subjects.append({
                "id": s_id,
                "name": name,
                "time_ago": time_ago_str,
                "exact_time": exact_time_format,
                "elapsed": elapsed_seconds
            })

        processed_subjects.sort(key=lambda x: x["elapsed"], reverse=True)

        if not processed_subjects:
            empty_lbl = tk.Label(
                self.scrollable_frame, 
                text="No subjects added yet. Add one above to get started!", 
                font=("Segoe UI", 10, "italic"), 
                bg="#F4F5F7", 
                fg="#5E6C84"
            )
            empty_lbl.pack(pady=20)
            return

        for sub in processed_subjects:
            if sub["elapsed"] == float('inf'):
                card_bg = "#FFEBE6"
                border_color = "#FF8F73"
            elif sub["elapsed"] > 259200:  # > 3 days
                card_bg = "#FFF0B3"
                border_color = "#FFC400"
            else:
                card_bg = "#E3FCEF"
                border_color = "#57D9A3"

            card = tk.Frame(self.scrollable_frame, bg=card_bg, highlightbackground=border_color, highlightthickness=1, bd=0)
            card.pack(fill="x", expand=True, pady=4, ipady=4)

            info_frame = tk.Frame(card, bg=card_bg)
            info_frame.pack(side="left", fill="both", expand=True, padx=10)

            name_lbl = tk.Label(info_frame, text=sub["name"], font=("Segoe UI", 11, "bold"), bg=card_bg, fg="#172B4D", anchor="w")
            name_lbl.pack(fill="x")

            # Precise relative display + exact timestamp
            if sub["exact_time"]:
                time_display = f"Last studied: {sub['time_ago']} ({sub['exact_time']})"
            else:
                time_display = f"Last studied: {sub['time_ago']}"

            time_lbl = tk.Label(info_frame, text=time_display, font=("Segoe UI", 9), bg=card_bg, fg="#5E6C84", anchor="w")
            time_lbl.pack(fill="x")

            btn_frame = tk.Frame(card, bg=card_bg)
            btn_frame.pack(side="right", padx=10)

            log_btn = tk.Button(
                btn_frame, 
                text="✔ Log Study", 
                command=lambda s_id=sub["id"]: self.log_study(s_id),
                font=("Segoe UI", 9, "bold"),
                bg="#00875A", 
                fg="white", 
                relief="flat",
                cursor="hand2"
            )
            log_btn.pack(side="left", padx=(0, 5))

            del_btn = tk.Button(
                btn_frame, 
                text="✕", 
                command=lambda s_id=sub["id"]: self.delete_subject(s_id),
                font=("Segoe UI", 9),
                bg=card_bg, 
                fg="#DE350B", 
                relief="flat",
                bd=0,
                cursor="hand2"
            )
            del_btn.pack(side="right")

if __name__ == "__main__":
    root = tk.Tk()
    app = StudyTrackerApp(root)
    root.mainloop()