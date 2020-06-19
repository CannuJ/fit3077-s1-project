import numpy as np
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def total_cholesterol_graph(master, practitioner):
    """

    :param master: the master where the graph is outputted on
    :param practitioner: the login practitioner
    :return: graph tkiner component
    """

    #Get the corresponding data ready
    patient_list = practitioner.get_current_page_patient_list()
    name_list = []
    cholesterol_list = []

    for patient_id in patient_list:
        patient = practitioner.get_patient(patient_id)

        if patient.cholesterol_latest() is not None:
            cholesterol_latest = float(patient.cholesterol_latest()[1])
            cholesterol_list.append(cholesterol_latest)

            name = patient.get_short_fullname()
            name_list.append(name)


    #Construct graph
    figure = plt.Figure(figsize=(5,3), dpi=100)
    ax = figure.add_subplot(111)
    bar = FigureCanvasTkAgg(figure, master)
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

def blood_pressure_history_graph(root, practitioner, patient_id):
    """

    :param root: root where the graph is on
    :param practitioner: the login practitioner
    :param patient_id: the id of patient who's blood pressure history is being monitored
    :return:
    """

    bp_list = []
    date_list = []

    patient= practitioner.get_patient(patient_id)
    patient_name = patient.get_fullname()
    full_bp_array = patient.blood_array["Systolic Blood Pressure"].copy()

    for i in range(5):
        latest = full_bp_array.pop(full_bp_array.index(max(full_bp_array)))
        latest_measurement = float(latest[1])
        latest_date = latest[0].strftime("%m/%d/%Y")
        bp_list.insert(0,latest_measurement)
        date_list.insert(0,latest_date)

    data = {'date': date_list,'Systolic blood pressure': bp_list}
    df = DataFrame(data, columns=['date', 'Systolic blood pressure'])

    figure = plt.Figure(figsize=(4.2, 2.4), dpi=100)
    ax = figure.add_subplot(111)
    ax.set_ylabel('mm[Hg]')
    ax.set_xticks(np.arange(5))
    ax.set_xticklabels(date_list,{'fontsize':8})
    line_chart = FigureCanvasTkAgg(figure, root)
    line_chart.get_tk_widget().grid()

    df = df[['date', 'Systolic blood pressure']].groupby('date').sum()
    df.plot(kind='line', ax=ax, color='r',marker='o', fontsize=8)
    ax.set_title(patient_name, fontsize=9)




