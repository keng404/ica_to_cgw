#!/usr/bin/env python
# every 5/10 minutes or so --- this will be controlled outside of this script?
# lookup project by id or name
# given a project, look up all the analyses associated with it
# subset the analyses to analyses by a particular pipeline
# decide on whether to write which ids to identify which to keep track of
#    - if file exists, check analysis submitted table to see which analyses have been submitted and remove id(s) from our list to keep track of if they have been submitted
# if analyses id SUCCEEDED, run downstream pipeline
#    - create sample manifest file
#    - grab output folder from completed analyses
#    - load in (API) template or craft our own
#    - identify which inputs are hard-coded or not
#    - log in table which analysis id, project id, time submitted for downstream pipeline
import ica_analysis_monitor
import ica_analysis_launch
import argparse
import time
import os
import sys
import requests
from requests.structures import CaseInsensitiveDict
import pprint
from pprint import pprint
import json
from datetime import datetime as dt
import re
### helper functions
def logging_statement(string_to_print):
    date_time_obj = dt.now()
    timestamp_str = date_time_obj.strftime("%Y/%b/%d %H:%M:%S:%f")
    #############
    final_str = f"[ {timestamp_str} ] {string_to_print}"
    return print(f"{final_str}")

def get_data(data_id,project_id):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/data/{data_id}"
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        response = requests.get(full_url, headers=headers)
    except:
        logging_statement(f"data {data_id} not found in project {project_id}")
        return None
    data_metadata = response.json()
    return data_metadata['data']['details']['status']

def link_data(data_to_link,destination_project):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{destination_project}/data/dataLinkingBatch"
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v4+json'
    headers['Content-Type'] = 'application/vnd.illumina.v4+json'
    headers['X-API-Key'] = api_key
    collected_data = {}
    collected_data['items'] = {}
    collected_data['items']['dataId'] = data_to_link
    try:
        response = requests.post(full_url, headers = headers,data = json.dumps(collected_data))
    except:
        raise ValueError(f"Could not  link data: {data_to_link} to {destination_project}")
    link_details = response.json()
    pprint(link_details, indent=4)
    return link_details

def link_batch_status(batch_id,project_id):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{destination_project}/data/dataLinkingBatch/{batch_id}"
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        response = requests.get(full_url, headers = headers,)
    except:
        raise ValueError(f"Could not  link batch status : {batch_id} to {project_id}")
    batch_details = response.json()
    pprint(batch_details, indent=4)
    return batch_details
