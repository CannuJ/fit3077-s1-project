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
            patient = self.practitioner.get_patient(id
                                                    )
            row = int(i/3)
            column = int(i%3)

            frame = tk.Frame(self.window)
            frame.grid(row=row, column=column)


            full_bp_array = patient.blood_array["Systolic Blood Pressure"].copy()

            history_text = "Last five systolic blood pressure history for " + patient.get_fullname() + "\n"
            value_list = []
            unit_list = []
            date_list = []

            for i in range(5):
                latest = full_bp_array.pop(full_bp_array.index(max(full_bp_array)))
                value = str(latest[1])
                unit = str(latest[2])
                date = str(latest[0])
                value_list.insert(0,value)
                unit_list.insert(0,unit)
                date_list.insert(0,date)

            for j in range(5):
                history_text += value_list[j] + " " + unit_list[j] + " " + date_list[j]
                if j != 4:
                    history_text += "\n"

            history_label = tk.Label(master=frame, text=history_text, bg='grey', fg='white')
            history_label.grid()


            blood_pressure_history_graph(frame,self.practitioner,id)