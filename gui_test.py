import requests
import pandas as pd
from datetime import datetime
import tkinter as tk
from PyQt5 import QtWidgets
import sys
import os

root_url = 'https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/'  # Root URL
npi_url = "http://hl7.org/fhir/sid/us-npi"


def get_screen_dimensions():

    # Tkinter way to find the screen resolution
    # screen_width = toplevel.winfo_screenwidth()
    # screen_height = toplevel.winfo_screenheight()

    app = QtWidgets.QApplication(sys.argv)

    screen = app.primaryScreen()
    # print('Screen: %s' % screen.name())
    size = screen.size()
    screen_width = size.width()
    screen_height = size.height()
    # print('Size: %d x %d' % (screen_width, screen_height))
    rect = screen.availableGeometry()
    # print('Available: %d x %d' % (rect.width(), rect.height()))

    x = screen_width/2
    y = screen_height/2

    return x, y


def login(user_login):

    identifier_url = root_url + "Encounter?participant.identifier=" + npi_url + "|" + \
                     user_login + "&_include=Encounter.participant.individual&_include=Encounter.patient"

    print("\nAttempting Identifier Login from: " + identifier_url + "\n")
    data = requests.get(url=identifier_url).json()

    # Assume input is an Identifier, if this fails, fallback onto Practitioner ID
    try:
        print("Found " + str(data['entry'][0]['resource']['participant'][0]['individual']['reference']))
        practitioner_url = root_url + str(data['entry'][0]['resource']['participant'][0]['individual']['reference'])
    except KeyError:
        print("Invalid Practitioner ID, perhaps this is an Identifier")
        practitioner_url = root_url + "Practitioner/" + user_login

    print("\nAttempting Practitioner ID Login from: " + practitioner_url)
    data = requests.get(url=practitioner_url).json()

    try:
        if data['issue'][0]['severity'] == "error":
            print("\nFailed Login!\n")
            return False
    except KeyError:
        print("\nSuccess!")

    for i in range(len(data['identifier'])):

        if data['identifier'][i]['system'] == npi_url:
            identifier_value = data['identifier'][i]['value']

            fullname = str(data['name'][0]['prefix'][0]) + " " + str(data['name'][0]['given'][0]) + " " + \
                       str(data['name'][0]['family'])

            print("\nWelcome " + fullname)

    return identifier_value, fullname


def get_all_patient_data(identifier):
    encounters_url = root_url + "Encounter?participant.identifier=" + npi_url + "|" + identifier + \
                     "&_include=Encounter.participant.individual&_include=Encounter.patient"

    print("\nPulling Patient Information")

    all_encouters_practitioner = requests.get(url=encounters_url).json()
    try:
        all_encouters_practitioner['entry']
    except KeyError:
        print("Invalid Identifier, returning to login\n")
        return

    all_encouter_data = all_encouters_practitioner['entry']

    # let's use a dataframe to store the data
    # TODO: cholesterol_data = pd.DataFrame(columns=['Patient', 'Cholestrol', 'Date'])
    patient_list = []

    processed_patient_id = []

    cholesterol_data = [['Patient', 'Cholestrol', 'Date']]

    for entry in all_encouter_data:
        item = entry['resource']
        patient = item['subject']['reference']

        # let's get the patient id, which we need to search for the cholesterol value
        patient_id = patient.split('/')[1]
        if patient_id in processed_patient_id:
            # print("Duplicate Patient_ID '" + str(patient_id + "'. Skipping"))
            continue
        processed_patient_id.append(patient_id)
        patient_list.append(patient)
        findCholesUrl = root_url + "Observation?patient=" + patient_id + "&code=2093-3&_sort=date&_count=13"
        patientChol = requests.get(url=findCholesUrl).json()
        try:
            cholData = patientChol['entry']
            # print(findCholesUrl)
            # print(cholData)
            # here we get all cholesterol values recorded for the particular patient
            print("\n" + str(['Patient', 'Cholestrol', 'Date']))
            for entry2 in cholData:
                record = []
                item = entry2['resource']
                cholesterol_value = item['valueQuantity']['value']
                # print(item)
                issued = item['issued'][:len('2008-10-14')]
                date = datetime.strptime(issued, '%Y-%m-%d').date()

                record.append(patient_id)
                record.append(cholesterol_value)
                aus_date_format = str(date.day) + '-' + str(date.month) + '-' + str(date.year)
                record.append(aus_date_format)
                # this prints the cholesterol data of the patients of a particular practitioner
                cholesterol_data.append(record)
                print(record)
                # TODO: cholesterol_data.append(record)
        except:
            continue
            # no data

    return cholesterol_data


def main():

    window = tk.Tk()
    window.title("Health Practitioner Database")

    # Draw 1/2 Screen Size @ Centered
    x, y = get_screen_dimensions()
    window.geometry('%dx%d+%d+%d' % (x, y, x/2, y/2))

    frame_entry = tk.Frame()

    label_entry = tk.Label(master=frame_entry, text="Practitioner ID / Identifier")
    label_entry.pack()

    frame_entry.pack()

    entry = tk.Entry(master=frame_entry)
    entry.pack()

    button_pressed = tk.IntVar()

    button = tk.Button(
        text="Login",
        width=5,
        height=2,
        bg="blue",
        fg="yellow",
        command=lambda: button_pressed.set(1)
    )

    # button.pack(side="top")
    # button.place(bordermode="outside", height=y/9, width=x/6, x=x/2.5, y=y/2.5)
    button.place(relx=0.5, rely=0.5, anchor="center")

    user_login = False

    while user_login is False:
        print("\nWaiting for user input...")
        button.wait_variable(button_pressed)
        print("Button Pressed")
        # label_entry = tk.Label(master=frame_entry, text="Loading...")
        label_entry.pack()
        input = entry.get()
        if input is not "":
            entry.delete(0, tk.END)
            user_login, fullname = login(input)

    welcome_message = "\nWelcome " + str(fullname)
    label_entry = tk.Label(master=frame_entry, text=welcome_message)
    label_entry.pack()

    cholesterol = get_all_patient_data(user_login)

    data_frame = tk.Frame()

    for line in cholesterol:
        cholesterol_entry = tk.Label(master=data_frame, text=line)
        cholesterol_entry.pack()

    data_frame.pack()

    window.mainloop()


if __name__ == "__main__":
    main()
