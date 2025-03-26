#!/usr/bin/env python
import sys
import os
import argparse
import requests
from requests.structures import CaseInsensitiveDict
import pprint
from pprint import pprint
import json
import time
import re
from time import sleep
from datetime import datetime as dt
import random
#################
def logging_statement(string_to_print):
    date_time_obj = dt.now()
    timestamp_str = date_time_obj.strftime("%Y/%b/%d %H:%M:%S:%f")
    #############
    final_str = f"[ {timestamp_str} ] {string_to_print}"
    return print(f"{final_str}")
def get_analysis_output_listing(api_key,project_id,analysis_id):
     # List all analyses in a project
    api_base_url = "https://ica.illumina.com" + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}/outputs"
    analysis_outputs = []
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectAnalysis = requests.get(full_url, headers=headers)
        analysis_outputs = projectAnalysis.json()
        ##print(pprint(analysis_metadata,indent=4))
    except:
        logging_statement(f"Could not get analyses outputs for project: {project_id} and analysis {analysis_id}")
    return analysis_outputs

def get_projectdata_metadata(api_key,project_id,data_id):
      # List all metadata for a given data_id in a project
    api_base_url = "https://ica.illumina.com" + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/data/{data_id}"
    data_metadata_outputs = []
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectdata_metadata= requests.get(full_url, headers=headers)
        data_metadata_outputs.append({"name": projectdata_metadata.json()['data']['details']['name'],
            "id": projectdata_metadata.json()['data']['id'],
            "path": projectdata_metadata.json()['data']['details']['path']})
        ##print(pprint(analysis_metadata,indent=4))
    except:
        print(f"Could not get analyses outputs for project: {project_id} and analysis {analysis_id}")
    return data_metadata_outputs   

def get_children_data(api_key,project_id,data_id):
    # List all metadata for a given data_id in a project
    pageOffset = 0
    remainingRecords = 1000
    pageSize = remainingRecords
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = "https://ica.illumina.com" + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/data/{data_id}/children"
    children_metadata_outputs = []
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v4+json'
    headers['Content-Type'] = 'application/vnd.illumina.v4+json'
    headers['X-API-Key'] = api_key
    try:
        children_metadata = requests.get(full_url, headers=headers)
        #logging_statement(children_metadata.json()['items'])
        if 'nextPageToken' in children_metadata.json().keys():
            nextPageToken = children_metadata.json()['nextPageToken']
            while remainingRecords > 0:
                children_metadata = requests.get(full_url, headers=headers)
                ####logging_statement(children_metadata.json()['items'])
                for idx,val in enumerate(children_metadata.json()['items']):
                    if 'data' in children_metadata.json()['items'][idx].keys():
                        datum  = children_metadata.json()['items'][idx]['data']
                        #logging_statement("adding data")
                        #logging_statement(datum)
                        datum_to_add = {"name": datum['details']['name'],"id": datum['id'],"path": datum['details']['path']}
                        children_metadata_outputs.append(datum_to_add)
                    else:
                        logging_statement(f"Not sure what to do with {children_metadata.json()['items'][idx]}")
                page_number += 1
                number_of_rows_to_skip = page_number * pageSize
                #logging_statement(f"keys_of_interest: {children_metadata.json().keys()}")
                nextPageToken = children_metadata.json()['nextPageToken']
                remainingRecords = children_metadata.json()['remainingRecords']
                logging_statement("performing ICA analysis data lookup")
                #logging_statement(f"remainingRecords: {remainingRecords}, nextPageToken: {nextPageToken}")
                endpoint = f"/api/projects/{project_id}/data/{data_id}/children?pageToken={nextPageToken}&pageSize={pageSize}"
                full_url = api_base_url + endpoint  
                #logging_statement(f"URL: {full_url}")
        else:
            for idx,val in enumerate(children_metadata.json()['items']):
                datum = children_metadata.json()['items'][idx]['data']
                datum_to_add = {"name": datum['details']['name'],"id": datum['id'],"path": datum['details']['path']}
                children_metadata_outputs.append(datum_to_add)
    except:
        ###logging_statement(f"child metadata {children_metadata.json()}")
        logging_statement(f"Could not get children metadata for project: {project_id} and data {data_id}")
    return children_metadata_outputs 

def get_full_analysis_output(api_key,project_id,analysis_id):
    outputs_of_interest = get_analysis_output_listing(api_key,project_id,analysis_id)
    x = []
    data_id = None
    for idx,item in enumerate(outputs_of_interest['items'][0]['data']):
        data_id = item['dataId']
        data_metadata = get_projectdata_metadata(api_key,project_id,data_id)
        #logging_statement(f"Writing analysis outputs to intermediate file data.json")
        #with open('data.json', 'w', encoding='utf-8') as file:
        #    json.dump(data_metadata,file, ensure_ascii=False, indent=4)
        x.append(data_metadata[0])
    if data_id is not None:
        children_metadata = get_children_data(api_key,project_id,data_id)
        for cm in children_metadata:
            x.append(cm)
    return x