from Screen import get_screen_dimensions
from Practitioner import Practitioner
import tkinter as tk
from Graph import total_cholesterol_graph

# This function destroy the information window when user is logging out.
def destroy_info_window(logged_in, info_window):
    if logged_in:
        info_window.destroy()


def failed_login(window):
    """
    Adds a message to login window explaining to user the login attempt failed
    :param window: The window we display this message on
    """
    relogin_text = "Login attempt failed, please try again with your ID or Practitioner Identifier (NPI)."
    Fail_login_label = tk.Label(window, text=relogin_text)
    Fail_login_label.pack()


def login_callback(window, entry,systolic_bp_entry, diastolic_bp_entry):
    """
    Checks whether login is valid before proceeding to info_window
    :param window: the login window screen
    :param entry: the user entered id or identifier
    :param systolic_bp_entry: the user entered systolic limit
    :param diastolic_bp_entry: the user entered diastolic limit
    """

    if len(systolic_bp_entry.get()) == 0:
        systolic_lim = 120
    else:
        try:
            systolic_lim = int(systolic_bp_entry.get())
        except:
            systolic_lim = 120

    if len(diastolic_bp_entry.get()) == 0:
        diastolic_lim = 80
    else:
        try:
            diastolic_lim = int(diastolic_bp_entry.get())
        except:
            diastolic_lim = 80

    practitioner = Practitioner(entry.get())
    if not practitioner.is_logged_in():
        failed_login(window)
    else:
        create_info_window(window, practitioner,systolic_lim,diastolic_lim)


def set_login_window():
    """
    First window, shows text box for user to enter practitioner id or npi identifier
    :return:
    """
    window = tk.Tk()
    window.title("Health Practitioner Database")

    x, y = get_screen_dimensions()
    window.geometry('%dx%d+%d+%d' % (x, y, x / 2, y / 2))  # Draw 1/2 Screen Size @ Centered

    frame_entry = tk.Frame()
    label_entry = tk.Label(master=frame_entry, text="Practitioner ID / Identifier")
    label_entry.pack()
    entry = tk.Entry(master=frame_entry)
    entry.pack()

    systolic_bp_label = tk.Label(master=frame_entry, text="systolic blood pressure limit (Default to 120 mm[Hg])")
    systolic_bp_label.pack()
    systolic_bp_entry = tk.Entry(master=frame_entry)
    systolic_bp_entry.pack()

    diastolic_bp_label = tk.Label(master=frame_entry, text="diastolic blood pressure limit (Default to 80 mm[Hg])")
    diastolic_bp_label.pack()
    diastolic_bp_entry = tk.Entry(master=frame_entry)
    diastolic_bp_entry.pack()

    frame_entry.pack()

    button = tk.Button(text="Login", width=5, height=2, bg="blue", fg="yellow",
                       command=lambda: login_callback(window, entry,systolic_bp_entry,diastolic_bp_entry))
    button.place(relx=0.5, rely=0.5, anchor="center")

    window.mainloop()