###################################################
### Here SOURCE and DESTINATION project refer to a BSSH-managed project in ICA and downstream project
### This is in the case where you are using ICA autolaunch but a custom pipeline run in a different ICA project
### In cases where the SOURCE and DESTINATION project are the same ,you only need to provide either the SOURCE project name or id
################
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source_project_id',default=None, type=str, help="SOURCE ICA project id")
    parser.add_argument('--source_project_name',default=None, type=str, help="SOURCE ICA project name")
    parser.add_argument('--destination_project_id',default=None, type=str, help="DESTINATION ICA project id [OPTIONAL]")
    parser.add_argument('--destination_project_name',default=None, type=str, help="DESTINATION ICA project name")
    parser.add_argument('--pipeline_name_to_monitor',default=None, type=str, help="Pipeline name to monitor")
    parser.add_argument('--pipeline_name_to_trigger',default=None, type=str, help="Pipeline name to trigger")
    parser.add_argument('--analyses_monitored_file', default='analyses_monitored_file.txt', type=str, help="ICA analysis id")
    parser.add_argument('--analyses_launched_table', default='analyses_launched_table.txt', type=str, help="ICA analysis name --- analysis user reference")
    parser.add_argument('--api_key_file', default=None, type=str, help="file that contains API-Key")
    parser.add_argument('--api_template_file', default=None, type=str, help="file that contains API template for launching analysis for pipeline")
    parser.add_argument('--server_url', default='https://ica.illumina.com', type=str, help="ICA base URL")
    parser.add_argument('--storage_size', default="Large",const='Large',nargs='?', choices=("Small","Medium","Large","XLarge","2XLarge","3XLarge"), type=str, help="Storage disk size used for job [OPTIONAL].\nSee https://help.ica.illumina.com/reference/r-pricing#compute for more details.\n")
    args, extras = parser.parse_known_args()
    #############
    source_project_id = args.source_project_id
    source_project_name = args.source_project_name
    destination_project_id = args.destination_project_id
    destination_project_name = args.destination_project_name
    pipeline_name_to_monitor = args.pipeline_name_to_monitor
    pipeline_name_to_trigger = args.pipeline_name_to_trigger
    analyses_monitored_file = args.analyses_monitored_file
    analyses_launched_table = args.analyses_launched_table
    storage_size = args.storage_size
    os.environ['ICA_BASE_URL'] = args.server_url
    ###### read in api key file
    my_api_key = None
    logging_statement("Grabbing API Key")
    if args.api_key_file is not None:
        if os.path.isfile(args.api_key_file) is True:
            with open(args.api_key_file, 'r') as f:
                my_api_key = str(f.read().strip("\n"))
    if my_api_key is None:
        raise ValueError("Need API key")

    #### get the project identifiers we need
    if source_project_id is None and source_project_name is not None:
        logging_statement("Grabbing ICA SOURCE PROJECT ID")
        source_project_id = ica_analysis_launch.get_project_id(my_api_key,source_project_name)

    if destination_project_id is None and destination_project_name is None:
        logging_statement("Grabbing ICA DESTINATION PROJECT ID")
        destination_project_name = source_project_name
        destination_project_id = source_project_id
    elif destination_project_id is None and destination_project_name is not None:
        logging_statement("Grabbing ICA DESTINATION PROJECT ID")
        destination_project_id = ica_analysis_launch.get_project_id(my_api_key,destination_project_name)
    if source_project_id is None:
        raise ValueError("Need to provide project name or project id")
    
    if pipeline_name_to_monitor is None:
        raise ValueError("Need to provide pipeline name to monitor")
    else:
        logging_statement("Grabbing ID for pipeline to monitor")
        pipeline_name_to_monitor_id = ica_analysis_launch.get_pipeline_id(pipeline_name_to_monitor,my_api_key,source_project_name,project_id=source_project_id)
        logging_statement(f"{pipeline_name_to_monitor} : {pipeline_name_to_monitor_id} ")
    if pipeline_name_to_trigger is None:
        raise ValueError("Need to provide pipeline name to trigger")
    else:
        logging_statement("Grabbing ID for pipeline to trigger")
        pipeline_name_to_trigger_id = ica_analysis_launch.get_pipeline_id(pipeline_name_to_trigger,my_api_key,destination_project_name,project_id=destination_project_id)
        logging_statement(f"{pipeline_name_to_trigger} : {pipeline_name_to_trigger_id} ")

    ####### now let's set up pipeline analysis by updating the template
    
    ### STEP1: grab analyses of interest to monitor and analysis_ids_of_interest to trigger
    logging_statement("STEP1: grab analyses of interest to monitor and analysis_ids_of_interest to trigger")
    analysis_ids_of_interest = []
    analysis_ids_to_trigger = []

    logging_statement(f"Grabbing analyses for {source_project_id}")
    analyses_list = ica_analysis_monitor.list_project_analyses(my_api_key,source_project_id)

    ### only keeping track of analyses in these status, any analyses aborted or failed will not be monitored
    logging_statement(f"Subsetting analyses_to_monitor and analyses_to_trigger for {source_project_id}")
    desired_analyses_status_to_monitor = ["REQUESTED","INTIALIZED","INPROGRESS",'QUEUED', 'INITIALIZING', 'PREPARING_INPUTS', 'GENERATING_OUTPUTS']
    desired_analyses_status_to_trigger = ["SUCCEEDED"]
    for aidx,project_analysis in enumerate(analyses_list):
        if project_analysis['pipeline']['id'] == pipeline_name_to_monitor_id and project_analysis['status'] in desired_analyses_status_to_monitor:
            analysis_ids_of_interest.append(project_analysis['id'])
        elif project_analysis['pipeline']['id'] == pipeline_name_to_monitor_id and project_analysis['status'] in desired_analyses_status_to_trigger:
            analysis_ids_to_trigger.append(project_analysis['id'])

    ###  STEP2: finialize analyses ids to monitor
    logging_statement(f"STEP2: finialize analyses ids to monitor")
    ### look at analyses ids previously monitored and written to a text file
    analysis_ids_previously_considered = []
    if os.path.exists(analyses_monitored_file) is True:
        logging_statement(f"Reading in previous analyses monitored from {analyses_monitored_file}")
        with open(analyses_monitored_file, 'r') as f:
            analysis_ids_previously_considered = str(f.read().split("\n"))

    ### if there are any analyses ids previously monitored and check  that they are not now ready to trigger
    for analysis_id in analysis_ids_previously_considered:
        if analysis_id not in analysis_ids_to_trigger and analysis_id not in analysis_ids_of_interest:
            analysis_ids_of_interest.append(analysis_id)
    
    if len(analysis_ids_of_interest) > 0:
        logging_statement(f"Writing in analyses monitored from {analyses_monitored_file}")
        with open(analyses_monitored_file, 'w') as f:
            for analysis_id in analysis_ids_of_interest:
                f.write(analysis_id + "\n")    
    else:
        logging_statement(f"No analyses to monitor")

    ###  STEP3: Focus on analyses ids to trigger
    if len(analysis_ids_to_trigger) > 0:
        logging_statement(f"STEP3: Focus on analyses ids to trigger")
        analysis_ids_previously_triggered = {}
        analyses_launched_table_data = []
        if os.path.exists(analyses_launched_table) is True:
            logging_statement(f"Reading in previous analyses monitored from {analyses_launched_table}")
            #### format is analysis_id_monitored,analysis_id_triggered
            with open(analyses_launched_table, 'r') as f:
                analyses_launched_table_data = str(f.read().split("\n"))

        if len(analyses_launched_table_data) > 0:
            for line in analyses_launched_table_data:
                line_split = line.split(",").strip("\n")
                if line_split[0] != "analysis_id_monitored":
                    analysis_ids_previously_triggered[line_split[0]] = line_split[1]

        ### if analysis id is already associated with a 'downstream' analysis (after looking it up in the analyses_launched_table), don't run trigger the downsream analysis
        logging_statement(f"Finalize list of analyses to trigger")
        analysis_ids_to_trigger_final = []
        if len(list(analysis_ids_previously_triggered.keys())) > 0:
            for id in analysis_ids_to_trigger:
                if id not in list(analysis_ids_previously_triggered.keys()):
                    analysis_ids_to_trigger_final.append(id)
        else:
            analysis_ids_to_trigger_final = analysis_ids_to_trigger
        metadata_to_write = {}
        if len(analysis_ids_to_trigger_final) > 0:
            analysis_ids_to_trigger_str = ", ".join(analysis_ids_to_trigger_final)
            logging_statement(f"analyses_to_trigger: {analysis_ids_to_trigger_str}")
            for id in analysis_ids_to_trigger_final: 
                ### otherwise do trigger the downstream analysis, and write pipeline launch metadata to analyses_launched_table
                ### first identify data id of output folder
                logging_statement(f"first identify data id of output folder for the analysis id: {id}")
                analysis_metadata = ica_analysis_launch.get_project_analysis(my_api_key,source_project_id,id)
                analysis_output = ica_analysis_monitor.get_analysis_output(my_api_key,source_project_id,analysis_metadata)
                #### folder path
                search_query_path = "/" + analysis_metadata['reference'] + "/" 
                output_folder_id = None
                for output in analysis_output:
                    if re.search(output['path'],search_query_path) is not None:
                        output_folder_id = output['id']
                logging_statement(f"output folder id is: {output_folder_id}")
                ### if SOURCE ICA PROJECT is not the same as DESTINATION ICA PROJECT, then link the output data
                if source_project_id != destination_project_id:
                    logging_statement(f"Checking if output folder id: {output_folder_id} is in project {destination_project_id}")
                    folder_exists = get_data(output_folder_id,destination_project_id)
                    if folder_exists is None:
                        link_batch_id = link_data(output_folder_id,destination_project_id)
                        link_batch_status = link_batch_status(link_batch_id,destination_project_id)
                        while link_batch_status['status'] != "SUCCEEDED":
                            link_batch_status = link_batch_status(link_batch_id,destination_project_id)
                            time.sleep(3)
                            
                ### TODO: then create sample manifest file for CGW and upload to ICA
                ### read-in template for downstream pipeline if available or create a template
                if args.api_template_file is not None:
                    logging_statement(f"reading in from API pipeline launch template from JSON is not implemented")
                else:
                    pipeline_run_name = f"{id}_test_trigger"
                    input_data_fields_to_keep  = []
                    param_fields_to_keep = []
                    job_templates = ica_analysis_launch.get_input_template(pipeline_name_to_trigger, my_api_key,destination_project_name,input_data_fields_to_keep, param_fields_to_keep,project_id=destination_project_id)
                    my_params = job_templates['parameter_settings']
                    my_data_inputs = job_templates['input_data']
                    pipeline_metadata = ica_analysis_launch.get_pipeline_metadata(pipeline_name_to_trigger_id,my_api_key,destination_project_name,project_id=destination_project_id)
                    workflow_language = pipeline_metadata['pipeline']['language'].lower()
                    my_tags = [pipeline_run_name,"from_orchestrator"]
                    if storage_size is None:
                        storage_size = args.storage_size
                    my_storage_analysis_id = ica_analysis_launch.get_analysis_storage_id(my_api_key, storage_size)
                    #### TODO: custom code to override data inputs
                    for idx,data_input in enumerate(my_data_inputs):
                        if data_input['parameter_code'] == "input_folders":
                            data_input['data_ids'] = [output_folder_id]
                    #####################################
                    ### launch downstream pipeline and collect id of launched analysis
                    logging_statement(f"Launching downstream analysis for {pipeline_run_name}")
                    test_launch = ica_analysis_launch.launch_pipeline_analysis(my_api_key, destination_project_id, pipeline_name_to_trigger_id, my_data_inputs, my_params,my_tags, my_storage_analysis_id, pipeline_run_name,workflow_language)
                    if test_launch is not None:
                        metadata_to_write[id] = test_launch['id']
                ### write pipeline launch metadata (i.e. analysis_id_monitored,analysis_id_triggered) to analyses_launched_table
            if len(list(metadata_to_write.keys()))> 0 :
                if os.path.exists(analyses_launched_table) is True:
                    logging_statement(f"Adding analysis launched from {analyses_launched_table}")
                    #### format is analysis_id_monitored,analysis_id_triggered
                    with open(analyses_launched_table, 'w+') as f:
                        for id in list(metadata_to_write.keys()):
                            line_arr = [id,metadata_to_write[id]]
                            new_str = ",".join(line_arr)
                            f.write(new_str + "\n")
                else:
                    logging_statement(f"Creating {analyses_launched_table}")
                    logging_statement(f"Adding analysis launched from {analyses_launched_table}")
                    #### format is analysis_id_monitored,analysis_id_triggered
                    with open(analyses_launched_table, 'w') as f:
                        line_arr = ["analysis_id_monitored","analysis_id_triggered"]
                        new_str = ",".join(line_arr)
                        f.write(new_str + "\n")
                        for id in list(metadata_to_write.keys()):
                            line_arr = [id,metadata_to_write[id]]
                            new_str = ",".join(line_arr)
                            f.write(new_str + "\n")

        else:
            logging_statement(f"No analyses to trigger")
    else:
        logging_statement(f"No analyses to trigger")
if __name__ == "__main__":
    main()