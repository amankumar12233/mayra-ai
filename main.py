"""Aarohi AI (Aaru) desktop application entry point."""

import tkinter as tk
from tkinter import messagebox

from config import ensure_user_directories


def main():
    root = tk.Tk()
    try:
        ensure_user_directories()
        from dashboard.main_window import AaruDashboard

        AaruDashboard(root)
    except Exception as exc:
        root.withdraw()
        messagebox.showerror("Aarohi AI could not start", str(exc), parent=root)
        root.destroy()
        raise
    root.mainloop()


if __name__ == "__main__":
    main()
