#!/usr/bin/env python
# coding: utf-8

# # Access FHIR server and query data in Python

# NOTE: In order to access Monash FHIR server, you need to connect to monash VPN. 

# To make HTTP request with *Python's Request Library*.
# You need to install request with command "pip install requests" and import requests in the script.

# In[3]:


import requests
import pandas as pd
from datetime import datetime


# Provide **root url** for the server.

# In[4]:


root_url = 'https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/'


# ## Example 1

# To get a **specific FHIR resource** from a FHIR server, extend the root url by appending the resource type you are looking for. e.g.[root_url]/Patient will return a bundle including all patients. 

# In[5]:


patients_url = root_url +"Patient"


# To get a particular Patient resource, you would want to use a Patient's id. Simply extend the patient_url by appending the patient's id.

# In[6]:


patient_id_url = patients_url +"/1"


# You can retrieve JSON data using HTTP request and use the builtin **JSON decoder** -json().

# In[7]:


data = requests.get(url=patient_id_url).json()


# In[8]:


data


# ## Example 2 - Search with parameters

# **Each resource type defines the parameters.** To search with parameters, we construct a URL starting with the root url followed by the resource type (e.g. Observation), a question mark character '?' and finished with the search parameters we wish to search, Patient=6430 in this case.

# In[9]:


search1_url = root_url +"Observation?patient=6430"


# To search on a particular observation, we can set the code for that observation. For example, 'total cholesterol' has the the code '2093-3'. So when we want to get the patient's total cholesterol value, we can set 'code=2093-3'.

# In[10]:


search2_url = root_url +"Observation?patient=6430&code=2093-3"


# To manage returned resources, we can use paramter _sort to define the order of results and use _count to define how many results should be displayed in a single page.

# NOTE: In order to keep the load on clidents, servers and the network minimized, the server may choose to return the results in a series of pages. The search result contains the URLs that the client uses to request additional pages from the search set. **The monash FHIR server return results in a series of pages. Each page contains 10 results as default.** Each page contains a URL to the previous page(if not the first page) and the next page(if not the last page). In this case, we use '_count=13' to display all results(13 results) in one page.

# NOTE: _sort=date indicates that results are displayed in increasing order according to the issued date. _sort=-date indicates that results are displayed in decreasing order. 

# In[11]:


search3_url= root_url +"Observation?patient=3689&code=2093-3&_sort=date&_count=13"


# In[12]:


data2 = requests.get(url=search3_url).json()


# In[13]:


data2


# ### Extract data from json data in python

# Json consists of attribute-value pairs and arrays. The above **data2** includes 7 attribute-value pairs: **resourceType, id, meta, type, total, link, entry**.
# Set the attribute name using square brackets, then we can get the corresponding value. data2['entry'] gives an array in this case. 

# In[14]:


entry=data2['entry']


# In[15]:


len(entry)


# In[16]:


Cholesterol_data = pd.DataFrame(columns =['cholestrol', 'issued'] )


# In[17]:


for i in range(len(entry)):
        record=[]
        item = entry[i]['resource']
        weight = item['valueQuantity']['value']
        issued = item['issued']
        record.append(weight)
        record.append(issued)
        Cholesterol_data.loc[i] = record


# In[18]:


Cholesterol_data


# ## Example 3  

# In this example, Urls under 'link' attribute is used to load additional results. (As discussed above, the server will only return a single page with at most 10 records.)<br>
# All patients' cholesterol values (if they are measured) as well as their basic information are recorded.

# In[44]:


dReport_url= root_url +"DiagnosticReport"


# In[45]:


data3 = pd.DataFrame(columns =['patientid','gender', 'birthDate',  'maritualStatus', 'totalCholesterol',"Triglycerides", 'lowDensity', 'highDensity', 'issued'] )


# In[46]:


def checkDate(patient_id,new_date):
    # check whether the observation's issued date is the latest
    if patient_id not in data3.index:
        return True
    else:
        old_date = data3.loc[patient_id,'issued']
        if new_date > old_date:
            data3.drop([patient_id])
            return True
        else:
            return False


# The code below is very computationally expensive, so run with care

# In[47]:


next_page = True
next_url = dReport_url
count_page = 0
count_patient = 0

