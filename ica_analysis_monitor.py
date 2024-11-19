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
import random
###############################################
##############
def get_analysis_info(api_key,project_id,analysis_id):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}"
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        pipeline_info = requests.get(full_url, headers=headers)
    except:
        raise ValueError(f"Could not get pipeline_info for analysis {analysis_id} in project: {project_id}")
    return pipeline_info.json()
##############################
def get_project_id(api_key, project_name):
    projects = []
    pageOffset = 0
    pageSize = 30
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects?search={project_name}&includeHiddenProjects=true&pageOffset={pageOffset}&pageSize={pageSize}"
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectPagedList = requests.get(full_url, headers=headers)
        totalRecords = projectPagedList.json()['totalItemCount']
        while page_number * pageSize < totalRecords:
            projectPagedList = requests.get(full_url, headers=headers)
            for project in projectPagedList.json()['items']:
                projects.append({"name": project['name'], "id": project['id']})
            page_number += 1
            number_of_rows_to_skip = page_number * pageSize
    except:
        raise ValueError(f"Could not get project_id for project: {project_name}")
    if len(projects) > 1:
        raise ValueError(f"There are multiple projects that match {project_name}")
    else:
        return projects[0]['id']
############
def list_project_analyses(api_key,project_id,max_retries=20):
    # List all analyses in a project
    pageOffset = 0
    pageSize = 1000
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses?pageOffset={pageOffset}&pageSize={pageSize}"
    analyses_metadata = []
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectAnalysisPagedList = None
        response_code = 404
        num_tries = 0
        while response_code != 200 and num_tries  < max_retries:
            num_tries += 1
            if num_tries > 1:
                print(f"NUM_TRIES:\t{num_tries}\tTrying to get analyses  for project {project_id}")
            sleep(random.uniform(1, 3))
            projectAnalysisPagedList = requests.get(full_url, headers=headers)
            totalRecords = projectAnalysisPagedList.json()['totalItemCount']
            response_code = projectAnalysisPagedList.status_code
            while page_number * pageSize < totalRecords:
                endpoint = f"/api/projects/{project_id}/analyses?pageOffset={number_of_rows_to_skip}&pageSize={pageSize}"
                full_url = api_base_url + endpoint  ############ create header
                projectAnalysisPagedList = requests.get(full_url, headers=headers)
                for analysis in projectAnalysisPagedList.json()['items']:
                    analyses_metadata.append(analysis)
                page_number += 1
                number_of_rows_to_skip = page_number * pageSize
    except:
        raise ValueError(f"Could not get analyses for project: {project_id}")
    return analyses_metadata
################
def get_project_analysis_id(api_key,project_id,analysis_name):
    desired_analyses_status = ["REQUESTED","INPROGRESS","SUCCEEDED","FAILED"]
    analysis_id  = None
    analyses_list = list_project_analyses(api_key,project_id)
    if analysis_name is not None:
        for aidx,project_analysis in enumerate(analyses_list):
            name_check  = project_analysis['userReference'] == analysis_name 
            status_check = project_analysis['status'] in desired_analyses_status
            if project_analysis['userReference'] == analysis_name and project_analysis['status'] in desired_analyses_status:
                analysis_id = project_analysis['id']
                return analysis_id
    else:
        idx_of_interest = 0
        status_of_interest = analyses_list[idx_of_interest]['status'] 
        current_analysis_id = analyses_list[idx_of_interest]['id'] 
        while status_of_interest not in desired_analyses_status:
            idx_of_interest = idx_of_interest + 1
            status_of_interest = analyses_list[idx_of_interest]['status'] 
            current_analysis_id = analyses_list[idx_of_interest]['id'] 
            print(f"analysis_id:{current_analysis_id} status:{status_of_interest}")
        default_analysis_name = analyses_list[idx_of_interest]['userReference']
        print(f"No user reference provided, will poll the logs for the analysis {default_analysis_name}")
        analysis_id = analyses_list[idx_of_interest]['id']
    return analysis_id
##########################################
def get_analysis_metadata(api_key,project_id,analysis_id):
     # List all analyses in a project
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}"
    analysis_metadata = []
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectAnalysis = requests.get(full_url, headers=headers)
        analysis_metadata = projectAnalysis.json()
        ##print(pprint(analysis_metadata,indent=4))
    except:
        raise ValueError(f"Could not get analyses metadata for project: {project_id}")
    return analysis_metadata

