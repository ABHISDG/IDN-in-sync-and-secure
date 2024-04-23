import requests
import os
import json
import time
import shutil
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
    
def initiate_backup():
    url = base_url + "/beta/sp-config/backups"
    now = datetime.now()
    timestamp_string = now.strftime("%Y-%m-%d %H:%M:%S")

    payload = json.dumps({
        "name": "Pipeline Backup " + timestamp_string,
    })
    headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Bearer ' + bearer_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json().get("jobId")

def get_backup_summary():
    url = f"{base_url}/beta/sp-config/backups/{job_id}/summary"

    headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer ' + bearer_token
    }

    response = requests.request("GET", url, headers=headers)

    return json.dumps(response.json(), indent=4, sort_keys=True)
    
if __name__ == "__main__":
    base_url = os.environ["SAIL_BASE_URL"]
    client_id = os.environ["SAIL_CLIENT_ID"]
    client_secret = os.environ["SAIL_CLIENT_SECRET"]

    # Get the bearer token
    print("Getting bearer token")
    bearer_token = get_bearer_token()

    # Initiate the backup
    print("Initiating backup")
    job_id = initiate_backup()

    # Check for when the backup completes
    time_out = 60
    while(True):
        url = base_url + "/beta/sp-config/backups/" + job_id
        headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + bearer_token
        }

        response = requests.request("GET", url, headers=headers)
        if response.json().get("status") == "COMPLETE":
            print("Backup completed")
            break
        elif time_out == 0:
            print("Backup timed out")
            exit(1)
        else:
            print("Backup still in progress")
            time.sleep(1)
        time_out -= 1
    
    print("Backup Summary\n-----------------------------------------------------")
    print(get_backup_summary())

    
    