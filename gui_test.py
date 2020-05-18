import requests
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from PyQt5 import QtWidgets
import sys
import os
from dateutil.parser import parse

root_url = 'https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/'  # Root URL
npi_url = "http://hl7.org/fhir/sid/us-npi"


def get_screen_dimensions():
    """
    Grabs the user's screen dimensions and calculates draw space for app window
    :return: x and y coordinates to draw window in middle of screen
    """
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    screen_width, screen_height = screen.size().width(), screen.size().height()

    return screen_width / 2, screen_height / 2


def on_closing(ui):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        ui.destroy()


# This function take the encounter list as input and go through every encounters in the list
# then generate a patient list with all latest value and data for each patient
def get_patient_list(encounter_list):
    patient_list = []
    current_patient = encounter_list[2]
    for i in range(2, len(encounter_list)):
        if encounter_list[i] == []:
            patient_list.append(current_patient)
            if i + 1 > len(encounter_list):
                break
            elif encounter_list[i + 1] != []:
                current_patient = encounter_list[i + 1]
            else:
                break
        elif parse(encounter_list[i][2]) >= parse(current_patient[2]):
            current_patient = encounter_list[i]

    return patient_list


def login(user_login):
    """
    Takes the user input identifier or practitioner id and attempts to match a practitioner profile within the fhir api
    :param user_login: The login the user enters to access their data from the fhir api
    :return: A valid identifier value and name of practitioner or False if failed
    """
    identifier_url = root_url + "Encounter?participant.identifier=" + npi_url + "|" + \
                     user_login + "&_include=Encounter.participant.individual&_include=Encounter.patient"
    data = requests.get(url=identifier_url).json()

    try:  # Assume input is an Identifier, if this fails, fallback onto Practitioner ID
        practitioner_url = root_url + str(data['entry'][0]['resource']['participant'][0]['individual']['reference'])
    except KeyError:  # Invalid Practitioner ID, try assumption user_login is Identifier
        practitioner_url = root_url + "Practitioner/" + user_login

    data = requests.get(url=practitioner_url).json()

    try:
        if data['issue'][0]['severity'] == "error":  # Failed Login
            return False, False
    except KeyError:  # Successful Login
        pass

    for i in range(len(data['identifier'])):
        if data['identifier'][i]['system'] == npi_url:
            identifier_value = data['identifier'][i]['value']
            fullname = str(data['name'][0]['prefix'][0]) + " " + str(data['name'][0]['given'][0]) + " " + \
                       str(data['name'][0]['family'])
            return identifier_value, fullname

    return False, False


def get_all_patient_data(identifier):
    """
    Takes the user identifier determined from logging in,
    and returns a list of encounters associated to that identifier
    :param identifier: the identifier that references the practitioner in question
    :return: a list of encounters associated to the identifier
    """
    encounters_url = root_url + "Encounter?participant.identifier=" + npi_url + "|" + identifier + \
                     "&_include=Encounter.participant.individual&_include=Encounter.patient"
    all_encounters_practitioner = requests.get(url=encounters_url).json()
    try:
        all_encounter_data = all_encounters_practitioner['entry']
    except KeyError:  # Was not a valid Identifier
        return False

    next_url = ""  # Test
    iterator = 0

    patient_list = []
    processed_patient_id = []  # We don't want to process the same Patient

    cholesterol_data_array = [['  Patient  ', '  Cholesterol  ', '    Date    ']]  # Header

    while next_url is not None:

        iterator += 1
        try:  # Large encounter bundles take a while to process, uncomment to get an idea how long to go
            parsed_entries = iterator * 50
            total = all_encounters_practitioner['total']
            if int(parsed_entries) < int(total):
                print("Parsed " + str(parsed_entries) + "/" + str(total) + " entries")
            else:
                print("Parsed " + str(total) + "/" + str(total) + " entries")
        except KeyError:
            parsed_entries = iterator * 50
            print("Parsed " + str(parsed_entries) + " entries")
            pass

        found_next_url = False
        for link in all_encounters_practitioner['link']:  # Grabs url for next 50 entries
            if link['relation'] == 'next':
                next_url = link['url']
                found_next_url = True
        if found_next_url is False:
            next_url = None

        for entry in all_encounter_data:
            patient = entry['resource']['subject']['reference']
            patient_id = patient.split('/')[1]
            if patient_id in processed_patient_id:  # Duplicate Patient_ID, Ignore ID
                continue
            cholesterol_data_array.append([])  # Acts as break between different patients
            processed_patient_id.append(patient_id)
            patient_list.append(patient)
            find_cholesterol_url = root_url + "Observation?patient=" + patient_id + "&code=2093-3&_sort=date&_count=13"
            patient_cholesterol = requests.get(url=find_cholesterol_url).json()
            try:
                cholesterol_data = patient_cholesterol['entry']
                for entry2 in cholesterol_data:  # For each Cholesterol Record of Patient
                    record = []
                    item = entry2['resource']
                    cholesterol_value = str(item['valueQuantity']['value'])
                    issued = item['issued'][:len('2008-10-14')]
                    date = datetime.strptime(issued, '%Y-%m-%d').date()
                    aus_date_format = str(date.day) + '-' + str(date.month) + '-' + str(date.year)
                    record.append("{:>11}".format(patient_id))
                    record.append("{:>14}".format(cholesterol_value + " mg/L"))
                    record.append("{:>13}".format(aus_date_format))
                    cholesterol_data_array.append(record)  # Append all 3 Values to Array
            except KeyError:  # No Cholesterol Data
                continue

        if next_url is not None:
            all_encounters_practitioner = requests.get(url=next_url).json()  # GET with next url

    return cholesterol_data_array


