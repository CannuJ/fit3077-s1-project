from Screen import get_screen_dimensions
from Practitioner import Practitioner
import tkinter as tk
from Graph import blood_pressure_history_graph

class Bp_monitor_window:
    def __init__(self,practitioner):
        self.practitioner = practitioner
        self.monitoring_array = practitioner.patient_bp_monitor_id_array

        self.window = None

    def create_window(self):
        self.window = self.window
        if self.window is not None:
            try:
                self.window.destroy()
            except tk.TclError:
                pass

        self.window = tk.Tk()
        self.window.title("Blood pressure monitor")
        # Draw 1/2 Screen Size @ Centered
        x, y = get_screen_dimensions()
        self.window.geometry('%dx%d+%d+%d' % (x, y, x / 2, y / 2))

        monitoring_list = self.practitioner.patient_bp_monitor_id_array

        for i in range(len(monitoring_list)):
            id = monitoring_list[i]
            row = int(i/3)
            column = int(i%3)

            frame = tk.Frame(self.window)
            frame.grid(row=row, column=column)
            blood_pressure_history_graph(frame,self.practitioner,id)





