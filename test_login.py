import requests
import pandas as pd
from datetime import datetime

root_url = 'https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/'  # Root URL


def login():
    valid_input = False
    while not valid_input:

        input_is_id = input("Are you logging in with a Practitioner ID (0) or Identifier (1): ")

        if input_is_id == "0":  # TODO: Practitioner ID -> Identifier
            valid_input = True

            practitioner_id = input("\nEnter you Practitioner ID: ")
            practitioner_url = root_url + "Practitioner/" + practitioner_id

            print("Grabbing Identifier from: " + practitioner_url)
            data = requests.get(url=practitioner_url).json()

            for i in range(len(data['identifier'])):

                system = data['identifier'][i]['system']
                identifier_value = data['identifier'][i]['value']
                print("\nSystem: " + system + " | Value: " + identifier_value)

                encounters_url = root_url + "Encounter?participant.identifier=" + system + "|" + identifier_value + \
                                 "&_include=Encounter.participant.individual&_include=Encounter.patient"
                print(encounters_url)

                return identifier_value

        if input_is_id == "1":  # TODO: Identifier | Assume using System: "http://hl7.org/fhir/sid/us-npi"
            valid_input = True

            system = "http://hl7.org/fhir/sid/us-npi"
            identifier_value = input("\nEnter you Identifier: ")
            print("\nSystem: " + system + " | Value: " + identifier_value)

            encounters_url = root_url + "Encounter?participant.identifier=" + system + "|" + identifier_value + \
                             "&_include=Encounter.participant.individual&_include=Encounter.patient"
            print(encounters_url)

            return identifier_value


def get_all_patient_data(identifier):

    encounters_url = root_url + "Encounter?participant.identifier=http://hl7.org/fhir/sid/us-npi|" + identifier + \
                     "&_include=Encounter.participant.individual&_include=Encounter.patient"

    all_encouters_practitioner = requests.get(url=encounters_url).json()
    all_encouter_data = all_encouters_practitioner['entry']

    # let's use a dataframe to store the data
    cholesterol_data = pd.DataFrame(columns=['Patient', 'Cholestrol', 'Date'])
    patient_list = []

    for entry in all_encouter_data:
        item = entry['resource']
        patient = item['subject']['reference']

        # let's get the patient id, which we need to search for the cholesterol value
        patient_id = patient.split('/')[1]
        patient_list.append(patient)
        findCholesUrl = root_url + "Observation?patient=" + patient_id + "&code=2093-3&_sort=date&_count=13"
        patientChol = requests.get(url=findCholesUrl).json()
        try:
            cholData = patientChol['entry']
            # here we get all cholesterol values recorded for the particular patient
            for entry2 in cholData:
                record = []
                item = entry2['resource']
                cholesterol_value = item['valueQuantity']['value']
                # print(item)
                issued = item['issued'][:len('2008-10-14')]
                date = datetime.strptime(issued, '%Y-%m-%d').date()

                if (patient_id == '29163') & (cholesterol_value == 199.14):
                    print(item)

                record.append(patient_id)
                record.append(cholesterol_value)
                aus_date_format = str(date.day) + '-' + str(date.month) + '-' + str(date.year)
                record.append(aus_date_format)
                # this prints the cholesterol data of the patients of a particular practitioner
                print(record)
                cholesterol_data.append(record)
        except:
            continue
            # no data


identifier = login()
get_all_patient_data(identifier)
