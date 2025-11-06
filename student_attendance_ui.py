import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog
import os
import webbrowser

try:
    # Try to use the new SQL database module first
    from database_sql import (
        get_all_students, get_student_by_id, add_student, delete_student_by_id,
        get_attendance, mark_attendance_db, delete_attendance_by_id, get_next_student_id, KNOWN_FACES_DIR
    )
except ImportError:
    # Fallback to the original SQLite database module
    from database import (
        get_all_students, get_student_by_id, add_student, delete_student_by_id,
        get_attendance, mark_attendance_db, delete_attendance_by_id, get_next_student_id, KNOWN_FACES_DIR
    )

# --- Optional heavy deps (cv2, face_recognition, PIL) ---
def _lazy_imports():
    """Lazily import heavy dependencies. Raise ImportError with a helpful message if they are not installed."""
    try:
        import cv2
        import face_recognition
        from PIL import Image, ImageTk
        return cv2, face_recognition, Image, ImageTk
    except ImportError as e:
        raise ImportError(
            "Camera/Face features need: opencv-python, face_recognition, pillow.\n"
            f"Install with: pip install opencv-python face_recognition pillow\n\nDetails: {e}"
        )

# Ensure the known_faces directory exists
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

# ===================== GUI =====================
class FancyApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("Cogni-Attendance — Face Attendance System")
        self.master.geometry("1300x820") # Slightly larger window
        self.master.configure(bg="#1e1e1e")

        # --- Modern Color Palette ---
        self.colors = {
            "dark_bg": "#1e1e1e",
            "bg": "#252526",
            "card": "#2d2d2d",
            "text": "#d4d4d4",
            "muted": "#a0a0a0",
            "accent": "#007acc",
            "accent_hover": "#0095ff",
            "green": "#4caf50",
            "red": "#f44336",
            "border": "#4a4a4a"
        }

        self.fonts = {
            "main": ("Segoe UI", 11),
            "bold": ("Segoe UI", 11, "bold"),
            "title": ("Segoe UI", 22, "bold"),
            "h1": ("Segoe UI", 18, "bold"),
            "h2": ("Segoe UI", 14, "bold"),
        }

        self.avatar = None
        self.avatar_label = None
        self.student_table = None
        self.attendance_columns = ("ID", "Name", "Date", "Time")
        self.attendance_table = None
        self.combo_camera = None
        self.btn_settings = None
        self.left_panel = None
        self.center_panel = None
        self.settings_panel = None
        self.settings_open = False
        self.status_label = None
        self.student_search_var = tk.StringVar()
        self.attendance_search_var = tk.StringVar()
        self.all_students_data = []
        self.all_attendance_data = []

        self.setup_styles()
        self.create_widgets()

        self.load_students()
        self.load_attendance()

        # Check if the database is empty and guide the user
        if not self.student_table.get_children():
            self.show_status("Welcome! Your database is empty. Add students to begin.", "accent")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # General widget styles
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["card"], relief="solid", borderwidth=1, bordercolor=self.colors["border"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=self.fonts["main"])
        style.configure("Card.TLabel", background=self.colors["card"], foreground=self.colors["text"], font=self.fonts["main"])
        style.configure("TEntry", fieldbackground=self.colors["bg"], foreground=self.colors["text"], insertcolor=self.colors["text"], bordercolor=self.colors["border"], lightcolor=self.colors["card"], darkcolor=self.colors["card"])

        # Button styles
        style.configure("TButton", font=self.fonts["bold"], padding=(12, 8), borderwidth=0, focusthickness=0, anchor="center")
        style.map("TButton",
                  foreground=[('active', self.colors["text"])],
                  background=[('active', self.colors["accent_hover"])])

        style.configure("Accent.TButton", background=self.colors["accent"], foreground="white")
        style.map("Accent.TButton", background=[('active', self.colors["accent_hover"])] )

        style.configure("Soft.TButton", background="#4f4f4f", foreground=self.colors["text"])
        style.map("Soft.TButton", background=[('active', "#5a5a5a")])

        # Treeview style
        style.configure("Treeview",
                        background="#252526", fieldbackground="#252526",
                        foreground=self.colors["text"], rowheight=32, borderwidth=0, font=self.fonts["main"])
        style.configure("Treeview.Heading", background="#3c3c3c", foreground=self.colors["text"], font=self.fonts["bold"], padding=(10,10))
        style.map("Treeview", background=[("selected", self.colors["accent"])], foreground=[("selected", "white")])
        style.map("Treeview.Heading", background=[('active', '#4a4a4a')])


        # Notebook style
        style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background="#2d2d2d", foreground=self.colors["muted"], font=self.fonts["bold"], padding=[15, 8])
        style.map("TNotebook.Tab",
                  background=[("selected", self.colors["card"])],
                  foreground=[("selected", self.colors["text"])] )

    def create_widgets(self):
        # --- Top bar ---
        top = tk.Frame(self.master, bg=self.colors["dark_bg"], pady=10)
        top.pack(fill="x", side="top")
        tk.Label(top, text="Cogni-Attendance", font=self.fonts["title"],
                 bg=self.colors["dark_bg"], fg=self.colors["text"])
        self.btn_settings = ttk.Button(top, text="⚙ Settings", style="Soft.TButton",
                                       command=self.toggle_settings)
        self.btn_settings.pack(side="right", padx=25)

        # --- Status Bar ---
        self.status_label = tk.Label(self.master, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                     bg=self.colors["accent"], fg="white", font=self.fonts["bold"])
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)


        # --- Main layout ---
        main = tk.Frame(self.master, bg=self.colors["bg"])
        main.pack(fill="both", expand=True, padx=25, pady=20)

        self.left_panel = ttk.Frame(main, style="Card.TFrame", width=320)
        self.left_panel.pack(side="left", fill="y", padx=(0, 20))
        self.left_panel.pack_propagate(False)
        self.build_left_panel(self.left_panel)

        self.center_panel = ttk.Frame(main)
        self.center_panel.pack(side="left", fill="both", expand=True)
        self.build_center_tabs(self.center_panel)

        # Settings panel (initially hidden)
        self.settings_panel = ttk.Frame(main, style="Card.TFrame", width=320)
        self.build_settings(self.settings_panel)

    def build_left_panel(self, parent):
        parent.configure(style="Card.TFrame")
        
        avatar_frame = ttk.Frame(parent, style="Card.TFrame", width=260, height=260)
        avatar_frame.pack(pady=20)
        avatar_frame.pack_propagate(False)

        self.avatar = tk.Label(avatar_frame, bg="#252526", bd=0)
        self.avatar.pack(fill="both", expand=True)

        self.avatar_label = tk.Label(parent, text="Live Camera / Profile", bg=self.colors["card"], fg=self.colors["muted"], font=self.fonts["main"])
        self.avatar_label.pack(pady=(0, 15))

        ttk.Button(parent, text="📷 Start Recognition", style="Accent.TButton",
                   command=self.start_attendance_camera).pack(padx=20, pady=10, fill="x", ipady=5)

        # Quick actions
        qframe = ttk.Frame(parent, style="Card.TFrame")
        qframe.pack(padx=20, pady=15, fill="x")
        ttk.Button(qframe, text="🌐 View Web App", style="Soft.TButton",
                   command=self.open_web_app).pack(fill="x", pady=5)

    def build_center_tabs(self, parent):
        nb = ttk.Notebook(parent, style="TNotebook")
        nb.pack(fill="both", expand=True)

        tab_students = ttk.Frame(nb)
        nb.add(tab_students, text="👥 People Management")

        tab_att = ttk.Frame(nb)
        nb.add(tab_att, text="🗓️ Attendance Log")

        self.build_students_tab(tab_students)
        self.build_attendance_tab(tab_att)

    def build_students_tab(self, parent):
        # Search and actions bar
        top_bar = ttk.Frame(parent)
        top_bar.pack(fill="x", padx=10, pady=(10,0))
        
        search_entry = ttk.Entry(top_bar, textvariable=self.student_search_var, width=40, font=self.fonts["main"])
        search_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
        search_entry.bind("<Return>", self.search_students)

        ttk.Button(top_bar, text="🔍 Search", style="Soft.TButton", command=self.search_students).pack(side="left", padx=5)
        
        ttk.Button(top_bar, text="🗑️ Delete", style="Soft.TButton", command=self.delete_selected_student).pack(side="right", padx=5)
        ttk.Button(top_bar, text="🔄 Reload", style="Soft.TButton", command=self.load_students).pack(side="right", padx=5)


        # Table
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        cols = ("ID", "Name", "Faculty", "Email", "Address", "DOB")
        self.student_table = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.student_table.heading(c, text=c)
            self.student_table.column(c, width=140, anchor="w")
        self.student_table.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.student_table.yview)
        self.student_table.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.student_table.bind("<<TreeviewSelect>>", self.on_table_select)


    def build_attendance_tab(self, parent):
        # Search and actions bar
        top_bar = ttk.Frame(parent)
        top_bar.pack(fill="x", padx=10, pady=(10,0))
        
        search_entry = ttk.Entry(top_bar, textvariable=self.attendance_search_var, width=40, font=self.fonts["main"])
        search_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
        search_entry.bind("<Return>", self.search_attendance)

        ttk.Button(top_bar, text="🔍 Search", style="Soft.TButton", command=self.search_attendance).pack(side="left", padx=5)
        ttk.Button(top_bar, text="🗑️ Delete Selected", style="Soft.TButton", command=self.delete_selected_attendance).pack(side="right", padx=5)
        ttk.Button(top_bar, text="🔄 Reload", style="Soft.TButton", command=self.load_attendance).pack(side="right", padx=5)

        # Table
        att_frame = ttk.Frame(parent)
        att_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.attendance_table = ttk.Treeview(att_frame, columns=self.attendance_columns, show="headings")
        for c, w in zip(self.attendance_columns, (150, 220, 150, 150)):
            self.attendance_table.heading(c, text=c)
            self.attendance_table.column(c, width=w, anchor="w")
        self.attendance_table.pack(side="left", fill="both", expand=True)
        asb = ttk.Scrollbar(att_frame, orient="vertical", command=self.attendance_table.yview)
        self.attendance_table.configure(yscrollcommand=asb.set)
        asb.pack(side="right", fill="y")

    def build_settings(self, parent):
        parent.configure(style="Card.TFrame")
        tk.Label(parent, text="Settings", background=self.colors["card"], foreground=self.colors["text"],
                 font=self.fonts["h1"])

        cam_frame = tk.LabelFrame(parent, text="Camera Selection", background=self.colors["card"], foreground=self.colors["text"], font=self.fonts["bold"], relief="solid", borderwidth=1, bd=1)
        cam_frame.pack(fill="x", padx=20, pady=10, ipady=5)
        tk.Label(cam_frame, text="Device Index", background=self.colors["card"], foreground=self.colors["text"])
        self.combo_camera = ttk.Combobox(cam_frame, values=['0', '1', '2', '3'], state="readonly", font=self.fonts["main"])
        self.combo_camera.set('0')
        self.combo_camera.pack(fill="x", padx=10, pady=(0, 10))

        util = tk.LabelFrame(parent, text="Utilities", background=self.colors["card"], foreground=self.colors["text"], font=self.fonts["bold"], relief="solid", borderwidth=1, bd=1)
        util.pack(fill="x", padx=20, pady=10, ipady=5)
        ttk.Button(util, text="🌐 Open Web App", style="Soft.TButton",
                   command=self.open_web_app).pack(fill="x", padx=10, pady=6)

    def animate_settings_panel(self, reverse=False):
        if reverse: # Close panel
            self.settings_open = False
            self.btn_settings.configure(text="⚙ Settings")
            end_x = self.master.winfo_width()
            start_x = end_x - 320
            dx = 20
        else: # Open panel
            self.settings_open = True
            self.btn_settings.configure(text="✕ Close")
            start_x = self.master.winfo_width()
            end_x = self.master.winfo_width() - 320
            dx = -20

        def step_animation(current_x):
            if (not reverse and current_x <= end_x) or (reverse and current_x >= end_x):
                if reverse:
                    self.settings_panel.place_forget()
                return
            self.settings_panel.place(x=current_x, y=self.left_panel.winfo_y(), relheight=1.0)
            self.master.after(10, step_animation, current_x + dx)

        if not reverse:
            self.settings_panel.place(x=start_x, y=self.left_panel.winfo_y(), relheight=1.0)
        step_animation(start_x)

    def toggle_settings(self):
        self.animate_settings_panel(reverse=self.settings_open)

    @staticmethod
    def open_web_app():
        webbrowser.open("http://127.0.0.1:5000")

    def show_status(self, message, level="info"):
        self.status_label.config(text=f" {message}")
        if level == "info":
            self.status_label.config(bg=self.colors["dark_bg"], fg=self.colors["text"])
        elif level == "success":
            self.status_label.config(bg=self.colors["green"], fg="white")
        elif level == "warning":
            self.status_label.config(bg="#ffc107", fg="black")
        elif level == "error":
            self.status_label.config(bg=self.colors["red"], fg="white")
        elif level == "accent":
            self.status_label.config(bg=self.colors["accent"], fg="white")

    # ===================== Behaviors =====================
    def load_students(self, query=None):
        for item in self.student_table.get_children():
            self.student_table.delete(item)
        
        if not self.all_students_data or query is None:
            self.all_students_data = get_all_students()

        students_to_display = self.all_students_data
        if query:
            query = query.lower()
            students_to_display = [s for s in self.all_students_data if query in s.get('name', '').lower() or query in s.get('id', '').lower()]

        for student in students_to_display:
            values = (
                student.get('id', ''),
                student.get('name', ''),
                student.get('faculty', ''),
                student.get('email', ''),
                student.get('address', ''),
                student.get('dob', '')
            )
            self.student_table.insert("", "end", values=values)
        
        if query:
            self.show_status(f"Found {len(students_to_display)} students matching '{query}'.", "info")
        else:
            self.show_status(f"Loaded {len(students_to_display)} students.", "info")


    def search_students(self, _event=None):
        query = self.student_search_var.get()
        self.load_students(query=query)

    def on_table_select(self, _event=None):
        sel = self.student_table.selection()
        if not sel:
            self.avatar.config(image='')
            self.avatar.image = None
            if self.avatar_label:
                self.avatar_label.config(text="Live Camera / Profile", fg=self.colors["muted"])
            return

        vals = self.student_table.item(sel[0], "values")
        if not vals:
            return
        student_id = vals[0]
        student = get_student_by_id(student_id)
        if not student:
            return

        if self.avatar_label:
            self.avatar_label.config(text=student.get('name', 'Profile'), fg=self.colors["text"])

        try:
            _, _, Image, ImageTk = _lazy_imports()  # noqa
            img_path = os.path.join(KNOWN_FACES_DIR, f"{student_id}.jpg")
            if os.path.exists(img_path):
                img = Image.open(img_path)
                img = img.resize((256, 256), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                self.avatar.config(image=imgtk)
                self.avatar.image = imgtk
            else:
                self.avatar.config(image='')
                self.avatar.image = None
        except (IOError, SyntaxError) as e:
            print(f"Error loading avatar for {student_id}: {e}")
            self.avatar.config(image='')
            self.avatar.image = None

    def load_attendance(self, query=None):
        for i in self.attendance_table.get_children():
            self.attendance_table.delete(i)
        
        if not self.all_attendance_data or query is None:
            self.all_attendance_data = get_attendance()

        records_to_display = self.all_attendance_data
        if query:
            query = query.lower()
            records_to_display = [r for r in self.all_attendance_data if query in r.get('name', '').lower() or query in r.get('student_id', '').lower() or query in r.get('date', '')]

        for rec in records_to_display:
            values = (
                rec.get('student_id', ''),
                rec.get('name', ''),
                rec.get('date', ''),
                rec.get('time', '')
            )
            self.attendance_table.insert("", "end", iid=rec.get('id'), values=values)
        
        if query:
            self.show_status(f"Found {len(records_to_display)} attendance records matching '{query}'.", "info")
        else:
            self.show_status(f"Loaded {len(records_to_display)} attendance records.", "info")

    def search_attendance(self, _event=None):
        query = self.attendance_search_var.get()
        self.load_attendance(query=query)

    def delete_selected_attendance(self):
        sel = self.attendance_table.selection()
        if not sel:
            self.show_status("Select an attendance row to delete.", "warning")
            return
        att_id = sel[0]
        if not messagebox.askyesno("Confirm", f"Delete attendance record? (ID: {att_id})"): 
            return

        if delete_attendance_by_id(att_id):
            self.all_attendance_data = [] # Force reload
            self.load_attendance()
            self.show_status("Attendance record deleted.", "success")
        else:
            self.show_status("Error: Record not found.", "error")

    

    

    def delete_selected_student(self):
        sel = self.student_table.selection()
        if not sel:
            self.show_status("Select a student to delete.", "warning")
            return
        
        vals = self.student_table.item(sel[0], "values")
        if not vals:
            return
        
        student_id, name = vals[0], vals[1]
        
        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {name} ({student_id})?\nThis will also delete their attendance records."):
            return

        try:
            delete_student_by_id(student_id)
            self.show_status(f"Student {name} deleted.", "success")
            self.all_students_data = [] # Force reload
            self.all_attendance_data = []
            self.load_students()
            self.load_attendance()
        except Exception as e:
            self.show_status(f"Error deleting student: {e}", "error")


    # ---------- Camera-based live attendance ----------
    def start_attendance_camera(self):
        try:
            cv2, face_recognition, Image, ImageTk = _lazy_imports()  # noqa
        except ImportError as e:
            messagebox.showerror("Missing Dependencies", str(e))
            return

        students = get_all_students()
        if not students:
            messagebox.showerror("No Students Registered", "There are no students in the database. Please register a student first.")
            return

        known_encodings = []
        known_ids = []
        loading_errors = []
        for student_data in students:
            student_id = student_data.get('id')
            img_path = os.path.join(KNOWN_FACES_DIR, f"{student_id}.jpg")
            if os.path.exists(img_path):
                try:
                    img = face_recognition.load_image_file(img_path)
                    face_encs = face_recognition.face_encodings(img)
                    if face_encs:
                        known_encodings.append(face_encs[0])
                        known_ids.append(student_id)
                    else:
                        loading_errors.append(f"No face detected for ID: {student_id}")
                except Exception as e:
                    loading_errors.append(f"Error with image for ID {student_id}: {e}")
            else:
                loading_errors.append(f"Image not found for ID: {student_id}")

        if not known_encodings:
            error_details = "\n".join(loading_errors)
            messagebox.showerror(
                "No Faces Loaded",
                f"Could not load any valid faces from the 'known_faces' directory.\n\nDetails:\n{error_details}"
            )
            return

        cam_index = int(self.combo_camera.get()) if self.combo_camera.get() else 0
        cap = cv2.VideoCapture(cam_index)
        
        # Check if the camera has been opened successfully.
        if not cap.isOpened():
            messagebox.showerror("Camera Error", f"Cannot open camera at index {cam_index}. It may be in use by another application or disconnected.")
            return

        # Check if the camera can grab a frame.
        ret, _ = cap.read()
        if not ret:
            cap.release()
            messagebox.showerror(
                "Camera Hardware Error",
                f"Could not grab a frame from camera at index {cam_index}.\n\n" 
                "This usually indicates a hardware or driver issue.\n\n" 
                "Please try the following:\n"
                "1. Restart your computer.\n"
                "2. Ensure your camera is not in use by another application.\n"
                "3. Update your camera drivers via Device Manager."
            )
            return

        cam_window = tk.Toplevel(self.master)
        cam_window.title("Live Attendance Camera")
        cam_window.geometry("900x700")
        cam_window.configure(bg=self.colors["dark_bg"])

        video_frame = ttk.Frame(cam_window, style="Card.TFrame")
        video_frame.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(video_frame, text="Live Attendance", background=self.colors["card"], fg=self.colors["text"],
                 font=self.fonts["h1"])

        cam_label = tk.Label(video_frame, bg="#000")
        cam_label.pack(padx=10, pady=10, fill="both", expand=True)

        status_label = tk.Label(video_frame, text="", background=self.colors["card"], fg=self.colors["green"],
                                font=self.fonts["bold"])
        status_label.pack(pady=10)

        stop_btn = ttk.Button(video_frame, text="Stop", style="Soft.TButton", command=cam_window.destroy)
        stop_btn.pack(pady=10)

        seen_today = set()

        def update_frame():
            nonlocal cap
            if not cap.isOpened():
                return

            ret, frame = cap.read()
            if not ret:
                status_label.config(text="Camera error.")
                return
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb)
            face_encodings = face_recognition.face_encodings(rgb, face_locations)

            for enc, loc in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(known_encodings, enc)

                if True in matches:
                    first_match_index = matches.index(True)
                    sid = known_ids[first_match_index]
                    current_student = get_student_by_id(sid)
                    name = current_student.get('name', 'Unknown')

                    if sid in seen_today:
                        status_label.config(text=f"Already marked: {name} ({sid})", fg=self.colors["accent"])
                    else:
                        new_row = mark_attendance_db(sid)
                        if new_row:
                            seen_today.add(sid)
                            self.all_attendance_data = [] # Force reload
                            self.load_attendance()
                            status_label.config(text=f"Attendance marked: {name} ({sid})", fg=self.colors["green"])
                        else:
                            status_label.config(text=f"Duplicate (12h rule): {name} ({sid})", fg=self.colors["muted"])

                    y1, x2, y2, x1 = loc
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                else:
                    y1, x2, y2, x1 = loc
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, "Not Registered. Please Register.", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    status_label.config(text="Unknown face detected. Please register.", fg=self.colors["red"])

            disp = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            disp = cv2.resize(disp, (860, 540))
            imgtk = ImageTk.PhotoImage(Image.fromarray(disp))
            cam_label.imgtk = imgtk
            cam_label.config(image=imgtk)

            if cam_window.winfo_exists():
                cam_label.after(15, update_frame)
            else:
                cap.release()
                cv2.destroyAllWindows()

        update_frame()

# ---- launch ----
if __name__ == "__main__":
    root = tk.Tk()
    app = FancyApp(root)
    root.mainloop()