def create_info_window(window, practitioner,systolic_lim,diastolic_lim):
    """

    :param window: The previous log in window
    :param practitioner: The logged in practitioner
    :param systolic_lim: Systolic blood pressure limit set by user
    :param diastolic_lim: Diastolic blood pressure limit set by user
    :return:
    """
    window.destroy()

    info_window = tk.Tk()

    info_window.title("Health Practitioner Database")

    # Draw 1/2 Screen Size @ Centered
    x, y = get_screen_dimensions()
    info_window.geometry('%dx%d+%d+%d' % (x, y, x / 2, y / 2))

    logged_in = True

    selection_button_frame = tk.Frame(info_window)
    graph_frame = tk.Frame(info_window)
    output_frame = tk.Frame(info_window)

    selection_button_frame.grid(row=0,column=0)
    graph_frame.grid(row=0,column=1)
    output_frame.grid(row=1,columnspan=2)

    welcome_message = "\nWelcome " + practitioner.fullname() + "\n"
    limit_message= "Diastolic limit: "+ str(diastolic_lim) + "mm[Hg]"+ "   " + " Systolic limit: "+str(systolic_lim) +"mm[Hg]"+"\n"
    label_entry = tk.Label(selection_button_frame, text=welcome_message)
    label_entry.grid(row=0,column=0)

    limit_label = tk.Label(selection_button_frame, text=limit_message, bg='black', fg='yellow')
    limit_label.grid(row=1, column=0, sticky='w')

    button_pressed = tk.IntVar()

    out_button = tk.Button(selection_button_frame, text="Logout", width=10, height=2, bg="blue", fg="yellow",
                           command=lambda: [destroy_info_window(logged_in, info_window), set_login_window()])
    out_button.grid(row=1,column=0,sticky='e')

    # Add Patient Feature
    label_entry = tk.Label(master=selection_button_frame, text="Patient ID:")
    label_entry.grid(row=2,column=0,sticky='w')
    entry = tk.Entry(master=selection_button_frame)
    entry.grid(row=2, column=0)

    add_button_pressed = tk.IntVar()

    add_patient_button = tk.Button(selection_button_frame, text="Add Patient ID", width=15, height=2, bg="green", fg="yellow",
                                   command=lambda: [add_patient_refresh(info_window, practitioner, entry.get(),systolic_lim,diastolic_lim)])

    add_patient_button.grid(row=2, column=0,sticky='e')

    lb_label = tk.Label(selection_button_frame, bg='grey', width=60, text=" ID     Name        Surname      Cholesterol    "
                                                               "Diastolic Blood    Systolic Blood")
    lb_label.grid(row=3, column=0, sticky='e')

    empty_label = tk.Label(selection_button_frame, fg='red', width=50, text="No patient information available")
    if len(practitioner.get_patient_list()) < 1:
        empty_label.grid(row=4, column=0, sticky='e')
    else:
        empty_label.destroy()

    patient_lb = tk.Listbox(selection_button_frame)
    for patient_id in practitioner.get_patient_list():
        patient_name = practitioner.get_patient(patient_id).get_fullname()
        if practitioner.get_patient(patient_id).has_cholesterol():
            cholesterol = practitioner.get_patient(patient_id).cholesterol_latest()[1]

            if practitioner.get_patient(patient_id).has_blood():
                diastolic_blood = practitioner.get_patient(patient_id).blood_latest()[0][1]
                systolic_blood = practitioner.get_patient(patient_id).blood_latest()[1][1]
            else:
                diastolic_blood = "    -    "
                systolic_blood = "    -    "

            patient = [patient_id, patient_name, str(cholesterol) + " mg/dL",
                       str(diastolic_blood) + " mm[Hg]", str(systolic_blood) + " mm[Hg]"]
            patient_lb.insert('end', tuple(patient))
        elif practitioner.get_patient(patient_id).has_blood():

            diastolic_blood = practitioner.get_patient(patient_id).blood_latest()[0][1]
            systolic_blood = practitioner.get_patient(patient_id).blood_latest()[1][1]

            cholesterol = "    -    "

            patient = [patient_id, patient_name, str(cholesterol) + " mg/dL",
                       str(diastolic_blood) + " mm[Hg]", str(systolic_blood) + " mm[Hg]"]
            patient_lb.insert('end', tuple(patient))

    # TODO: Mark above average cholesterol as red
    cholesterol_average = practitioner.cholesterol_average()
    i = 0
    for patient_id in practitioner.get_patient_list():
        if practitioner.get_patient(patient_id).cholesterol_latest():
            if float(practitioner.get_patient(patient_id).cholesterol_latest()[1]) > cholesterol_average:
                patient_lb.itemconfigure(i, {'fg': 'red'})
            else:
                patient_lb.itemconfigure(i, {'fg': 'black'})
        i += 1

    # # TODO: Mark above average blood as purple
    # blood_average = practitioner.blood_average()
    # i = 0
    # for patient_id in practitioner.get_patient_list():
    #     if practitioner.get_patient(patient_id).blood_latest():
    #         if float(practitioner.get_patient(patient_id).blood_latest()[0][1]) > blood_average[0]:
    #             patient_lb.itemconfigure(i, {'fg': 'purple'})
    #         else:
    #             patient_lb.itemconfigure(i, {'fg': 'black'})
    #
    #         if float(practitioner.get_patient(patient_id).blood_latest()[1][1]) > blood_average[1]:
    #             patient_lb.itemconfigure(i, {'fg': 'purple'})
    #         else:
    #             patient_lb.itemconfigure(i, {'fg': 'black'})
    #
    #     i += 1

    patient_lb.config(width=0, height=0)
    patient_lb.grid(row=4,column=0,sticky='n')


    cholesterol_graph = total_cholesterol_graph(graph_frame,practitioner)
    cholesterol_graph.grid()

    detail_text = tk.Text(output_frame, height='8')
    history_text = tk.Text(output_frame, height='13')
    blood_pressure_text = tk.Text(output_frame, height='5')

    history_button = tk.Button(selection_button_frame, text='Show patient detail', width=15, height=2, command=lambda: [
            show_patient_cholesterol_history(history_text, practitioner, patient_lb.get(patient_lb.curselection())[0]),
            show_patient_detail(detail_text, practitioner, patient_lb.get(patient_lb.curselection())[0])])
    history_button.grid(row=5,column=0,sticky='wn')

    blood_pressure_button = tk.Button(selection_button_frame, text='Show blood pressure', width=15, height=2, command=lambda :[
            show_patient_bp(blood_pressure_text,practitioner,systolic_lim,diastolic_lim,patient_lb.get(patient_lb.curselection())[0])])
    blood_pressure_button.grid(row=5,column=0,sticky='n')

    remove_button_pressed = tk.IntVar()

    remove_patient_button = tk.Button(selection_button_frame, text="Remove Patient ID", width=15, height=2, bg="green", fg="yellow",
                    command=lambda: [remove_patient_refresh(info_window, practitioner, patient_lb.get(patient_lb.curselection())[0],systolic_lim,diastolic_lim)])


    remove_patient_button.grid(row=5,column=0,sticky='en')

    history_text.grid(row=0, column=0,sticky='n')
    detail_text.grid(row=0, column=1,sticky='n')
    blood_pressure_text.grid(row=0, column=1,sticky='s')

    while logged_in:
        print("\nWaiting for user input...")
        out_button.wait_variable(button_pressed)  # Hold until Button is pressed
        # history_button.wait_variable(button_pressed)
        add_patient_button.wait_variable(add_button_pressed)
        remove_patient_button.wait_variable(remove_button_pressed)
        window.destroy()
        main()
    info_window.mainloop()


