import requests
import os
import json
import time
import shutil
import argparse
from datetime import datetime

def get_bearer_token():
    try:
        response = requests.post(base_url + "/oauth/token", data={"grant_type": "client_credentials"}, auth=(client_id, client_secret))
        # print(response.json())
        if response.status_code != 200:
            raise Exception("Unable to get bearer token")
        else:
            return response.json()["access_token"]
    except Exception as e:
        print("Unable to get bearer token" + response.text)
        print(e)
        return None
    
def initiate_draft(backup_id):
    url = base_url + "/beta/sp-config/drafts"
    now = datetime.now()
    timestamp_string = now.strftime("%Y-%m-%d %H:%M:%S")

    source_tenant_info = get_source_tenant()
    source_tenant = source_tenant_info.get("sourceTenant")
    target_tenant = source_tenant_info.get("targetTenant")
    print("Deploying from tenant: " + source_tenant + " to tenant: " + target_tenant)
    print("Using Backup: " + backup_id)
    print(get_backup_summary(backup_id))
    payload = json.dumps({
        "sourceBackupId": backup_id,
        "name": "Pipeline Draft for Deployment " + timestamp_string,
        "mode": "PROMOTE",
        "sourceTenant": source_tenant
    })
    headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Bearer ' + bearer_token
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
    except Exception as e:
        print("Unable to initiate draft")
        print(e)
        return None
    # print(response.json())

    return response.json().get("jobId")

def get_backup_summary(backup_id):
    url = f"{base_url}/beta/sp-config/backups/{backup_id}/summary"

    headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer ' + bearer_token
    }

    response = requests.request("GET", url, headers=headers)

    return json.dumps(response.json(), indent=4, sort_keys=True)
 

def initiate_deploy():
    url = f"{base_url}/beta/sp-config/deploy"

    payload = json.dumps({
        "draftId": job_id
    })
    headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Bearer ' + bearer_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.json())
    return response.json().get("jobId")

def get_deploy_summary():
    url = f"{base_url}/beta/sp-config/deploy/{deploy_id}/download"

    headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer ' + bearer_token
    }

    response = requests.request("GET", url, headers=headers)

    return json.dumps(response.json(), indent=4, sort_keys=True)

def get_source_tenant():
    url = base_url + "/beta/sp-config/connections"

    headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer ' + bearer_token,
    }

    response = requests.request("GET", url, headers=headers)

    # print(response.json())
    return response.json()[0]
    
if __name__ == "__main__":

    base_url = os.environ["SAIL_BASE_URL"]
    client_id = os.environ["SAIL_CLIENT_ID"]
    client_secret = os.environ["SAIL_CLIENT_SECRET"]

    # Get the bearer token
    print("Getting bearer token")
    bearer_token = get_bearer_token()

    # Initiate the configuration draft 
    print("Initiating draft")
    job_id = initiate_draft()

    # Check for when the draft completes
    time_out = 60
    while(True):
        url = base_url + "/beta/sp-config/drafts/" + job_id
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + bearer_token
        }

        response = requests.request("GET", url, headers=headers)
        if response.json().get("status") == "COMPLETE":
            print("Draft completed")
            break
        elif time_out == 0:
            print("Draft timed out")
            exit(1)
        else:
            print("Draft still in progress")
            time.sleep(1)
        time_out -= 1
    
    # Begin the deployment
    print("Initiating deploy")
    # Here you'd want to have logic to grab the latest backup from your source environment
    deploy_id = initiate_deploy("SOME_BACKUP_ID")
    
    # Check for when the deploy completes
    time_out = 60
    while(True):
        url = base_url + "/beta/sp-config/deploy/" + deploy_id
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + bearer_token
        }

        response = requests.request("GET", url, headers=headers)
        if response.json().get("status") == "COMPLETE" or response.json().get("status") == "FAILED":
            print("Deploy completed")
            break
        elif time_out == 0:
            print("Deploy timed out")
            exit(1)
        else:
            print("Deploy still in progress")
            time.sleep(1)
        time_out -= 1
    
    print("Deploy Summary\n-----------------------------------------------------")
    print(get_deploy_summary())



    
    