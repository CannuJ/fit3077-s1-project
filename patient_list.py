from dateutil.parser import parse


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
