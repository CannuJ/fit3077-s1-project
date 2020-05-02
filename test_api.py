import requests
import pandas as pd
from datetime import datetime
import json

# TODO: Root URL
root_url = 'https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/'
print("Root URL: " + root_url)

# TODO: Generic Request - Patient ID

# Patients Bundle Url
patients_url = root_url + "Patient"
print("Patients URL: " + patients_url)

# Individual Patient  Url ("1" is test ID)
patient_id_url = patients_url + "/1"
print("Patient 1 URL: " + patient_id_url)

# GET Request for Patient ID "1"
data = requests.get(url=patient_id_url).json()
# print(data)
# print(json.dumps(data, indent=4, sort_keys=True))

# TODO: Specific Request - Search Patient with Parameters

#
search1_url = root_url + "Observation?patient=6430"
print("Observation [patient=6430] URL: " + search1_url)

#
search2_url = root_url + "Observation?patient=6430&code=2093-3"
print("Observation [patient=6430&code=2093-3] URL: " + search2_url)

#
search3_url = root_url + "Observation?patient=3689&code=2093-3&_sort=date&_count=13"
print("Observation [patient=3689&code=2093-3&_sort=date&_count=13] URL: " + search3_url)

data2 = requests.get(url=search3_url).json()
entry = data2['entry']
print(len(entry))
# print(data2)

# Cholesterol Data
Cholesterol_data = pd.DataFrame(columns=['cholestrol', 'issued'])
for i in range(len(entry)):
    record = []
    item = entry[i]['resource']
    weight = str(item['valueQuantity']['value']) + item['valueQuantity']['unit']
    issued = item['issued']
    record.append(weight)
    record.append(issued)
    Cholesterol_data.loc[i] = record

print(Cholesterol_data)


# TODO: Request 3 - Additional | Call as function below


def check_date(patient_id, new_date, data):
    # check whether the observation's issued date is the latest
    if patient_id not in data.index:
        return True
    else:
        old_date = data.loc[patient_id, 'issued']
        if new_date > old_date:
            data.drop([patient_id])
            return True
        else:
            return False


def request_3():
    dReport_url = root_url + "DiagnosticReport"
    data3 = pd.DataFrame(
        columns=['patientid', 'gender', 'birthDate', 'maritualStatus', 'totalCholesterol', "Triglycerides",
                 'lowDensity',
                 'highDensity', 'issued'])

    next_page = True
    next_url = dReport_url
    count_page = 0
    count_patient = 0

    while next_page:
        dReports = requests.get(url=next_url).json()

        # As discussed before, The monash FHIR server return results in a series of pages.
        # Each page contains 10 results as default.
        # here we check and record the next page
        next_page = False
        links = dReports['link']
        for i in range(len(links)):
            link = links[i]
            if link['relation'] == 'next':
                next_page = True
                next_url = link['url']
                count_page += 1

        # Extract data
        entry = dReports['entry']
        print(entry)
        for i in range(len(entry)):
            patient_array = []
            results = entry[i]['resource']['result']

            # Check whether this observation is on chterol or not.
            chterol = False
            for result in results:
                if result['display'] == 'Total Cholesterol':
                    chterol = True

            # If this observation is on cholesterol value, then record the patient's id and issued date.
            if chterol:
                patient_id = entry[i]['resource']['subject']['reference'][len('Patient/'):]
                issued = entry[i]['resource']['issued'][:len('2008-10-14')]
                date = datetime.strptime(issued, '%Y-%m-%d').date()

                # Get patient's basic information
                patient_data = requests.get(url=root_url + "Patient/" + patient_id).json()
                gender = patient_data['gender']
                birth = patient_data['birthDate']
                birthDate = datetime.strptime(birth, '%Y-%m-%d').date()
                maritalStatus = patient_data['maritalStatus']['text']

                check = check_date(patient_id, date, data3)

                # Check if the patient's Chterol value has already been recorded in the dataframe
                if check:
                    count_patient += 1
                    patient_array.append(patient_id)
                    patient_array.append(gender)
                    patient_array.append(birthDate)
                    patient_array.append(maritalStatus)
                    # Record chtoral(including total, Triglycerides, lowDensity and highDensity) value

                    observation_ref = result['reference']
                    observation_data = requests.get(url=root_url + observation_ref).json()
                    value = observation_data['valueQuantity']['value']
                    patient_array.append(value)
                    patient_array.append(date)
                    print(patient_array)
                    data3.append(patient_array)


# Uncomment to run Request 3
# request_3()


# TODO: Request 4 - Encounters | Uncomment Function Call Below

def request_4():
    encounters_url = root_url + "Encounter?participant.identifier=http://hl7.org/fhir/sid/us-npi|500&_include=Encounter" \
                                ".participant.individual&_include=Encounter.patient"
    print("Encounters URL: " + encounters_url)
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
                issued = item['issued'][:len('2008-10-14')]
                date = datetime.strptime(issued, '%Y-%m-%d').date()
                record.append(patient)
                record.append(cholesterol_value)
                record.append(date)
                # this prints the cholesterol data of the patients of a particular practitioner
                print(record)
                cholesterol_data.append(record)
        except:
            continue
            # no data


# request_4()


# TODO: Request 5 - Alternate for Request 4

def request_5():

    encounters_url = root_url + "Encounter?participant.identifier=http://hl7.org/fhir/sid/us-npi|500&_include=Encounter" \
                                ".participant.individual&_include=Encounter.patient"
    print("Encounters URL: " + encounters_url)
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

    for patient_id in patient_list:
        dReport_url = root_url + "DiagnosticReport/?patient=" + patient_id
        dReports = requests.get(url=dReport_url).json()
        # Extract data
        try:
            entry = dReports['entry']
        except:
            continue
            # no entry

        for en in entry:
            results = en['resource']['result']

            # Check whether this observation is on cholesterol or not.
            chterol = False
            for result in results:
                if result['display'] == 'Total Cholesterol':
                    chterol = True
                    issued = en['resource']['issued'][:len('2008-10-14')]
                    date = datetime.strptime(issued, '%Y-%m-%d').date()

                    observation_ref = result['reference']
                    # print("Cholesterol URL: " + root_url + observation_ref)
                    observation_data = requests.get(url=root_url + observation_ref).json()
                    value = observation_data['valueQuantity']['value']
                    patient_array = []
                    patient_array.append(patient_id)
                    patient_array.append(value)
                    patient_array.append(date)
                    # this prints the cholesterol data of the patients of a particular practitioner
                    print(patient_array)


request_5()
