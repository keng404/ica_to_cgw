import requests
from requests.structures import CaseInsensitiveDict
import pprint
from pprint import pprint
import json
import subprocess
import os
import argparse
import re
import sys
from datetime import datetime as dt
import time
from time import sleep
import random

##ICA_BASE_URL = "https://ica.illumina.com/ica"
def logging_statement(string_to_print):
    date_time_obj = dt.now()
    timestamp_str = date_time_obj.strftime("%Y/%b/%d %H:%M:%S:%f")
    #############
    final_str = f"[ {timestamp_str} ] {string_to_print}"
    return print(f"{final_str}")
## helper functions to create objects for the input_data and input_parameters of a 'newly' launched pipeline run
def create_analysis_parameter_input_object(parameter_template):
    parameters = []
    for parameter_item, parameter in enumerate(parameter_template):
        param = {}
        param['code'] = parameter['name']
        if parameter['multiValue'] is False:
            if len(param['values']) > 0:
                param['value'] = parameter['values'][0]
            else:
                param['value'] = ""
        else:
            param['multiValue'] = parameter['values']
        parameters.append(param)
    return parameters


######################
def create_analysis_parameter_input_object_extended(parameter_template, params_to_keep):
    parameters = []
    for parameter_item, parameter in enumerate(parameter_template):
        param = {}
        param['code'] = parameter['name']
        if len(params_to_keep) > 0:
            if param['code'] in params_to_keep or len(params_to_keep) < 1:
                if parameter['multiValue'] is False:
                    if len(parameter['values']) > 0:
                        param['value'] = parameter['values'][0]
                    else:
                        param['value'] = ""
                else:
                    param['multiValue'] = parameter['values']
            else:
                param['value']  = ""
        else:
            if parameter['multiValue'] is False:
                if len(parameter['values']) > 0:
                    param['value'] = parameter['values'][0]
                else:
                    param['value'] = ""
            else:
                param['multiValue'] = parameter['values']           
        parameters.append(param)
    return parameters


######################
def parse_analysis_data_input_example(input_example, inputs_to_keep):
    input_data = []
    for input_item, input_obj in enumerate(input_example):
        input_metadata = {}
        input_metadata['parameter_code'] = input_obj['code']
        data_ids = []
        if len(inputs_to_keep) > 0:
            if input_obj['code'] in inputs_to_keep or len(inputs_to_keep) < 1:
                for inputs_idx, inputs in enumerate(input_obj['analysisData']):
                    data_ids.append(inputs['dataId'])
        else:
            for inputs_idx, inputs in enumerate(input_obj['analysisData']):
                data_ids.append(inputs['dataId'])
        input_metadata['data_ids'] = data_ids
        input_data.append(input_metadata)
    return input_data

##
def get_project_id(api_key, project_name):
    projects = []
    pageOffset = 0
    remainingRecords = 1000
    pageSize = remainingRecords
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    #endpoint = f"/api/projects?search={project_name}&includeHiddenProjects=true&pageOffset={pageOffset}&pageSize={pageSize}"
    endpoint = f"/api/projects"
    full_url = api_base_url + endpoint	############ create header
    #print(f"FULL_URL: {full_url}")
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    data = CaseInsensitiveDict()
    data['search'] = project_name
    data['pageOffSet'] = pageOffset
    data['pageSize'] = pageSize
    data['includeHiddenProjects'] = 'true'
    try:
        projectPagedList = requests.get(full_url, headers=headers,params = data)
        #if 'totalItemCount' in projectPagedList.json().keys():
       # totalRecords = projectPagedList.json()['totalItemCount']
        if 'nextPageToken' in projectPagedList.json().keys():
            nextPageToken = projectPagedList.json()['nextPageToken']
            while remainingRecords > 0:
                endpoint = f"/api/projects?includeHiddenProjects=true&pageToken={nextPageToken}&pageSize={pageSize}"
                full_url = api_base_url + endpoint  ############ create header
                projectPagedList = requests.get(full_url, headers=headers)
                for project in projectPagedList.json()['items']:
                    if project['name'] == project_name:
                        projects.append({"name": project['name'], "id": project['id']})
                page_number += 1
                number_of_rows_to_skip = page_number * pageSize
                nextPageToken = projectPagedList.json()['nextPageToken']
                remainingRecords = projectPagedList.json()['remainingRecords']
        else:
            for project in projectPagedList.json()['items']:
                if project['name'] == project_name:
                    projects.append({"name": project['name'], "id": project['id']})  

    except:
        pprint(projectPagedList,indent = 4)
        raise ValueError(f"Could not get project_id for project: {project_name}")
    if len(projects) > 1:
        pprint(projects)
        raise ValueError(f"There are multiple projects that match {project_name}")
    else:
        return projects[0]['id']
