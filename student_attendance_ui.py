
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import os
import webbrowser
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
        self.master.title("CognAttendance — Face Attendance System")
        self.master.geometry("1280x800")
        self.master.configure(bg="#1e1e1e")

        # --- Modern Color Palette ---
        self.colors = {
            "dark_bg": "#1e1e1e",
            "bg": "#2d2d2d",
            "card": "#3c3c3c",
            "text": "#d4d4d4",
            "muted": "#a0a0a0",
            "accent": "#007acc",
            "accent_active": "#005f9e",
            "green": "#4caf50",
            "red": "#f44336"
        }

        self.avatar = None
        self.entries = {}
        self.entry_id = None
        self.student_table = None
        self.attendance_columns = ("ID", "Name", "Date", "Time")
        self.attendance_table = None
        self.combo_camera = None
        self.btn_settings = None
        self.left_panel = None
        self.center_panel = None
        self.settings_panel = None
        self.settings_open = False

        self.setup_styles()
        self.create_widgets()

        self.load_students()
        self.load_attendance()

        # Check if the database is empty and guide the user
        if not self.student_table.get_children():
            messagebox.showinfo(
                "Database is Empty",
                "Welcome! Your database is currently empty.\n\n"
                "If you have existing CSV files, please run the `migrate_to_db.py` script to import your data.\n\n"
                "Otherwise, you can start by registering new students."
            )

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # General widget styles
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["card"], relief="solid", borderwidth=1, bordercolor="#4a4a4a")
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 11))
        style.configure("Card.TLabel", background=self.colors["card"], foreground=self.colors["text"], font=("Segoe UI", 11))

        # Button styles
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(10, 8), borderwidth=0, focusthickness=0)
        style.map("TButton",
                  foreground=[('active', self.colors["text"])],
                  background=[('active', self.colors["accent_active"])])

        style.configure("Accent.TButton", background=self.colors["accent"], foreground="white")
        style.map("Accent.TButton", background=[('active', self.colors["accent_active"])])

        style.configure("Soft.TButton", background="#4f4f4f", foreground=self.colors["text"])
        style.map("Soft.TButton", background=[('active', "#5a5a5a")])

        # Treeview style
        style.configure("Treeview",
                        background="#252526", fieldbackground="#252526",
                        foreground=self.colors["text"], rowheight=30, borderwidth=0)
        style.configure("Treeview.Heading", background="#3c3c3c", foreground=self.colors["text"], font=("Segoe UI", 11, "bold"))
        style.map("Treeview", background=[("selected", self.colors["accent"])])

        # Notebook style
        style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background="#2d2d2d", foreground=self.colors["muted"], font=("Segoe UI", 11, "bold"), padding=[12, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", self.colors["card"])],
                  foreground=[("selected", self.colors["text"])])

    def create_widgets(self):
        # --- Top bar ---
        top = tk.Frame(self.master, bg="#1e1e1e")
        top.pack(fill="x", side="top", pady=(0, 10))
        tk.Label(top, text="CognAttendance", font=("Segoe UI", 18, "bold"),
                 bg="#1e1e1e", fg=self.colors["text"]).pack(side="left", padx=20, pady=10)
        self.btn_settings = ttk.Button(top, text="⚙ Settings", style="Soft.TButton",
                                       command=self.toggle_settings)
        self.btn_settings.pack(side="right", padx=20, pady=10)

        # --- Main layout ---
        main = tk.Frame(self.master, bg=self.colors["bg"])
        main.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.left_panel = ttk.Frame(main, style="Card.TFrame", width=300)
        self.left_panel.pack(side="left", fill="y", padx=(0, 20))
        self.left_panel.pack_propagate(False)
        self.build_left_panel(self.left_panel)

        self.center_panel = ttk.Frame(main)
        self.center_panel.pack(side="left", fill="both", expand=True)
        self.build_center_tabs(self.center_panel)

        self.settings_panel = ttk.Frame(main, style="Card.TFrame", width=320)
        self.build_settings(self.settings_panel)

    def build_left_panel(self, parent):
        parent.configure(style="Card.TFrame")
        # Avatar/preview placeholder
        self.avatar = tk.Label(parent, bg="#252526", bd=1, relief="solid", width=34, height=17)
        self.avatar.pack(padx=20, pady=20)
        tk.Label(parent, text="Live Camera / Profile", bg=self.colors["card"], fg=self.colors["muted"],
                 font=("Segoe UI", 10)).pack(pady=(0, 15))

        ttk.Button(parent, text="Start Recognition", style="Accent.TButton",
                   command=self.start_attendance_camera).pack(padx=20, pady=10, fill="x")

        # Quick actions
        qframe = ttk.Frame(parent, style="Card.TFrame")
        qframe.pack(padx=20, pady=15, fill="x")
        ttk.Button(qframe, text="Take Attendance", style="Soft.TButton",
                   command=self.start_attendance_camera).pack(fill="x", pady=5)
        ttk.Button(qframe, text="View Web App", style="Soft.TButton",
                   command=self.open_web_app).pack(fill="x", pady=5)

    def build_center_tabs(self, parent):
        nb = ttk.Notebook(parent, style="TNotebook")
        nb.pack(fill="both", expand=True)

        tab_students = ttk.Frame(nb)
        nb.add(tab_students, text="People Management")

        tab_att = ttk.Frame(nb)
        nb.add(tab_att, text="Attendance")

        self.build_students_tab(tab_students)
        self.build_attendance_tab(tab_att)

    def build_students_tab(self, parent):
        form = ttk.Frame(parent, style="Card.TFrame")
        form.pack(side="top", fill="x", padx=10, pady=10)

        def field(row, label):
            tk.Label(form, text=label, background=self.colors["card"], foreground=self.colors["text"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=10, pady=8)
            e = tk.Entry(form, width=35, bg="#252526", fg=self.colors["text"], insertbackground=self.colors["text"], relief="solid", bd=1)
            e.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            return e

        self.entries["Name"] = field(0, "Name")
        self.entries["Faculty"] = field(1, "Faculty")
        self.entries["Email"] = field(2, "Email")
        self.entries["Address"] = field(3, "Address")
        self.entries["DOB"] = field(4, "DOB (yyyy-mm-dd)")

        tk.Label(form, text="Student ID", background=self.colors["card"], foreground=self.colors["text"], font=("Segoe UI", 10)).grid(row=5, column=0, sticky="w", padx=10, pady=8)
        self.entry_id = tk.Entry(form, width=35, relief="solid", bd=1, state="readonly", readonlybackground="#252526", fg=self.colors["text"])
        self.entry_id.grid(row=5, column=1, sticky="ew", padx=10, pady=8)
        self.update_student_id()

        actions = ttk.Frame(form, style="Card.TFrame")
        actions.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        ttk.Button(actions, text="Register", style="Accent.TButton", command=self.register_student).pack(side="left", padx=5)
        ttk.Button(actions, text="Update", style="Soft.TButton", command=self.update_student).pack(side="left", padx=5)
        ttk.Button(actions, text="Delete", style="Soft.TButton", command=self.delete_selected_student).pack(side="left", padx=5)
        ttk.Button(actions, text="Clear", style="Soft.TButton", command=self.clear_form).pack(side="left", padx=5)

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

        btnbar = ttk.Frame(parent)
        btnbar.pack(fill="x", padx=10, pady=10)
        ttk.Button(btnbar, text="Delete Selected", style="Soft.TButton",
                   command=self.delete_selected_attendance).pack(side="left", padx=5)
        ttk.Button(btnbar, text="Reload", style="Soft.TButton",
                   command=self.load_attendance).pack(side="left", padx=5)

    def build_settings(self, parent):
        parent.configure(style="Card.TFrame")
        tk.Label(parent, text="Settings", background=self.colors["card"], foreground=self.colors["text"],
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=20, pady=(20, 10))

        cam_frame = tk.LabelFrame(parent, text="Camera Selection", background=self.colors["card"], foreground=self.colors["text"], font=("Segoe UI", 11))
        cam_frame.configure(borderwidth=1, relief="solid")
        cam_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(cam_frame, text="Device Index", background=self.colors["card"], foreground=self.colors["text"]).pack(anchor="w", padx=10, pady=5)
        self.combo_camera = ttk.Combobox(cam_frame, values=['0', '1', '2', '3'], state="readonly")
        self.combo_camera.set('0')
        self.combo_camera.pack(fill="x", padx=10, pady=(0, 10))

        util = tk.LabelFrame(parent, text="Utilities", background=self.colors["card"], foreground=self.colors["text"], font=("Segoe UI", 11))
        util.configure(borderwidth=1, relief="solid")
        util.pack(fill="x", padx=20, pady=10)
        ttk.Button(util, text="Open Web App", style="Soft.TButton",
                   command=self.open_web_app).pack(fill="x", padx=10, pady=6)

    def toggle_settings(self):
        if self.settings_open:
            self.settings_panel.pack_forget()
            self.btn_settings.configure(text="⚙ Settings")
        else:
            self.settings_panel.pack(side="right", fill="y", padx=(0, 0))
            self.btn_settings.configure(text="✕ Close")
        self.settings_open = not self.settings_open

    @staticmethod
    def open_web_app():
        webbrowser.open("http://127.0.0.1:5000")

    # ===================== Behaviors =====================
    def update_student_id(self):
        sid = get_next_student_id()
        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, tk.END)
        self.entry_id.insert(0, sid)
        self.entry_id.configure(state="readonly")

    def clear_form(self):
        for e in self.entries.values():
            e.delete(0, tk.END)
        self.update_student_id()
        self.avatar.config(image='')
        self.avatar.image = None

    def load_students(self):
        for item in self.student_table.get_children():
            self.student_table.delete(item)
        students = get_all_students()
        for student in students:
            values = (
                student.get('id', ''),
                student.get('name', ''),
                student.get('faculty', ''),
                student.get('email', ''),
                student.get('address', ''),
                student.get('dob', '')
            )
            self.student_table.insert("", "end", values=values)

    def on_table_select(self, _event=None):
        sel = self.student_table.selection()
        if not sel:
            return
        vals = self.student_table.item(sel[0], "values")
        if not vals:
            return
        student_id = vals[0]
        student = get_student_by_id(student_id)
        if not student:
            return

        self.entries["Name"].delete(0, tk.END)
        self.entries["Name"].insert(0, student.get('name', ''))
        self.entries["Faculty"].delete(0, tk.END)
        self.entries["Faculty"].insert(0, student.get('faculty', ''))
        self.entries["Email"].delete(0, tk.END)
        self.entries["Email"].insert(0, student.get('email', ''))
        self.entries["Address"].delete(0, tk.END)
        self.entries["Address"].insert(0, student.get('address', ''))
        self.entries["DOB"].delete(0, tk.END)
        self.entries["DOB"].insert(0, student.get('dob', ''))
        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, tk.END)
        self.entry_id.insert(0, student.get('id', ''))
        self.entry_id.configure(state="readonly")

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

    def prepare_register(self):
        self.clear_form()
        self.entries["Name"].focus_set()

    def register_student(self):
        name = self.entries["Name"].get().strip()
        faculty = self.entries["Faculty"].get().strip()
        email = self.entries["Email"].get().strip()
        address = self.entries["Address"].get().strip()
        dob = self.entries["DOB"].get().strip()
        sid = self.entry_id.get().strip()

        if not all([name, faculty, email, address, dob]):
            messagebox.showwarning("Missing Info", "Please fill all required fields.")
            return

        add_student(sid, name, faculty, dob, email, address)

        # Capture face
        try:
            cv2, _, _, _ = _lazy_imports()  # noqa
        except ImportError as e:
            messagebox.showerror("Missing Dependencies", str(e))
            self.load_students()
            return

        cam_index = int(self.combo_camera.get()) if self.combo_camera.get() else 0
        cam = cv2.VideoCapture(cam_index)
        if not cam.isOpened():
            messagebox.showerror("Camera Error", "Cannot open camera. Check device & permissions.")
            return
        messagebox.showinfo("Capture", "Press SPACE to capture, Q to cancel.")

        while True:
            ret, frame = cam.read()
            if not ret:
                break
            cv2.imshow("Capture Face", frame)
            key = cv2.waitKey(1) & 0xff
            if key in (ord('q'), ord('Q')):
                break
            if key == 32:  # SPACE
                path = os.path.join(KNOWN_FACES_DIR, f"{sid}.jpg")
                cv2.imwrite(path, frame)
                messagebox.showinfo("Saved", f"Saved face to: {path}")
                break
        cam.release()
        cv2.destroyAllWindows()

        self.load_students()
        self.clear_form()

    def update_student(self):
        sid = self.entry_id.get().strip()
        if not get_student_by_id(sid):
            messagebox.showerror("Error", "Student not found.")
            return
        name = self.entries['Name'].get().strip()
        faculty = self.entries['Faculty'].get().strip()
        email = self.entries['Email'].get().strip()
        address = self.entries['Address'].get().strip()
        dob = self.entries['DOB'].get().strip()

        add_student(sid, name, faculty, dob, email, address)
        self.load_students()
        messagebox.showinfo("Updated", f"Student {sid} updated.")

    def delete_selected_student(self):
        sel = self.student_table.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a student to delete.")
            return
        vals = self.student_table.item(sel[0], "values")
        sid, name = vals[0], vals[1]
        if not messagebox.askyesno("Confirm", f"Delete {name} (ID: {sid})?"):
            return
        if delete_student_by_id(sid):
            self.load_students()
            self.clear_form()
            messagebox.showinfo("Deleted", f"Student {name} removed.")
        else:
            messagebox.showerror("Error", "Failed to delete.")

    def load_attendance(self):
        for i in self.attendance_table.get_children():
            self.attendance_table.delete(i)
        attendance_records = get_attendance()
        for rec in attendance_records:
            values = (
                rec.get('student_id', ''),
                rec.get('name', ''),
                rec.get('date', ''),
                rec.get('time', '')
            )
            self.attendance_table.insert("", "end", iid=rec.get('id'), values=values)

    def delete_selected_attendance(self):
        sel = self.attendance_table.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select an attendance row to delete.")
            return
        att_id = sel[0]
        if not messagebox.askyesno("Confirm", f"Delete attendance record? (ID: {att_id})"): 
            return

        if delete_attendance_by_id(att_id):
            self.load_attendance()
            messagebox.showinfo("Deleted", "Attendance deleted.")
        else:
            messagebox.showerror("Error", "Record not found.")

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

        cam_window = tk.Toplevel(self.master)
        cam_window.title("Live Attendance Camera")
        cam_window.geometry("900x700")
        cam_window.configure(bg=self.colors["dark_bg"])

        video_frame = ttk.Frame(cam_window, style="Card.TFrame")
        video_frame.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(video_frame, text="Live Attendance", background=self.colors["card"], fg=self.colors["text"],
                 font=("Segoe UI", 16, "bold")).pack(pady=10)

        cam_label = tk.Label(video_frame, bg="#000")
        cam_label.pack(padx=10, pady=10, fill="both", expand=True)

        status_label = tk.Label(video_frame, text="", background=self.colors["card"], fg=self.colors["green"],
                                font=("Segoe UI", 12, "bold"))
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