def get_analysis_output(api_key,project_id,analysis_metadata):
    ### assume user has not output the results of analysis to custom directory
    search_query_path = "/" + analysis_metadata['reference'] + "/" 
    search_query_path_str = [re.sub("/", "%2F", x) for x in search_query_path]
    search_query_path = "".join(search_query_path_str)
    datum = []
    pageOffset = 0
    pageSize = 1000
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/data?filePath={search_query_path}&filePathMatchMode=STARTS_WITH_CASE_INSENSITIVE&pageOffset={pageOffset}&pageSize={pageSize}"
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        #print(full_url)
        projectDataPagedList = requests.get(full_url, headers=headers)
        if projectDataPagedList.status_code == 200:
            if 'totalItemCount' in projectDataPagedList.json().keys():
                totalRecords = projectDataPagedList.json()['totalItemCount']
                while page_number * pageSize < totalRecords:
                    endpoint = f"/api/projects/{project_id}/data?filePath={search_query_path}&filePathMatchMode=STARTS_WITH_CASE_INSENSITIVE&pageOffset={pageOffset}&pageSize={pageSize}"
                    full_url = api_base_url + endpoint  ############ create header
                    projectDataPagedList = requests.get(full_url, headers=headers)
                    for projectData in projectDataPagedList.json()['items']:
                        if re.search(analysis_metadata['reference'],projectData['data']['details']['path']) is not None:
                            datum.append({"name": projectData['data']['details']['name'], "id": projectData['data']['id'],
                                    "path": projectData['data']['details']['path']})
                    page_number += 1
                    number_of_rows_to_skip = page_number * pageSize
            else:
                for projectData in projectDataPagedList.json()['items']:
                    if re.search(analysis_metadata['reference'],projectData['data']['details']['path']) is not None:
                        datum.append({"name": projectData['data']['details']['name'], "id": projectData['data']['id'],
                                "path": projectData['data']['details']['path']}) 
        else:
            print(f"Could not get results for project: {project_id} looking for filePath: {search_query_path}")
    except:
        print(f"Could not get results for project: {project_id} looking for filePath: {search_query_path}")
    return datum

def find_db_file(api_key,project_id,analysis_metadata,search_query = "metrics.db"):
    db_file = None
    ### assume user has not output the results of analysis to custom directory
    search_query_path = "/" + analysis_metadata['reference'] + "/" 
    search_query_path_str = [re.sub("/", "%2F", x) for x in search_query_path]
    search_query_path = "".join(search_query_path_str)
    datum = []
    pageOffset = 0
    pageSize = 1000
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/data?filename={search_query}&filenameMatchMode=FUZZY&pageOffset={pageOffset}&pageSize={pageSize}"
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        #print(full_url)
        projectDataPagedList = requests.get(full_url, headers=headers)
        if projectDataPagedList.status_code == 200:
            if 'totalItemCount' in projectDataPagedList.json().keys():
                totalRecords = projectDataPagedList.json()['totalItemCount']
                while page_number * pageSize < totalRecords:
                    endpoint = f"/api/projects/{project_id}/data?filename={search_query}&filenameMatchMode=FUZZY&pageOffset={pageOffset}&pageSize={pageSize}"
                    full_url = api_base_url + endpoint  ############ create header
                    projectDataPagedList = requests.get(full_url, headers=headers)
                    for projectData in projectDataPagedList.json()['items']:
                        if re.search(analysis_metadata['reference'],projectData['data']['details']['path']) is not None:
                            datum.append({"name": projectData['data']['details']['name'], "id": projectData['data']['id'],
                                    "path": projectData['data']['details']['path']})
                    page_number += 1
                    number_of_rows_to_skip = page_number * pageSize
            else:
                for projectData in projectDataPagedList.json()['items']:
                    if re.search(analysis_metadata['reference'],projectData['data']['details']['path']) is not None:
                        datum.append({"name": projectData['data']['details']['name'], "id": projectData['data']['id'],
                                "path": projectData['data']['details']['path']}) 
        else:
            print(f"Could not get results for project: {project_id} looking for filename: {search_query}")
    except:
        print(f"Could not get results for project: {project_id} looking for filename: {search_query}")
    if len(datum) > 0:
        if len(datum) > 1:
            print(f"Found more than 1 matching DB file for project: {project_id}")
            pprint(datum,indent = 4)
        db_file = datum[0]['id']
    return db_file
#####################################################
def get_analysis_steps(api_key,project_id,analysis_id):
     # List all analyses in a project
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}/steps"
    analysis_step_metadata = []
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectAnalysisSteps = requests.get(full_url, headers=headers)
        test_response = projectAnalysisSteps.json()
        if 'items' in test_response.keys():
            for step in projectAnalysisSteps.json()['items']:
                analysis_step_metadata.append(step)
        else:
            print(pprint(test_response,indent=4))
            raise ValueError(f"Could not get analyses steps for project: {project_id}")
    except:
        raise ValueError(f"Could not get analyses steps for project: {project_id}")
    return analysis_step_metadata
#################
###################
def download_data_from_url(download_url,output_name=None):
    command_base = ["wget"]
    if output_name is not None:
        output_name = '"' + output_name + '"' 
        command_base.append("-O")
        command_base.append(f"{output_name}")
    command_base.append(f"{download_url}")
    command_str = " ".join(command_base)
    print(f"Running: {command_str}")
    os.system(command_str)
    return print(f"Downloading from {download_url}")

def download_file(api_key,project_id,data_id,output_path):
    # List all analyses in a project
    api_base_url = os.environ['ICA_BASE_URL']+ "/ica/rest"
    endpoint = f"/api/projects/{project_id}/data/{data_id}:createDownloadUrl"
    download_url = None
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        downloadFile = requests.post(full_url, headers=headers)
        download_url = downloadFile.json()['url']
        download_url = '"' + download_url + '"'
        download_data_from_url(download_url,output_path)
    except:
        raise ValueError(f"Could not get analyses streams for project: {project_id}")

    return print(f"Completed download from {download_url}")
##################
 