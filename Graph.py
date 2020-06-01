from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def total_cholesterol_graph(window, practitioner):
    #Get the corresponding dataframe ready
    patient_list = practitioner.get_patient_list()
    name_list = []
    cholesterol_list = []

    for patient_id in patient_list:
        patient = practitioner.get_patient(patient_id)
        name = patient.get_fullname()
        name_list.append(name)

        cholesterol_latest = float(patient.cholesterol_latest()[1])
        cholesterol_list.append(cholesterol_latest)

    cholesterol_data = {'Patient Name': name_list,
            'Cholesterol value': cholesterol_list}

    cholesterol_dataframe = DataFrame(cholesterol_data, columns=['Patient Name', 'Cholesterol value'])

    #Construct graph
    figure = plt.Figure(figsize=(4,4), dpi=100)
    ax = figure.add_subplot(111)
    bar = FigureCanvasTkAgg(figure, window)
    graph = bar.get_tk_widget()

    cholesterol_dataframe = cholesterol_dataframe[['Patient Name', 'Cholesterol value']].groupby('Patient Name').sum()
    cholesterol_dataframe.plot(kind='bar', legend=False, ax=ax, fontsize=5)
    ax.set_title('Total Cholesterol mg/dL')

    return graph