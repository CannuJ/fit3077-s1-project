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


def get_next_url(response):
    """
    Checks to see if there exists a next url in the response
    :param response: The response from the fhir server
    :return: The url of the next response, or False if non existent
    """
    for link in response['link']:
        if link['relation'] == 'next':
            return link['url']
    return False


def get_patient_list(encounter_list):
    """
    Iterates through our list of encounters, building a new list of latest recordings
    :param encounter_list: A list of all cholesterol values of patients being watched
    :return: A list of latest cholesterol values per patient being watched
    """
    patient_list = []
    current_patient = encounter_list[2]
    for i in range(3, len(encounter_list)):
        if encounter_list[i][0] == current_patient[0]:
            if parse(encounter_list[i][2]) > parse(current_patient[2]):
                current_patient = encounter_list[i]
        else:
            patient_list.append(current_patient)
            current_patient = encounter_list[i]
    if current_patient not in patient_list:
        patient_list.append(current_patient)

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


def get_all_patient_data(identifier, additional_id_array):
    """
    Takes the user identifier determined from logging in,
    and returns a list of encounters associated to that identifier
    :param identifier: the identifier that references the practitioner in question
    :param additional_id_array: if any IDs are added they will be in here
    :return: a list of encounters associated to the identifier
    """
    encounters_url = root_url + "Encounter?participant.identifier=" + npi_url + "|" + identifier + \
                     "&_include=Encounter.participant.individual&_include=Encounter.patient"
    encounters_response = requests.get(url=encounters_url).json()
    try:
        all_encounter_data = encounters_response['entry']
    except KeyError:  # Was not a valid Identifier
        return False

    next_url = ""  # Test
    iterator = 0

    patient_id_list = []  # We don't want to process the same Patient

    while next_url is not False:

        iterator += 1
        try:  # Large encounter bundles take a while to process, uncomment to get an idea how long to go
            parsed_entries = iterator * 50
            total = encounters_response['total']  # Total is calculated dynamically
            if int(parsed_entries) < int(total):
                print("Parsed " + str(parsed_entries) + "/" + str(total) + " entries")
            else:
                print("Parsed " + str(total) + "/" + str(total) + " entries")
        except KeyError:
            parsed_entries = iterator * 50
            print("Parsed " + str(parsed_entries) + " entries")
            pass

        next_url = get_next_url(encounters_response)
        for entry in all_encounter_data:
            patient = entry['resource']['subject']['reference']
            patient_id = patient.split('/')[1]
            if patient_id in patient_id_list:  # Duplicate Patient_ID, Ignore ID
                continue
            patient_id_list.append(patient_id)
        if next_url is not False:
            encounters_response = requests.get(url=next_url).json()  # GET with next url

    # Append additional IDs if not already present
    for id_num in additional_id_array:
        if str(id_num) not in patient_id_list:
            patient_id_list.append(str(id_num))

    cholesterol_data_array = [['  Patient  ', '  Cholesterol  ', '    Date    ']]  # Header

    # Grab Patient Cholesterol
    for patient_id in patient_id_list:
        cholesterol_url = root_url + "Observation?patient=" + patient_id + "&code=2093-3&_sort=date&_count=13"
        patient_cholesterol = requests.get(url=cholesterol_url).json()
        try:
            cholesterol_data = patient_cholesterol['entry']
            for entry2 in cholesterol_data:  # For each Cholesterol Record of Patient
                record = []
                item = entry2['resource']
                cholesterol_value = str(item['valueQuantity']['value'])
                issued = item['issued'][:len('2008-10-14')]
                date = datetime.strptime(issued, '%Y-%m-%d').date()
                aus_date_format = str(date.day) + '-' + str(date.month) + '-' + str(date.year)
                record.append(patient_id)
                record.append(cholesterol_value + " mg/L")
                record.append(aus_date_format)
                cholesterol_data_array.append(record)  # Append all 3 Values to Array
        except KeyError:  # No Cholesterol Data
            continue

    return cholesterol_data_array