#############################
def get_pipeline_id(pipeline_code, api_key,project_name,project_id=None):
    pipelines = []
    pageOffset = 0
    pageSize = 1000
    page_number = 0
    number_of_rows_to_skip = 0
    # ICA project ID
    if project_id is None:
        project_id = get_project_id(api_key,project_name)
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/pipelines?pageOffset={pageOffset}&pageSize={pageSize}"
    full_url = api_base_url + endpoint	############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        #print(f"FULL_URL: {full_url}")
        pipelinesPagedList = requests.get(full_url, headers=headers)
        if 'totalItemCount' in pipelinesPagedList.json().keys():
            totalRecords = pipelinesPagedList.json()['totalItemCount']
            while page_number*pageSize <  totalRecords:
                endpoint = f"/api/projects/{project_id}/pipelines?pageOffset={number_of_rows_to_skip}&pageSize={pageSize}"
                full_url = api_base_url + endpoint  ############ create header
                #print(f"FULL_URL: {full_url}")
                pipelinesPagedList = requests.get(full_url, headers=headers)
                for pipeline_idx,pipeline in enumerate(pipelinesPagedList.json()['items']):
                    pipelines.append({"code":pipeline['pipeline']['code'],"id":pipeline['pipeline']['id']})
                page_number += 1
                number_of_rows_to_skip = page_number * pageSize
        else:
            for pipeline_idx,pipeline in enumerate(pipelinesPagedList.json()['items']):
                pipelines.append({"code": pipeline['pipeline']['code'], "id": pipeline['pipeline']['id']})
    except:
        raise ValueError(f"Could not get pipeline_id for project: {project_name} and name {pipeline_code}\n")
    for pipeline_item, pipeline in enumerate(pipelines):
        # modify this line below to change the matching criteria ... currently the pipeline_code must exactly match
        if pipeline['code'] == pipeline_code:
             pipeline_id = pipeline['id']
    return pipeline_id
########################
def get_pipeline_metadata(pipeline_id, api_key,project_name,project_id=None):
    pipelines = []
    pageOffset = 0
    pageSize = 1000
    page_number = 0
    number_of_rows_to_skip = 0
    # ICA project ID
    if project_id is None:
        project_id = get_project_id(api_key,project_name)
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/pipelines/{pipeline_id}"
    full_url = api_base_url + endpoint	############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        #print(f"FULL_URL: {full_url}")
        pipelinesPagedList = requests.get(full_url, headers=headers)
    except:
        raise ValueError(f"Could not get pipeline_metadata for project: {project_name} and id {pipeline_id}\n")
    #pprint(pipelinesPagedList.json(),indent=4)
    return pipelinesPagedList.json()

#######################


def get_analysis_storage_id(api_key, storage_label=""):
    storage_id = None
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/analysisStorages"
    full_url = api_base_url + endpoint	############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        # Retrieve the list of analysis storage options.
        api_response = requests.get(full_url, headers=headers)
        #pprint(api_response, indent = 4)
        if storage_label not in ['Large', 'Medium', 'Small','XLarge','2XLarge','3XLarge']:
            print("Not a valid storage_label\n" + "storage_label:" + str(storage_label))
            raise ValueError
        else:
            for analysis_storage_item, analysis_storage in enumerate(api_response.json()['items']):
                if analysis_storage['name'] == storage_label:
                    storage_id = analysis_storage['id']
                    return storage_id
    except :
        raise ValueError(f"Could not find storage id based on {storage_label}")


#######################
def does_folder_exist(folder_name,folder_results):
    num_hits = 0
    folder_id = None
    for result_idx,result in enumerate(folder_results):
        if re.search(folder_name, result['name']) is not None and re.search("fol", result['id']) is not None:
            num_hits = 1
            folder_id = result['id']
    return  num_hits,folder_id

