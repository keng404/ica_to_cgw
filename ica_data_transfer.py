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
import boto3
from botocore.exceptions import ClientError

##ICA_BASE_URL = "https://ica.illumina.com/ica"
def logging_statement(string_to_print):
    date_time_obj = dt.now()
    timestamp_str = date_time_obj.strftime("%Y/%b/%d %H:%M:%S:%f")
    #############
    final_str = f"[ {timestamp_str} ] {string_to_print}"
    return print(f"{final_str}")
    
### obtain temporary AWS credentials
def get_temporary_credentials(api_key,project_id,data_id):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/data/{data_id}:createTemporaryCredentials"
    full_url = api_base_url + endpoint
    ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    payload = {}
    payload['credentialsFormat'] = "RCLONE"
    ########
    response = requests.post(full_url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        pprint(json.dumps(response.json()),indent=4)
        raise ValueError(f"Could not get temporary credentials for {data_id}")
    return response.json()

def set_temp_credentials(credential_json):
    CREDS = credential_json
    os.environ['AWS_ACCESS_KEY_ID'] = CREDS['rcloneTempCredentials']['config']['access_key_id']
    os.environ['AWS_SESSION_TOKEN'] = CREDS['rcloneTempCredentials']['config']['session_token']
    os.environ['AWS_SECRET_ACCESS_KEY'] = CREDS['rcloneTempCredentials']['config']['secret_access_key']
    return print("Set credentials for upload")


def create_aws_service_object(aws_service_name,credential_json):
   required_aws_obj = boto3.client(
       aws_service_name,
       aws_access_key_id=credential_json['rcloneTempCredentials']['config']['access_key_id'],
       aws_secret_access_key=credential_json['rcloneTempCredentials']['config']['secret_access_key'],
       aws_session_token=credential_json['rcloneTempCredentials']['config']['session_token'],
       region_name = credential_json['rcloneTempCredentials']['config']['region']
   )
   return required_aws_obj

def upload_file(filename,credential_json):
    try:
        s3 = create_aws_service_object('s3',credential_json)
        s3_uri_split = credential_json['rcloneTempCredentials']['filePathPrefix'].split('/')
        bucket = s3_uri_split[0]
        object_name = "/".join(s3_uri_split[1:(len(s3_uri_split))])
        response = s3.upload_file(filename, bucket, object_name)
    except ClientError as e:
        logging.error(e)
    return logging_statement(f"Uploaded {filename}")

def download_file(filename,credential_json):
    try:
        s3 = create_aws_service_object('s3',credential_json)
        s3_uri_split = credential_json['rcloneTempCredentials']['filePathPrefix'].split('/')
        bucket = s3_uri_split[0]
        object_name = "/".join(s3_uri_split[1:(len(s3_uri_split))])
        response = s3.download_file( bucket, object_name,filename)
    except ClientError as e:
        logging.error(e)
    return logging_statement(f"Downloaded {filename}")