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
        if self.window is not None:
            try:
                self.window.destroy()
            except tk.TclError:
                pass

        self.window = tk.Tk()