def get_patient_name(patient_id):
    """
    Grabs patient full name with title
    :param patient_id: The patients id within the fhir server
    :return: A string of their "Title + First Name + Surname"
    """
    patient_URL = root_url + "Patient" + "/" + patient_id
    data = requests.get(url=patient_URL).json()
    patient_name = str(data['name'][0]['prefix'][0]) + str(data['name'][0]['given'][0]) + " " + str(
        data['name'][0]['family'])
    return patient_name


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
    user_login, fullname = login(entry.get())
    if user_login is False or fullname is False:
        failed_login(window)
    else:
        create_info_window(window, entry)


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
def create_info_window(window, entry, prac_id=None, is_recall=False, additional_id_array=None):
    if additional_id_array is None:
        additional_id_array = []

    input = entry.get()

    if is_recall is False:
        prac_id = entry.get()
    else:
        additional_id_array.append(input)

    window.destroy()

    info_window = tk.Tk()

    info_window.title("Health Practitioner Database")

    # Draw 1/2 Screen Size @ Centered
    x, y = get_screen_dimensions()
    info_window.geometry('%dx%d+%d+%d' % (x, y, x / 2, y / 2))

    user_login, fullname = login(prac_id)

    welcome_message = "\nWelcome " + str(fullname) + "\n"
    label_entry = tk.Label(info_window, text=welcome_message)
    label_entry.pack()

    cholesterol = get_all_patient_data(user_login, additional_id_array)

    if cholesterol is False:
        main()

    logged_in = True

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
                                   command=lambda: [create_info_window(info_window, entry, prac_id, True, additional_id_array)])

    add_patient_button.pack()

    lb_label = tk.Label(info_window, bg='grey', width=40, text=" ID     Name        Surname      Cholesterol")
    lb_label.pack()

    empty_label = tk.Label(info_window, fg='red', width=50, text="No patient information available")
    if len(cholesterol) == 2:
        empty_label.pack()
    else:
        empty_label.destroy()

    patient_latest_list = get_patient_list(cholesterol)

    cholesterol_array = []

    patient_lb = tk.Listbox(info_window)
    for patient in patient_latest_list:
        patient_ID = str(int(patient[0]))
        patient_name = get_patient_name(patient_ID)

        cholesterol_array.append(float(patient[1].strip("mg/L").strip(" ")))

        patient = [patient_ID, patient_name, patient[1]]
        patient_lb.insert('end', tuple(patient))

    cholesterol_average = sum(cholesterol_array) / len(cholesterol_array)

    for i in range(len(patient_latest_list)):
        if cholesterol_array[i] > cholesterol_average:
            patient_lb.itemconfigure(i, {'fg': 'red'})
        else:
            patient_lb.itemconfigure(i, {'fg': 'black'})

    patient_lb.config(width=0, height=0)

    patient_lb.pack()

    history_text = tk.Text(info_window, height='6')
    detail_text = tk.Text(info_window, height='5')

    history_button = tk.Button(info_window, text='Show patient detail', width=15, height=2, command=lambda: [
            show_patient_history(history_text, cholesterol, patient_lb, patient_latest_list),
            show_patient_detail(detail_text, cholesterol, patient_lb)])
    history_button.pack()

    history_text.pack()
    detail_text.pack()

    while logged_in:
        print("\nWaiting for user input...")
        out_button.wait_variable(button_pressed)  # Hold until Button is pressed
        history_button.wait_variable(button_pressed)
        add_patient_button.wait_variable(add_button_pressed)
        window.destroy()
        main()
    info_window.mainloop()


def show_patient_history(history_text, encounter_list, patient_lb, latest_list):
    """
    This function takes the encounter list, patient list box and history text in the information
    window to output the other history value for the selected patient in the list box in the text space.
    :param history_text:
    :param encounter_list:
    :param patient_lb:
    :param latest_list:
    :return: Outputs patient history of all cholesterol values recorded
    """
    history_text.delete('1.0', tk.END)

    history_text.insert('end', "Patient history: \n")
    history_text.insert('end', "   Patient        Cholestrol        Date    \n")

    patient = patient_lb.get(patient_lb.curselection())

    patient_id = patient[0]

    for item in latest_list:
        if len(item) == 3:
            if item[0].strip(" ") == patient_id:
                latest_date = item[2].strip(" ")

    index = 2
    for e in encounter_list:
        if len(e) == 3:
            if e[0].strip(" ") == patient[0]:
                for item in e:
                    history_text.insert('end', str(item) + "    ")
                history_text.insert('end', "\n")
                index += 1
            if e[2].strip(" ") == latest_date:
                start_index = str(index) + '.0'
                end_index = str(index) + '.100'
                history_text.tag_add('latest', start_index, end_index)
                history_text.tag_configure('latest', foreground='red')


def show_patient_detail(detail_text, patient_lb):
    """
    This function take the patient list box and detail text in the information window to output
    the patient details for the selected patient in the list box in the text space.
    :param detail_text:
    :param patient_lb:
    :return:
    """
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
