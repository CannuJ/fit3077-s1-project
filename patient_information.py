import requests
import tkinter as tk


root_url = 'https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/'  # Root URL
npi_url = "http://hl7.org/fhir/sid/us-npi"



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

