from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

def total_cholesterol_graph(window, practitioner):
    #Get the corresponding dataframe ready
    patient_list = practitioner.get_patient_list()
    name_list = []
    cholesterol_list = []

    for patient_id in patient_list:
        patient = practitioner.get_patient(patient_id)

        if patient.cholesterol_latest() is not None:
            cholesterol_latest = float(patient.cholesterol_latest()[1])
            cholesterol_list.append(cholesterol_latest)

            name = patient.get_short_fullname()
            name_list.append(name)



    cholesterol_data = {'Patient Name': name_list,
            'Cholesterol value': cholesterol_list}

    cholesterol_dataframe = DataFrame(cholesterol_data, columns=['Patient Name', 'Cholesterol value'])

    #Construct graph
    figure = plt.Figure(figsize=(5,3), dpi=100)
    ax = figure.add_subplot(111)
    bar = FigureCanvasTkAgg(figure, window)
    graph = bar.get_tk_widget()

    x = np.arange(len(name_list))  # the label locations
    width = 0.35  # the width of the bars

    rect = ax.bar(x, cholesterol_list, width, label='Cholesterol')
    ax.set_title('Total Cholesterol mg/dL')
    ax.set_xticks(x)
    ax.set_xticklabels(name_list,{'fontsize':8})

    #Font size of the height label
    plt.rcParams.update({'font.size': 8})

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')

    autolabel(rect)

    return graph