def list_data(api_key,sample_query,project_id):
    datum = []
    pageOffset = 0
    pageSize = 1000
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/data?filePath={sample_query}&filenameMatchMode=FUZZY&filePathMatchMode=STARTS_WITH_CASE_INSENSITIVE&pageOffset={pageOffset}&pageSize={pageSize}"
    full_url = api_base_url + endpoint	############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectDataPagedList = requests.get(full_url, headers=headers)
        if 'totalItemCount' in projectDataPagedList.json().keys():
            totalRecords = projectDataPagedList.json()['totalItemCount']
            while page_number*pageSize <  totalRecords:
                projectDataPagedList = requests.get(full_url, headers=headers)
                for projectData in projectDataPagedList.json()['items']:
                        datum.append({"name":projectData['data']['details']['name'],"id":projectData['data']['id']})
                page_number += 1
                number_of_rows_to_skip = page_number * pageSize
    except:
        raise ValueError(f"Could not get results for project: {project_id} looking for filename: {sample_query}")
    return datum
############
def get_project_analysis(api_key,project_id,analysis_id,max_retries = 5):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}"
    analysis_metadata = None
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        response = None
        response_code = 404
        num_tries = 0
        while response_code != 200 and num_tries < max_retries:
            num_tries = num_tries + 1
            response = requests.get(full_url, headers=headers)
            response_code = response.status_code
            time.sleep(1)
        if num_tries == max_retries and response_code != 200:
            sys.stderr.write(f"Could not get metadata for analysis: {analysis_id}\n")
        else:
            analysis_metadata = response.json()
    except:
        sys.stderr.write(f"Could not get metadata for analysis: {analysis_id}\n")
    return analysis_metadata
############
def list_project_analyses(api_key,project_id):
    # List all analyses in a project
    pageOffset = 0
    remainingRecords = 1000
    pageSize = remainingRecords
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses?pageSize={pageSize}"
    analyses_metadata = []
    full_url = api_base_url + endpoint  ############ create header
    headers = dict()
    headers['accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = f"{api_key}"
    try:
        projectAnalysisPagedList = requests.get(full_url, headers=headers)
        #totalRecords = projectAnalysisPagedList.json()['totalItemCount']
        response_code = projectAnalysisPagedList.status_code
        if 'nextPageToken' in projectAnalysisPagedList.json().keys():
            nextPageToken = projectAnalysisPagedList.json()['nextPageToken']
            while remainingRecords > 0:
                endpoint = f"/api/projects/{project_id}/analyses?pageToken={nextPageToken}&pageSize={pageSize}"
                full_url = api_base_url + endpoint  ############ create header
                projectAnalysisPagedList = requests.get(full_url, headers=headers)
                for analysis in projectAnalysisPagedList.json()['items']:
                    analyses_metadata.append(analysis)
                page_number += 1
                number_of_rows_to_skip = page_number * pageSize
                nextPageToken = projectAnalysisPagedList.json()['nextPageToken']
                remainingRecords = projectAnalysisPagedList.json()['remainingRecords']
                if page_number % 5 == 0:
                    logging_statement(f"ANALYSIS_METADATA_REMAINING_RECORDS: {remainingRecords}")
        else:
            for analysis in projectAnalysisPagedList.json()['items']:
                analyses_metadata.append(analysis) 
    except:
        pprint(projectAnalysisPagedList, indent = 4)
        raise ValueError(f"Could not get analyses for project: {project_id}")
    return analyses_metadata
################
##### code to launch pipeline in ICAv2
def get_input_template(pipeline_code, api_key,project_name, fixed_input_data_fields,params_to_keep=[] , analysis_id=None,project_id=None):
    if project_id is None:
        project_id = get_project_id(api_key, project_name)
    project_analyses = list_project_analyses(api_key,project_id)
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    # users can define an analysis_id of interest
    if analysis_id is None:
        # find most recent analysis_id for the pipeline_code that succeeeded
        analyses_dict = {}
        for analysis_idx,analysis in enumerate(project_analyses):
            if analysis['pipeline']['code'] == pipeline_code and analysis['status'] == "SUCCEEDED":
                analyses_dict[analysis['endDate']] = analysis
        
        sorted_keys = sorted(analyses_dict.keys())
        analysis_id = analyses_dict[sorted_keys[len(sorted_keys)-1]]['id']
        print(f"Using {analysis_id}")
    templates = {}  # a dict that returns the templates we'll use to launch an analysis
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    # grab the input files for the given analysis_id
    input_endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}/inputs"
    full_input_endpoint = api_base_url + input_endpoint
    #print(f"FULL_URL: {full_input_endpoint}")
    try:
        inputs_response = requests.get(full_input_endpoint, headers=headers)
        input_data_example = inputs_response.json()['items']
    except:
        raise ValueError(f"Could not get inputs for the project analysis {analysis_id}")
    # grab the parameters set for the given analysis_id
    parameters_endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}/configurations"
    full_parameters_endpoint = api_base_url + parameters_endpoint
    try:
        parameter_response = requests.get(full_parameters_endpoint, headers=headers)
        parameter_settings = parameter_response.json()['items']
    except:
        raise ValueError(f"Could not get parameters for the project analysis {analysis_id}")
    # return both the input data template and parameter settings for this pipeline
    input_data_template = parse_analysis_data_input_example(input_data_example, fixed_input_data_fields)
    parameter_settings_template = create_analysis_parameter_input_object_extended(parameter_settings,params_to_keep)
    templates['input_data'] = input_data_template
    templates['parameter_settings'] = parameter_settings_template
    return templates


