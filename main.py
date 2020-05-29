from Screen import get_screen_dimensions
from Practitioner import Practitioner
import tkinter as tk


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


def login_callback(window, entry):
    """
    Checks whether login is valid before proceeding to info_window
    :param window: the login window screen
    :param entry: the user entered id or identifier
    """
    practitioner = Practitioner(entry.get())
    if not practitioner.is_logged_in():
        failed_login(window)
    else:
        create_info_window(window, practitioner)


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
    frame_entry.pack()

    button = tk.Button(text="Login", width=5, height=2, bg="blue", fg="yellow",
                       command=lambda: login_callback(window, entry))
    button.place(relx=0.5, rely=0.5, anchor="center")

    window.mainloop()


# This function create the information window to show data associated to the user
# identification
def create_info_window(window, practitioner):

    window.destroy()

    info_window = tk.Tk()

    info_window.title("Health Practitioner Database")

    # Draw 1/2 Screen Size @ Centered
    x, y = get_screen_dimensions()
    info_window.geometry('%dx%d+%d+%d' % (x, y, x / 2, y / 2))

    logged_in = True

    welcome_message = "\nWelcome " + practitioner.fullname() + "\n"
    label_entry = tk.Label(info_window, text=welcome_message)
    label_entry.pack()

    button_pressed = tk.IntVar()

    out_button = tk.Button(info_window, text="Logout", width=10, height=2, bg="blue", fg="yellow",
                           command=lambda: [destroy_info_window(logged_in, info_window), set_login_window()])
    out_button.pack()

    # Add Patient Feature
    frame_entry = tk.Frame()
    label_entry = tk.Label(master=frame_entry, text="Patient ID")
    label_entry.pack()
    entry = tk.Entry(master=frame_entry)
    entry.pack()
    frame_entry.pack()

    add_button_pressed = tk.IntVar()

    add_patient_button = tk.Button(info_window, text="Add Patient ID", width=15, height=2, bg="green", fg="yellow",
                                   command=lambda: [add_patient_refresh(info_window, practitioner, entry.get())])

    add_patient_button.pack()

    lb_label = tk.Label(info_window, bg='grey', width=60, text=" ID     Name        Surname      Cholesterol    "
                                                               "Diastolic Blood    Systolic Blood")
    lb_label.pack()

    empty_label = tk.Label(info_window, fg='red', width=50, text="No patient information available")
    if len(practitioner.get_patient_list()) < 1:
        empty_label.pack()
    else:
        empty_label.destroy()

    patient_lb = tk.Listbox(info_window)
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

    patient_lb.pack()

    history_text = tk.Text(info_window, height='6')
    detail_text = tk.Text(info_window, height='5')

    history_button = tk.Button(info_window, text='Show patient detail', width=15, height=2, command=lambda: [
            show_patient_history(history_text, practitioner, patient_lb.get(patient_lb.curselection())[0]),
            show_patient_detail(detail_text, practitioner, patient_lb.get(patient_lb.curselection())[0])])
    history_button.pack()

    remove_button_pressed = tk.IntVar()

    remove_patient_button = tk.Button(info_window, text="Remove Patient ID", width=15, height=2, bg="green", fg="yellow",
                    command=lambda: [remove_patient_refresh(info_window, practitioner, patient_lb.get(patient_lb.curselection())[0])])

    remove_patient_button.pack()

    history_text.pack()
    detail_text.pack()

    while logged_in:
        print("\nWaiting for user input...")
        out_button.wait_variable(button_pressed)  # Hold until Button is pressed
        # history_button.wait_variable(button_pressed)
        add_patient_button.wait_variable(add_button_pressed)
        remove_patient_button.wait_variable(remove_button_pressed)
        window.destroy()
        main()
    info_window.mainloop()


def add_patient_refresh(window, practitioner, patient_id):
    practitioner.add_patient(patient_id)
    create_info_window(window, practitioner)


def remove_patient_refresh(window, practitioner, patient_id):
    practitioner.remove_patient(patient_id)
    create_info_window(window, practitioner)


def show_patient_detail(detail_text, practitioner, patient_id):
    detail_text.delete('1.0', tk.END)

    patient = practitioner.get_patient(patient_id)

    detail_text.insert('end', "Patient Details: \n")
    detail_text.insert('end', 'Name: ' + patient.get_fullname().title() + "\n")
    detail_text.insert('end', 'Gender: ' + patient.get_gender().title() + "\n")
    detail_text.insert('end', 'Birth Date: ' + patient.get_birth_date() + "\n")
    detail_text.insert('end', 'Address: ' + patient.get_address() + "\n")


def show_patient_history(history_text, practitioner, patient_id):
    history_text.delete('1.0', tk.END)

    patient = practitioner.get_patient(patient_id)

    history_text.insert('end', "Patient History: \n")
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