# This function create the login window allow user to input the user identification
def set_login_window():
    window = tk.Tk()
    window.title("Health Practitioner Database")

    # Draw 1/2 Screen Size @ Centered
    x, y = get_screen_dimensions()
    window.geometry('%dx%d+%d+%d' % (x, y, x / 2, y / 2))

    frame_entry = tk.Frame()

    label_entry = tk.Label(master=frame_entry, text="Practitioner ID / Identifier")
    label_entry.pack()

    frame_entry.pack()

    entry = tk.Entry(master=frame_entry)
    entry.pack()

    button = tk.Button(
        text="Login",
        width=5,
        height=2,
        bg="blue",
        fg="yellow",
        command=lambda: create_info_window(window, entry)
    )

    # button.pack(side="top")
    # button.place(bordermode="outside", height=y/9, width=x/6, x=x/2.5, y=y/2.5)
    button.place(relx=0.5, rely=0.5, anchor="center")
    # window.protocol("WM_DELETE_WINDOW", on_closing(window))
    window.mainloop()


# This function create the information window to show data associated to the user
# identification
def create_info_window(window, entry):
    input = entry.get()

    window.destroy()

    info_window = tk.Tk()

    info_window.title("Health Practitioner Database")

    # Draw 1/2 Screen Size @ Centered
    x, y = get_screen_dimensions()
    info_window.geometry('%dx%d+%d+%d' % (x, y, x / 2, y / 2))

    user_login, fullname = login(input)

    welcome_message = "\nWelcome " + str(fullname) + "\n"
    label_entry = tk.Label(info_window, text=welcome_message)
    label_entry.pack()

    cholesterol = get_all_patient_data(user_login)

    if cholesterol is False:
        main()

    logged_in = True

    button_pressed = tk.IntVar()

    out_button = tk.Button(
        info_window,
        text="Logout",
        width=5,
        height=2,
        bg="blue",
        fg="yellow",
        command=lambda: [destroy_info_window(logged_in, info_window), set_login_window()]
    )

    out_button.pack()

    lb_label = tk.Label(info_window, bg='grey', width=40, text=" ID     Name        Surname    ")
    lb_label.pack()

    patient_lb = tk.Listbox(info_window)

    if len(cholesterol) > 2:

        patient_list = get_patient_list(cholesterol)

        for patient in patient_list:
            patient_ID = str(int(patient[0]))
            patient_URL = root_url + "Patient" + "/" + patient_ID

            data = requests.get(url=patient_URL).json()

            patient_name = str(data['name'][0]['prefix'][0]) + str(data['name'][0]['given'][0]) + " " + str(
                data['name'][0]['family'])
            patient = [patient_ID, patient_name]
            patient_lb.insert('end', tuple(patient))

        for i in range(len(patient_list)):
            patient_lb.itemconfigure(i, {'fg': 'red'})

    patient_lb.config(width=0, height=0)

    patient_lb.pack()

    history_text = tk.Text(info_window, height='6')
    detail_text = tk.Text(info_window, height='5')

    history_button = tk.Button(info_window, text='Show patient detail', width=15,
                               height=2, command=lambda: [show_patient_history(history_text, cholesterol, patient_lb),
                                                          show_patient_detail(detail_text, cholesterol, patient_lb)])
    history_button.pack()

    history_text.pack()
    detail_text.pack()

    while logged_in:
        print("\nWaiting for user input...")
        out_button.wait_variable(button_pressed)  # Hold until Button is pressed
        history_button.wait_variable(button_pressed)
        window.destroy()
        main()
    # info_window.protocol("WM_DELETE_WINDOW", on_closing(info_window))
    info_window.mainloop()


# This function taks the encounter list, patienn list box and history text in the infomation
# window to output the other history value for the selected patient in the list box in the text space.
def show_patient_history(history_text, encounter_list, patient_lb):
    history_text.delete('1.0', tk.END)

    history_text.insert('end', "Patient history: \n")
    history_text.insert('end', "   Patient        Cholestrol        Date    \n")

    patient = patient_lb.get(patient_lb.curselection())

    for e in encounter_list:
        if len(e) == 3:
            if e[0].strip(" ") == patient[0]:
                for item in e:
                    history_text.insert('end', str(item) + "    ")
                history_text.insert('end', "\n")


# This function taks the encounter list, patienn list box and history text in the infomation
# window to output the patient details for the selected patient in the list box in the text space.
def show_patient_detail(detail_text, cholesterol, patient_lb):
    detail_text.delete('1.0', tk.END)

    patient = patient_lb.get(patient_lb.curselection())

    detail_text.insert('end', "Patient details: \n")

    patient_ID = str(int(patient[0]))

    patient_URL = root_url + "Patient" + "/" + patient_ID

    data = requests.get(url=patient_URL).json()

    patient_name = str(data['name'][0]['prefix'][0]) + str(data['name'][0]['given'][0]) + " " + str(
        data['name'][0]['family'])

    patient_address = str(data['address'][0]['line'][0]) + " " + str(data['address'][0]['city']) + " " + str(
        data['address'][0]['state']) + " " + str(data['address'][0]['country'])

    patient_gender = str(data['gender'])

    patient_birthdate = str(data['birthDate'])

    detail_text.insert('end', 'Name: ' + patient_name + "\n")
    detail_text.insert('end', 'Gender: ' + patient_gender + "\n")
    detail_text.insert('end', 'Birth Date: ' + patient_birthdate + "\n")
    detail_text.insert('end', 'Address: ' + patient_address + "\n")


# This function destroy the information window when user is logging out.
def destroy_info_window(logged_in, info_window):
    if logged_in:
        info_window.destroy()


def main():
    # Create and set the login window
    set_login_window()


if __name__ == "__main__":
    main()