########################
##################################################
#### Conversion functions
def convert_data_inputs(data_inputs):
    converted_data_inputs = []
    for idx,item in enumerate(data_inputs):
        converted_data_input = {}
        converted_data_input['parameterCode'] = item['parameter_code']
        converted_data_input['dataIds'] = item['data_ids']
        converted_data_inputs.append(converted_data_input)
    return converted_data_inputs

def get_activation_code(api_key,project_id,pipeline_id,data_inputs,input_parameters,workflow_language):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/activationCodes:findBestMatchingFor{workflow_language}"
    full_url = api_base_url + endpoint
    #print(full_url)
    ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    ######## create body
    collected_parameters = {}
    collected_parameters["pipelineId"] = pipeline_id
    collected_parameters["projectId"] = project_id
    collected_parameters["analysisInput"] = {}
    collected_parameters["analysisInput"]["objectType"] = "STRUCTURED"
    collected_parameters["analysisInput"]["inputs"] = convert_data_inputs(data_inputs)
    collected_parameters["analysisInput"]["parameters"] = input_parameters
    collected_parameters["analysisInput"]["referenceDataParameters"] = []
    response = requests.post(full_url, headers = headers, data = json.dumps(collected_parameters))
    #pprint(response.json())
    entitlement_details = response.json()
    return entitlement_details['id']

def launch_pipeline_analysis(api_key,project_id,pipeline_id,data_inputs,input_parameters,user_tags,storage_analysis_id,user_pipeline_reference,workflow_language,make_template=False):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analysis:{workflow_language}"
    full_url = api_base_url + endpoint
    if workflow_language == "cwl":
        activation_details_code_id = get_activation_code(api_key,project_id,pipeline_id,data_inputs,input_parameters,"Cwl")
    elif workflow_language == "nextflow":
        activation_details_code_id = get_activation_code(api_key,project_id,pipeline_id,data_inputs,input_parameters,"Nextflow")
    #print(full_url)
    ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v4+json'
    headers['Content-Type'] = 'application/vnd.illumina.v4+json'
    headers['X-API-Key'] = api_key
    ######## create body
    collected_parameters = {}
    collected_parameters['userReference'] = user_pipeline_reference
    collected_parameters['activationCodeDetailId'] = activation_details_code_id
    collected_parameters['analysisStorageId'] = storage_analysis_id
    collected_parameters["tags"] = {}
    collected_parameters["tags"]["technicalTags"] = []
    collected_parameters["tags"]["userTags"] = user_tags
    collected_parameters["tags"]["referenceTags"] = []
    collected_parameters["pipelineId"] = pipeline_id
    collected_parameters["projectId"] = project_id
    collected_parameters["analysisInput"] = {}
    collected_parameters["analysisInput"]["objectType"] = "STRUCTURED"
    collected_parameters["analysisInput"]["inputs"] = convert_data_inputs(data_inputs)
    collected_parameters["analysisInput"]["parameters"] = input_parameters
    collected_parameters["analysisInput"]["referenceDataParameters"] = []
    # Writing to job template to f"{user_pipeline_reference}.job_template.json"
    if make_template is True:
        user_pipeline_reference_alias = user_pipeline_reference.replace(" ","_")
        api_template = {}
        api_template['headers'] = dict(headers)
        api_template['data'] = collected_parameters
        print(f"Writing your API job template out to {user_pipeline_reference_alias}.api_job_template.json for future use.\n")
        with open(f"{user_pipeline_reference_alias}.api_job_template.json", "w") as outfile:
            outfile.write(json.dumps(api_template,indent = 4))
        return(print("Please feel free to edit before submitting"))
    else:
        ##########################################
        response = requests.post(full_url, headers = headers, data = json.dumps(collected_parameters))
        launch_details = response.json()
        if launch_details['status'] == "REQUESTED":
            print("Successfully launched")
            pprint(launch_details, indent=4)
            return launch_details
        else:
            print("Error launching analysis")
            pprint(launch_details, indent=4)
            return None
    return launch_details

