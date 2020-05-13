import requests
import pandas as pd
from datetime import datetime
import tkinter as tk
from PyQt5 import QtWidgets
import sys
import os
from dateutil.parser import parse


root_url = 'https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/'  # Root URL
npi_url = "http://hl7.org/fhir/sid/us-npi"


def get_screen_dimensions():

    app = QtWidgets.QApplication(sys.argv)

    screen = app.primaryScreen()
    size = screen.size()
    screen_width = size.width()
    screen_height = size.height()

    x = screen_width/2
    y = screen_height/2

    return x, y

def get_patient_list(encounter_list):
    patient_list = []
    current_patient = encounter_list[2]
    for i in range(2,len(encounter_list)):
        if encounter_list[i] == []:
            patient_list.append(current_patient)
            if i+1 > len(encounter_list):
                break
            elif encounter_list[i+1] != []:
                current_patient = encounter_list[i+1]
            else:
                break
        elif parse(encounter_list[i][2]) >= parse(current_patient[2]):
            current_patient = encounter_list[i]

    return patient_list

def login(user_login):

    identifier_url = root_url + "Encounter?participant.identifier=" + npi_url + "|" + \
                     user_login + "&_include=Encounter.participant.individual&_include=Encounter.patient"

    data = requests.get(url=identifier_url).json()  # "\nAttempting Identifier Login from: " + identifier_url + "\n"

    # Assume input is an Identifier, if this fails, fallback onto Practitioner ID
    try:  # Found " + str(data['entry'][0]['resource']['participant'][0]['individual']['reference']
        practitioner_url = root_url + str(data['entry'][0]['resource']['participant'][0]['individual']['reference'])
    except KeyError:  # Invalid Practitioner ID, perhaps this is an Identifier
        practitioner_url = root_url + "Practitioner/" + user_login

    data = requests.get(url=practitioner_url).json()  # "\nAttempting Practitioner ID Login from: " + practitioner_url"

    try:
        if data['issue'][0]['severity'] == "error":  # "\nFailed Login!\n"
            return False, False
    except KeyError:  # "\nSuccess!"
        pass

    for i in range(len(data['identifier'])):

        if data['identifier'][i]['system'] == npi_url:
            identifier_value = data['identifier'][i]['value']

            fullname = str(data['name'][0]['prefix'][0]) + " " + str(data['name'][0]['given'][0]) + " " + \
                       str(data['name'][0]['family'])

    return identifier_value, fullname

def get_all_patient_data(identifier):
    encounters_url = root_url + "Encounter?participant.identifier=" + npi_url + "|" + identifier + \
                     "&_include=Encounter.participant.individual&_include=Encounter.patient"

    all_encouters_practitioner = requests.get(url=encounters_url).json()  # "\nPulling Patient Information"
    try:
        all_encouters_practitioner['entry']
    except KeyError:  # print("Invalid Identifier, returning to login\n")
        return False

    all_encouter_data = all_encouters_practitioner['entry']

    patient_list = []
    processed_patient_id = []  # We don't want to process the same Patient

    cholesterol_data = [['  Patient  ', '  Cholestrol  ', '    Date    ']]  # Header

    for entry in all_encouter_data:
        item = entry['resource']
        patient = item['subject']['reference']
        patient_id = patient.split('/')[1]
        if patient_id in processed_patient_id:  # "Duplicate Patient_ID '" + str(patient_id + "'. Skipping")
            continue
        cholesterol_data.append([])
        processed_patient_id.append(patient_id)
        patient_list.append(patient)
        findCholesUrl = root_url + "Observation?patient=" + patient_id + "&code=2093-3&_sort=date&_count=13"
        patientChol = requests.get(url=findCholesUrl).json()
        try:
            # print("\n" + str(['Patient', 'Cholestrol', 'Date']))  # Header
            cholData = patientChol['entry']
            for entry2 in cholData:  # For each Cholesterol Value in Patient
                record = []
                item = entry2['resource']
                cholesterol_value = str(item['valueQuantity']['value'])
                issued = item['issued'][:len('2008-10-14')]
                date = datetime.strptime(issued, '%Y-%m-%d').date()
                aus_date_format = str(date.day) + '-' + str(date.month) + '-' + str(date.year)
                record.append("{:>11}".format(patient_id))
                record.append("{:>14}".format(cholesterol_value + " mg/L"))
                record.append("{:>13}".format(aus_date_format))
                cholesterol_data.append(record)  # Append all 3 Values to Array
        except KeyError:  # No Cholesterol Data
            continue

    return cholesterol_data

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
        command=lambda: create_info_window(window,entry)
    )

    # button.pack(side="top")
    # button.place(bordermode="outside", height=y/9, width=x/6, x=x/2.5, y=y/2.5)
    button.place(relx=0.5, rely=0.5, anchor="center")
    window.mainloop()

def create_info_window(window,entry):
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
        command=lambda: [destroy_info_window(logged_in,info_window),set_login_window()]
    )

    out_button.pack()

    lb_label = tk.Label(info_window, bg='grey', width=40, text="   Patient     Cholestrol        Date    ")
    lb_label.pack()

    patient_list = get_patient_list(cholesterol)


    patient_lb = tk.Listbox(info_window)
    for patient in patient_list:
        patient_lb.insert('end', tuple(patient))

    patient_lb.config(width=0, height=0)

    patient_lb.pack()

    history_text = tk.Text(info_window)

    history_button = tk.Button(info_window, text='Show history', width=15,
                   height=2, command=lambda: show_patient_history(history_text,cholesterol,patient_lb))
    history_button.pack()

    history_text.pack()


    while logged_in:
        print("\nWaiting for user input...")
        out_button.wait_variable(button_pressed)  # Hold until Button is pressed
        history_button.wait_variable(button_pressed)
        window.destroy()
        main()

    info_window.mainloop()

def show_patient_history(history_text, encounter_list, patient_lb):
    history_text.delete('1.0',tk.END)

    patient = patient_lb.get(patient_lb.curselection())

    for e in encounter_list:
        if len(e) == 3:
            if e[0] == patient[0]:
                history_text.insert('end',str(e)+"\n")


def destroy_info_window(logged_in, info_window):
    if logged_in:
        info_window.destroy()


def main():
    #Create and set the login window
    set_login_window()




if __name__ == "__main__":
    main()
