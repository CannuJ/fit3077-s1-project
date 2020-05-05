import requests
import pandas as pd
from datetime import datetime

root_url = 'https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/'  # Root URL
npi_url = "http://hl7.org/fhir/sid/us-npi"


def login():
    valid_input = False
    while not valid_input:

        user_login = input("Enter your Practitioner ID or Identifier to login: ")

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
                continue
        except KeyError:
            print("\nSuccess!")

        for i in range(len(data['identifier'])):

            if data['identifier'][i]['system'] == npi_url:
                identifier_value = data['identifier'][i]['value']

                print("\nWelcome " + str(data['name'][0]['prefix'][0]) + " " + str(data['name'][0]['given'][0]) + " " +
                      str(data['name'][0]['family']))
                # print("\nSystem: " + system + " | Value: " + identifier_value)

                encounters_url = root_url + "Encounter?participant.identifier=" + npi_url + "|" + identifier_value + \
                                 "&_include=Encounter.participant.individual&_include=Encounter.patient"
                # print(encounters_url)

                valid_input = True

    return identifier_value


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
                print(record)
                # TODO: cholesterol_data.append(record)
        except:
            continue
            # no data

    return False


if __name__ == '__main__':

    failed_attempt = True

    while failed_attempt:
        identifier = login()
        failed_attempt = get_all_patient_data(identifier)
