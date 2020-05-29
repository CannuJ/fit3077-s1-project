import requests
from Patient import Patient

root_url = 'https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/'  # Root URL
npi_url = "http://hl7.org/fhir/sid/us-npi"


class Practitioner:
    def __init__(self, login):

        self.login_type = None
        self.login = str(login)

        self.prefix = ""
        self.given_name = ""
        self.family_name = ""

        self.gender = ""
        self.address = ""

        self.practitioner_id = None
        self.npi_id = None

        self.patient_base_id_array = []
        self.patient_parsed_id_array = []
        self.patient_monitor_id_array = []

        self.patient_data = {}

        self.attempt_login()

        if self.login_type is not None:
            self.get_personal_details()  # TODO: Potential to run Asynchronously
            self.get_practitioner_patients()  # TODO: Potential to run Asynchronously
            self.parse_patient_list()  # TODO: Potential to run Asynchronously

    # URLs and Handling

    def url_practitioner_id(self):
        if not self.practitioner_id:
            return None
        return root_url + "Practitioner/" + self.practitioner_id

    def url_npi_id(self):
        if not self.npi_id:
            return None
        return root_url + "Practitioner?identifier=" + npi_url + "|" + self.npi_id

    def url_patient_encounter(self):
        return root_url + "Encounter?participant.identifier=" + npi_url + "|" + self.npi_id + \
               "&_include=Encounter.participant.individual&_include=Encounter.patient"

    # Attempt Login
    def attempt_login(self):

        identifier_url = root_url + "Practitioner?identifier=" + npi_url + "|" + self.login
        data = requests.get(url=identifier_url).json()

        try:  # Assume input is an Identifier, if this fails, fallback onto Practitioner ID
            if data['entry'][0]['resource']['resourceType'] != "Practitioner":
                raise KeyError
            self.login_type = "NPI Identifier"
            self.npi_id = self.login
        except KeyError:  # Invalid Identifier, try assumption user_login is Practitioner ID
            practitioner_url = root_url + "Practitioner/" + self.login
            data = requests.get(url=practitioner_url).json()
            try:
                if data['issue'][0]['severity'] == "error":  # Failed Login
                    pass
            except KeyError:  # Successful Login
                pass
                self.login_type = "Practitioner ID"
                self.practitioner_id = self.login

                for i in range(len(data['identifier'])):
                    if data['identifier'][i]['system'] == npi_url:
                        self.npi_id = data['identifier'][i]['value']

    def is_logged_in(self):
        if not self.login_type:
            return False
        else:
            return True

    # Fullname
    def fullname(self):
        return self.prefix + " " + self.given_name + " " + self.family_name

    def get_personal_details(self):

        data = requests.get(url=self.url_npi_id()).json()

        name_details = data['entry'][0]['resource']['name'][0]

        self.prefix = str(name_details['prefix'][0])
        self.given_name = str(name_details['given'][0])
        self.family_name = str(name_details['family'])

        self.gender = data['entry'][0]['resource']['gender']

        address_details = data['entry'][0]['resource']['address'][0]

        self.address = str(address_details['line'][0]) + " " + str(address_details['city']) + " " \
                       + str(address_details['state']) + " " + str(address_details['country'])

    # Patient Handling
    def get_practitioner_patients(self):

        next_url = self.url_patient_encounter()
        iterator = 0

        print("")

        while next_url is not False:
            encounters_response = requests.get(url=next_url).json()
            next_url = get_next_url(encounters_response)

            all_encounter_data = encounters_response['entry']

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

            for entry in all_encounter_data:
                patient = entry['resource']['subject']['reference']
                patient_id = patient.split('/')[1]
                if patient_id in self.patient_base_id_array:  # Duplicate Patient_ID, Ignore ID
                    continue
                self.patient_base_id_array.append(patient_id)

        print("")

    def parse_patient_list(self):
        for patient_id in self.patient_base_id_array:

            self.patient_data[patient_id] = Patient(patient_id)
            self.patient_parsed_id_array.append(patient_id)

            if not self.patient_data[patient_id].has_cholesterol() and not self.patient_data[patient_id].has_blood():
                print("Patient ID: " + str(patient_id) + " processed from Practitioner Encounters (NO DATA)")
                continue

            self.patient_monitor_id_array.append(patient_id)
            print("Patient ID: " + str(patient_id) + " processed from Practitioner Encounters (WITH DATA)")

    def add_patient(self, patient_id):
        patient_id = str(patient_id)  # Testing through code assumes ID is int
        if patient_id in self.patient_parsed_id_array:
            if self.patient_data[patient_id].has_cholesterol() or self.patient_data[patient_id].has_blood():
                if patient_id not in self.patient_monitor_id_array:
                    self.patient_monitor_id_array.append(patient_id)
                    print("Patient ID: " + str(patient_id) + " already processed, added to Monitor List")
                    return
                else:
                    print("Patient ID: " + str(patient_id) + " already being monitored")
                    return
            else:
                print("Patient ID: " + str(patient_id) + " already being monitored or no data exists for Patient")
                return

        self.patient_data[patient_id] = Patient(patient_id)
        if not self.patient_data[patient_id].valid:
            print("Patient ID: " + str(patient_id) + " is an invalid ID")
            del self.patient_data[patient_id]
            return

        self.patient_parsed_id_array.append(patient_id)

        if not self.patient_data[patient_id].has_cholesterol() and not self.patient_data[patient_id].has_blood():
            print("Patient ID: " + str(patient_id) + " ADDED by Practitioner Request (NO DATA)")
            return

        self.patient_monitor_id_array.append(patient_id)
        print("Patient ID: " + str(patient_id) + " ADDED by Practitioner Request (WITH DATA)")

    def remove_patient(self, patient_id):
        patient_id = str(patient_id)  # Testing through code assumes ID is int
        if patient_id not in self.patient_monitor_id_array:
            print("Patient ID: " + str(patient_id) + " not currently being monitored")
            return

        self.patient_monitor_id_array.remove(patient_id)
        print("Patient ID: " + str(patient_id) + " REMOVED by Practitioner Request")

    def get_patient_list(self):
        return self.patient_monitor_id_array

    def get_patient(self, patient_id):
        return self.patient_data[patient_id]

    def display_patients(self):

        print("\nDisplaying all Patients being monitored WITH DATA:")

        for patient_id in self.patient_monitor_id_array:
            print("\n" + self.patient_data[patient_id].id + " | " + self.patient_data[patient_id].get_fullname())
            if self.patient_data[patient_id].has_cholesterol():
                print(str(self.patient_data[patient_id].cholesterol_latest()))
            if self.patient_data[patient_id].has_blood():
                print(str(self.patient_data[patient_id].blood_latest()))

    def cholesterol_average(self):
        cholesterol_array = []

        for patient_id in self.patient_monitor_id_array:
            cholesterol_array.append(self.patient_data[patient_id].cholesterol_latest()[1])

        valid_len = len(cholesterol_array)
        total = float(0)
        for value in cholesterol_array:
            if not value:
                valid_len -= 1
            else:
                total += float(value)

        return total / valid_len

    def blood_average(self):
        diastolic_array = []
        systolic_array = []

        for patient_id in self.patient_monitor_id_array:
            diastolic_array.append(self.patient_data[patient_id].blood_latest()[0][1])
            systolic_array.append(self.patient_data[patient_id].blood_latest()[1][1])

        diastolic_len = len(diastolic_array)
        diastolic_total = float(0)

        for value in diastolic_array:
            if not value:
                diastolic_len -= 1
            else:
                diastolic_total += float(value)

        systolic_len = len(systolic_array)
        systolic_total = float(0)

        for value in systolic_array:
            if not value:
                systolic_len -= 1
            else:
                systolic_total += float(value)

        return [diastolic_total/diastolic_len, systolic_total/systolic_len]


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


if __name__ == '__main__':
    testPractitioner = Practitioner(850)

    print("\nPractitioner ID Url: " + str(testPractitioner.url_practitioner_id()))
    print("NPI ID Url: " + str(testPractitioner.url_npi_id()))

    print("\nIs Logged in: " + str(testPractitioner.is_logged_in()))
    print("\nWelcome " + str(testPractitioner.fullname()) + "\n")

    testPractitioner.add_patient(29163)
    testPractitioner.add_patient(3912781)
    testPractitioner.add_patient(2)

    testPractitioner.display_patients()

    print("")
    testPractitioner.remove_patient(1807650)  # Parsed WITH DATA
    testPractitioner.remove_patient(29163)  # Added WITH DATA
    testPractitioner.remove_patient(4431584)  # Parsed but NO DATA

    testPractitioner.display_patients()

    print("")
    testPractitioner.add_patient(29163)  # Parsed but REMOVED
    testPractitioner.add_patient(29163)  # Duplicate

    testPractitioner.display_patients()



