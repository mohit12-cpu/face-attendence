import tkinter as tk

# Import the UI module (database import is handled within the module)
try:
    from student_attendance_ui import FancyApp
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please make sure all dependencies are installed.")
    exit(1)

if __name__ == '__main__':
    root = tk.Tk()
    app = FancyApp(root)
    root.mainloop()