while next_page == True:
    dReports = requests.get(url=next_url).json()
    
    # As discussed before, The monash FHIR server return results in a series of pages. 
    # Each page contains 10 results as default.
    # here we check and record the next page 
    next_page = False
    links = dReports['link']
    for i in range(len(links)):
        link=links[i]
        if link['relation'] == 'next':
            next_page = True
            next_url = link['url']
            count_page += 1
            
    # Extract data 
    entry = dReports['entry']
    for i in range(len(entry)):
        patient_array = []
        results = entry[i]['resource']['result']
        
        # Check whether this observation is on chterol or not.
        chterol = False
        for result in results:
            if result['display'] == 'Total Cholesterol':
                chterol = True
        
        # If this observation is on cholesterol value, then record the patient's id and issued date.
        if chterol == True:
            patient_id = entry[i]['resource']['subject']['reference'][len('Patient/'):]
            issued = entry[i]['resource']['issued'][:len('2008-10-14')]
            date = datetime.strptime(issued, '%Y-%m-%d').date()

            # Get patient's basic information
            patient_data = requests.get(url = root_url+"Patient/"+patient_id).json()
            gender = patient_data['gender']
            birth = patient_data['birthDate']
            birthDate = datetime.strptime(birth, '%Y-%m-%d').date()
            maritalStatus = patient_data['maritalStatus']['text']
            
            check = checkDate(patient_id,date)
            
            # Check if the patient's Chterol value has already been recorded in the dataframe
            if check == True:
                count_patient+=1
                patient_array.append(patient_id)
                patient_array.append(gender)
                patient_array.append(birthDate)
                patient_array.append(maritalStatus)
                # Record chtoral(including total, Triglycerides, lowDensity and highDensity) value

                observation_ref = result['reference']
                observation_data = requests.get(url = root_url + observation_ref).json()
                value = observation_data['valueQuantity']['value']
                patient_array.append(value)
                patient_array.append(date)
                print(patient_array)
                data3.append(patient_array)


# # Example 4

# Getting all encouters with patient and practitioner information. Test with Practitioner/1381208 which has the following id http://hl7.org/fhir/sid/us-npi|500 - (https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/Practitioner/1381208)
# 
# - another example you can try iss http://hl7.org/fhir/sid/us-npi|850. This one has more patients.

# In[27]:


encounters_url=root_url+"Encounter?participant.identifier=http://hl7.org/fhir/sid/us-npi|500&_include=Encounter.participant.individual&_include=Encounter.patient"
all_encouters_practitioner = requests.get(url=encounters_url).json()


# In[37]:


all_encouter_data=all_encouters_practitioner['entry']

#let's use a dataframe to store the data
cholesterol_data = pd.DataFrame(columns =['Patient','Cholestrol', 'Date'] )
patient_list=[]

for entry in all_encouter_data:
        item = entry['resource']
        patient = item['subject']['reference']
        
        # let's get the patient id, which we need to search for the cholesterol value
        patient_id=patient.split('/')[1]
        patient_list.append(patient)
        findCholesUrl = root_url +"Observation?patient="+patient_id+"&code=2093-3&_sort=date&_count=13"
        patientChol = requests.get(url=findCholesUrl).json()
        try:
            cholData=patientChol['entry']
            # here we get all cholesterol values recorded for the particular patient
            for entry2 in cholData:
                record=[]
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


# # Example 5

# another way to get the patient data for Practitioner/1381208 which has the following id http://hl7.org/fhir/sid/us-npi|500 - (https://fhir.monash.edu/hapi-fhir-jpaserver/fhir/Practitioner/1381208)

# In[38]:


#patient list for a particular practitioner (Practitioner/1381208) is calculated in example 4

for patient_id in patient_list:
    dReport_url= root_url +"DiagnosticReport/?patient="+patient_id
    dReports = requests.get(url=dReport_url).json()
    # Extract data 
    try:
        entry = dReports['entry']
    except:
        continue
        #no entry
    
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
                observation_data = requests.get(url = root_url + observation_ref).json()
                value = observation_data['valueQuantity']['value']
                patient_array = []
                patient_array.append(patient_id)
                patient_array.append(value)
                patient_array.append(date)
                # this prints the cholesterol data of the patients of a particular practitioner
                print(patient_array)


# Referrences(Good to look at): 
# https://fhir-drills.github.io/simple-patient.html<br>
# https://www.hl7.org/fhir/search.html
