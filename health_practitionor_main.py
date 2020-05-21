from Screnn_dimension import get_screen_dimensions
from patient_list import get_patient_list
from Encounter_list import get_all_patient_data
from patient_information import*
import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

root_url = 'https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/'  # Root URL
npi_url = "http://hl7.org/fhir/sid/us-npi"

def remove_patient(info_window, entry, prac_id, additional_id_array,patient_lb,remove_id_array):
    patient = patient_lb.get(patient_lb.curselection())

    remove_id = patient[0]
    remove_id_array.append(remove_id)

    if remove_id in additional_id_array:
        additional_id_array.remove(remove_id)

    create_info_window(info_window, entry, prac_id, True, additional_id_array, remove_id_array)

def add_patient(info_window, entry, prac_id, additional_id_array,remove_id_array):
    create_info_window(info_window, entry, prac_id, True, additional_id_array, remove_id_array)


# This function destroy the information window when user is logging out.
def destroy_info_window(logged_in, info_window):
    if logged_in:
        info_window.destroy()

def failed_login(window):
    """
    Adds a message to login window explaining to user the login attempt failed
    :param window: The window we display this message on
    """
    relogin_text = "Login attempt failed, please try again with your ID or Practitioner Identifier (NPI)."
    Fail_login_label = tk.Label(window, text=relogin_text)
    Fail_login_label.pack()

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
def create_info_window(window, entry, prac_id=None, is_recall=False, additional_id_array=None, remove_id_array=None):
    if additional_id_array is None:
        additional_id_array = []

    if remove_id_array is None:
        remove_id_array = []

    input = entry.get()


    if is_recall is False:
        prac_id = entry.get()
    else:
        additional_id_array.append(input)
        if input in remove_id_array:
            remove_id_array.remove(input)

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

    cholesterol = get_all_patient_data(user_login, additional_id_array, remove_id_array)

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
                                   command=lambda: [add_patient(info_window, entry, prac_id, additional_id_array, remove_id_array,)])

    add_patient_button.pack()


    lb_label = tk.Label(info_window, bg='grey', width=40, text=" ID     Name        Surname      Cholesterol")
    lb_label.pack()

    empty_label = tk.Label(info_window, fg='red', width=50, text="No patient information available")
    if len(cholesterol) == 1:
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
            show_patient_detail(detail_text, patient_lb)])
    history_button.pack()

    remove_button_pressed = tk.IntVar()

    remove_patient_button = tk.Button(info_window, text="Remove Patient ID", width=15, height=2, bg="green", fg="yellow",
                    command = lambda: [remove_patient(info_window, entry, prac_id, additional_id_array,patient_lb, remove_id_array)])

    remove_patient_button.pack()

    history_text.pack()
    detail_text.pack()

    while logged_in:
        print("\nWaiting for user input...")
        out_button.wait_variable(button_pressed)  # Hold until Button is pressed
        history_button.wait_variable(button_pressed)
        add_patient_button.wait_variable(add_button_pressed)
        remove_patient_button.wait_variable(remove_button_pressed)
        window.destroy()
        main()
    info_window.mainloop()


def main():
    # Create and set the login window
    set_login_window()


if __name__ == "__main__":
    main()