############
####
def flatten_list(nested_list):
    def flatten(lst):
        for item in lst:
            if isinstance(item, list):
                flatten(item)
            else:
                flat_list.append(item)

    flat_list = []
    flatten(nested_list)
    return flat_list
    
def get_pipeline_request_template(api_key, project_id, pipeline_name, data_inputs, params,tags, storage_size, pipeline_run_name,workflow_language):
    cli_template_prefix = ["icav2","projectpipelines","start",f"{workflow_language}",f"'{pipeline_name}'","--user-reference",f"{pipeline_run_name}"]
    #### user tags for input
    cli_tags_template = []
    for k,v in enumerate(tags):
        cli_tags_template.append(["--user-tag",v])
    ### data inputs for the CLI command
    cli_inputs_template =[]
    for k in range(0,len(data_inputs)):
        # deal with data inputs with a single value
        if len(data_inputs[k]['data_ids']) < 2 and len(data_inputs[k]['data_ids']) > 0:
            cli_inputs_template.append(["--input",f"{data_inputs[k]['parameter_code']}:{data_inputs[k]['data_ids'][0]}"])
         # deal with data inputs with multiple values
        else:
            v_string = ','.join(data_inputs[k]['data_ids'])
            cli_inputs_template.append(["--input",f"{data_inputs[k]['parameter_code']}:{v_string}"])
    ### parameters for the CLI command        
    cli_parameters_template = []
    for k in range(0,len(params)):
        parameter_of_interest = 'value'
        if 'value' not in params[k].keys():
            parameter_of_interest = 'multiValue'
        # deal with parameters with a single value
        if isinstance(params[k][parameter_of_interest],list) is False:
            if params[k][parameter_of_interest] != "":
                cli_parameters_template.append(["--parameters",f"{params[k]['code']}:'{params[k][parameter_of_interest]}'"])
        else:
            # deal with parameters with multiple values
            if len(params[k][parameter_of_interest])  > 0:
                # remove single-quotes 
                simplified_string = [x.strip('\'') for x in params[k][parameter_of_interest]]
                # stylize multi-value parameters
                v_string = ','.join([f"'{x}'" for x in simplified_string])
                if len(simplified_string) > 1:
                    cli_parameters_template.append(["--parameters",f"{params[k]['code']}:\"{v_string}\""])
                elif len(simplified_string) > 0 and simplified_string[0] != '':
                    cli_parameters_template.append(["--parameters",f"{params[k]['code']}:{v_string}"])
    cli_metadata_template = ["--x-api-key",f"'{api_key}'","--project-id",f"{project_id}","--storage-size",f"{storage_size}"]
    if workflow_language == "cwl":
        cli_metadata_template.append("--type-input STRUCTURED")
    full_cli = [cli_template_prefix,cli_tags_template,cli_inputs_template,cli_parameters_template,cli_metadata_template]
    cli_template = ' '.join(flatten_list(full_cli))
    ######
    pipeline_run_name_alias = pipeline_run_name.replace(" ","_")
    print(f"Writing your cli job template out to {pipeline_run_name_alias}.cli_job_template.txt for future use.\n")
    with open(f"{pipeline_run_name_alias}.cli_job_template.txt", "w") as outfile:
        outfile.write(f"{cli_template}")
    print("Also printing out the CLI template to screen\n")
    return(print(f"{cli_template}\n"))
###################################################
