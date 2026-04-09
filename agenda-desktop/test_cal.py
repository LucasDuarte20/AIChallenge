try:
    import tkinter as tk
    from tkcalendar import Calendar
    root = tk.Tk()
    cal = Calendar(root, locale='es_ES')
    print("Calendar initialized successfully")
except Exception as e:
    print(f"Error: {e}")