#Collection of functions called when different buttons are clicked

def add_patient_refresh(window, practitioner, patient_id, sys_lim, dia_lim):
    """

    :param window: the information window
    :param practitioner: practitioner who logged in
    :param patient_id: the new added patient's id
    :return:
    """
    practitioner.add_patient(patient_id)
    create_info_window(window, practitioner,sys_lim, dia_lim)

def remove_patient_refresh(window, practitioner, patient_id,sys_lim,dia_lim):
    """

    :param window: the info window
    :param practitioner: practitioner who logged in
    :param patient_id: the removing patient's id
    :return:
    """
    practitioner.remove_patient(patient_id)
    create_info_window(window, practitioner,sys_lim,dia_lim)

def show_patient_detail(detail_text, practitioner, patient_id):
    """

    :param detail_text: text section that display the details of patient
    :param practitioner: the logged in practitioner
    :param patient_id: the monitoring patient's id
    :return:
    """
    detail_text.delete('1.0','end')

    patient = practitioner.get_patient(patient_id)

    detail_text.insert('end', "Patient Details: \n")
    detail_text.insert('end', 'Name: ' + patient.get_fullname().title() + "\n")
    detail_text.insert('end', 'Gender: ' + patient.get_gender().title() + "\n")
    detail_text.insert('end', 'Birth Date: ' + patient.get_birth_date() + "\n")
    detail_text.insert('end', 'Address: ' + patient.get_address() + "\n")

def show_patient_bp(text,practitioner,systolic_lim,diastolic_lim,patient_id):
    """

    :param text: the text section displaying blood pressure of patient
    :param practitioner: the logged in practitioner
    :param systolic_lim: the set systolic blood pressure limit
    :param diastolic_lim: the set diastolic blood pressure limit
    :param patient_id: the monitoring patient's id
    :return:
    """
    text.delete('1.0','end')

    patient = practitioner.get_patient(patient_id)

    text.insert('end',patient.get_fullname() + "'s latest blood pressure measurement: \n")
    if not patient.has_blood():
        text.insert('end', "No blood pressure measurement for this patient!")
    else:
        sys_list = patient.systolic_latest()
        sys_measurement = float(sys_list[1])
        sys_date = sys_list[0]
        sys_unit = sys_list[2]

        text.insert('end', "Systolic blood pressure: ")
        text.insert('end', str(sys_measurement)  +" " + sys_unit + " " + str(sys_date) + "\n")
        if sys_measurement > systolic_lim:
            text.tag_add('sys','2.26','2.100')
            text.tag_configure('sys',foreground='blue')


        dia_list = patient.diastolic_latest()
        dia_measurement = float(dia_list[1])
        dia_date = dia_list[0]
        dia_unit = dia_list[2]

        text.insert('end', "Diastolic blood pressure: ")
        text.insert('end', str(dia_measurement) + " " + dia_unit + " " + str(dia_date) + "\n")
        if dia_measurement > diastolic_lim:
            text.tag_add('dia','3.26','3.100')
            text.tag_configure('dia',foreground='blue')

def show_patient_cholesterol_history(history_text, practitioner, patient_id):
    """

    :param history_text: the text section displaying historical cholesterol measurement of patient
    :param practitioner: the logged in practitioner
    :param patient_id: the monitoring patient's id
    :return:
    """
    history_text.delete('1.0','end')

    patient = practitioner.get_patient(patient_id)

    history_text.insert('end', patient.get_fullname() + "'s Cholesterol Measurement History: \n")
    history_text.insert('end', "   Patient        Cholesterol        Date    \n")

    latest_date = practitioner.get_patient(patient_id).cholesterol_latest()[0]

    index = 2

    for i in range(len(patient.cholesterol_array)):

        entry = patient.cholesterol_array[i]

        text = "    " + patient.id + "    " + entry[1] + " mg/dL    " + entry[0].strftime("%m/%d/%Y")
        history_text.insert('end', str(text) + "    ")
        history_text.insert('end', "\n")
        index += 1

        if entry[0] == latest_date:
            start_index = str(index) + '.0'
            end_index = str(index) + '.100'
            history_text.tag_add('latest', start_index, end_index)
            history_text.tag_configure('latest', foreground='red')


def main():
    # Create and set the login window
    set_login_window()


if __name__ == "__main__":
    main()
