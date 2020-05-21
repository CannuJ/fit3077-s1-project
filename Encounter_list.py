import requests
from datetime import datetime

root_url = 'https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/'  # Root URL
npi_url = "http://hl7.org/fhir/sid/us-npi"

def get_all_patient_data(identifier, additional_id_array, removed_id_array):
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
        if patient_id in removed_id_array:
            continue
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
