import requests
from datetime import datetime


class Patient:
    def __init__(self, id_num):
        self.id = str(id_num)
        self.valid = False

        self.prefix = ""
        self.given_name = ""
        self.family_name = ""
        self.gender = ""
        self.birth_date = ""
        self.address = ""

        if self.valid_id():
            self.valid = True
            # self.get_personal_details()  # TODO: Potential to run Asynchronously
            self.cholesterol_array = []
            # self.get_cholesterol()  # TODO: Potential to run Asynchronously
            self.blood_array = {"Diastolic Blood Pressure": [], "Systolic Blood Pressure": []}
            # self.get_blood()  # TODO: Potential to run Asynchronously

    # URLs and Handling

    def url_base(self):
        return "https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/Patient/" + self.id

    def url_cholesterol(self):
        return "https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/Observation?patient=" + self.id + \
               "&code=2093-3&_sort=date"

    def url_blood(self):
        return "https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/Observation?patient=" + self.id + \
               "&code=55284-4&_sort=date"

    def valid_id(self):
        patient_data = requests.get(url=self.url_base()).json()
        try:
            if patient_data['issue'][0]['severity'] == "error" and patient_data['issue'][0]['code'] == "processing":
                return False
        except KeyError:  # If either of these is not "error" and "processing" ASSUME is valid_id
            return True

    # Valid Patient Init
    def get_preload(self):
        self.get_personal_details()
        self.get_cholesterol()
        self.get_blood()

    # Personal Details
    def get_personal_details(self):
        patient_data = requests.get(url=self.url_base()).json()

        # Personal Details
        try:
            self.prefix = str(patient_data['name'][0]['prefix'][0])
        except KeyError:
            self.prefix = None
        self.given_name = str(patient_data['name'][0]['given'][0])
        self.family_name = str(patient_data['name'][0]['family'])

        self.gender = str(patient_data['gender'])
        self.birth_date = str(patient_data['birthDate'])
        self.address = str(patient_data['address'][0]['line'][0]) + " " + str(patient_data['address'][0]['city']) \
                       + " " + str(patient_data['address'][0]['state']) + " " \
                       + str(patient_data['address'][0]['country'])

    # Returning Strings of Details
    def get_fullname(self):
        if not self.prefix:
            return self.given_name + " " + self.family_name
        return self.prefix + " " + self.given_name + " " + self.family_name

    def get_short_fullname(self):
        return self.given_name + "." + self.family_name[0]

    def get_address(self):
        return self.address

    def get_gender(self):
        return self.gender

    def get_birth_date(self):
        return self.birth_date

    # Cholesterol and Blood
    def get_cholesterol(self):
        next_url = self.url_cholesterol()
        while next_url is not False:
            cholesterol_data = requests.get(url=next_url).json()
            next_url = get_next_url(cholesterol_data)
            try:
                cholesterol_data = cholesterol_data['entry']
                for entry in cholesterol_data:
                    item = entry['resource']
                    cholesterol_value = str(item['valueQuantity']['value'])
                    cholesterol_units = str(item['valueQuantity']['unit'])
                    issued = item['issued'][:len('2000-01-01')]
                    date = datetime.strptime(issued, '%Y-%m-%d').date()
                    record = [date, cholesterol_value, cholesterol_units]
                    self.cholesterol_array.append(record)
            except KeyError:  # No Cholesterol Data
                continue

    def cholesterol_latest(self):
        if not self.has_cholesterol():
            return None
        return max(self.cholesterol_array)

    def has_cholesterol(self):
        if not self.cholesterol_array:
            return False
        return True

    def get_blood(self):
        next_url = self.url_blood()
        while next_url is not False:
            blood_data = requests.get(url=next_url).json()
            next_url = get_next_url(blood_data)
            try:
                blood_data = blood_data['entry']
                for entry in blood_data:
                    entry2 = entry['resource']['component']
                    for item in entry2:
                        blood_value = str(item['valueQuantity']['value'])
                        blood_units = str(item['valueQuantity']['unit'])
                        blood_type = str(item['code']['coding'][0]['display'])
                        issued = entry['resource']['issued'][:len('2000-01-01')]
                        date = datetime.strptime(issued, '%Y-%m-%d').date()
                        record = [date, blood_value, blood_units, blood_type]
                        self.blood_array[blood_type].append(record)
            except KeyError:  # No Blood Data
                continue

    def blood_latest(self):
        if not self.has_blood():
            return None
        return [self.diastolic_latest(), self.systolic_latest()]

    def has_blood(self):
        if not self.blood_array["Diastolic Blood Pressure"] and not self.blood_array["Systolic Blood Pressure"]:
            return False
        return True

    def diastolic_latest(self):
        if not self.blood_array["Diastolic Blood Pressure"]:
            return None
        return max(self.blood_array["Diastolic Blood Pressure"])

    def systolic_latest(self):
        if not self.blood_array["Systolic Blood Pressure"]:
            return None
        return max(self.blood_array["Systolic Blood Pressure"])


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
    testPatient = Patient(29163)

    print(testPatient.get_fullname())
    print(testPatient.url_base())
    print(testPatient.url_cholesterol())
    print(testPatient.url_blood())

    print(testPatient.cholesterol_latest())
    print(testPatient.blood_latest())
