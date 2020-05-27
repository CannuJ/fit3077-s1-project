import requests
from datetime import datetime


class Patient:
    def __init__(self, id_num):
        # Patient ID
        self.id = str(id_num)

        patient_data = requests.get(url=self.url_base()).json()

        # Personal Details
        self.prefix = str(patient_data['name'][0]['prefix'][0])
        self.given_name = str(patient_data['name'][0]['given'][0])
        self.family_name = str(patient_data['name'][0]['family'])

        self.gender = str(patient_data['gender'])
        self.birth_date = str(patient_data['birthDate'])
        self.address = str(patient_data['address'][0]['line'][0]) + " " + str(patient_data['address'][0]['city']) \
                       + " " + str(patient_data['address'][0]['state']) + " " \
                       + str(patient_data['address'][0]['country'])

        self.cholesterol_array = []
        self.get_cholesterol()

        self.blood_array = {"Diastolic Blood Pressure": [], "Systolic Blood Pressure": []}
        self.get_blood()

    def fullname(self):
        return self.prefix + " " + self.given_name + " " + self.family_name

    # URLs and Handling

    def url_base(self):
        return "https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/Patient/" + self.id

    def url_cholesterol(self):
        return "https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/Observation?patient=" + self.id + \
               "&code=2093-3&_sort=date"

    def url_blood(self):
        return "https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/Observation?patient=" + self.id + \
               "&code=55284-4&_sort=date"

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
                    issued = item['issued'][:len('2008-10-14')]
                    date = datetime.strptime(issued, '%Y-%m-%d').date()
                    record = [date, cholesterol_value, cholesterol_units]
                    self.cholesterol_array.append(record)
            except KeyError:  # No Cholesterol Data
                continue

    def cholesterol_latest(self):
        if not self.cholesterol_array:
            return None
        return max(self.cholesterol_array)

    def get_blood(self):

        next_url = self.url_blood()
        while next_url is not False:
            blood_data = requests.get(url=next_url).json()
            next_url = get_next_url(blood_data)
            try:
                blood_data = blood_data['entry']
                for entry in blood_data:
                    issued = entry['resource']['issued'][:len('2008-10-14')]
                    date = datetime.strptime(issued, '%Y-%m-%d').date()

                    entry2 = entry['resource']['component']
                    for item in entry2:
                        blood_value = str(item['valueQuantity']['value'])
                        blood_units = str(item['valueQuantity']['unit'])
                        blood_type = str(item['code']['coding'][0]['display'])

                        record = [date, blood_value, blood_units, blood_type]
                        self.blood_array[blood_type].append(record)
            except KeyError:  # No Blood Data
                continue

    def blood_latest(self):
        if not self.blood_array:
            return None
        return [self.diastolic_latest(), self.systolic_latest()]

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


testPatient = Patient(29163)

print(testPatient.fullname())
print(testPatient.url_base())
print(testPatient.url_cholesterol())
print(testPatient.url_blood())

print(testPatient.cholesterol_latest())
print(testPatient.blood_latest())
