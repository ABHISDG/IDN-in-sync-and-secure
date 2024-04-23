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
    
def initiate_export():
    url = base_url + "/beta/sp-config/export"
    now = datetime.now()
    timestamp_string = now.strftime("%Y-%m-%d %H:%M:%S")

    payload = json.dumps({
    "description": "Pipeline Export " + timestamp_string,
    "excludeTypes": [
        "AUTH_ORG",
        "SOD_POLICY"
    ],
    "includeTypes": [
        "PASSWORD_POLICY",
        "NOTIFICATION_TEMPLATE"
    ],
    "objectOptions": {}
    })
    headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Bearer ' + bearer_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json().get("jobId")

def download_export():
    url = f"{base_url}/beta/sp-config/export/{job_id}/download"

    headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer ' + bearer_token
    }

    response = requests.request("GET", url, headers=headers)

    return response.json().get("objects")
    
if __name__ == "__main__":
    base_url = os.environ["SAIL_BASE_URL"]
    client_id = os.environ["SAIL_CLIENT_ID"]
    client_secret = os.environ["SAIL_CLIENT_SECRET"]

    print("Getting bearer token")
    bearer_token = get_bearer_token()

    print("Initiating export")
    job_id = initiate_export()

    time_out = 60
    while(True):
        url = base_url + "/beta/sp-config/export/" + job_id
        headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + bearer_token
        }

        response = requests.request("GET", url, headers=headers)
        if response.json().get("status") == "COMPLETE":
            print("Export completed")
            break
        elif time_out == 0:
            print("Export timed out")
            exit(1)
        else:
            print("Export still in progress")
            time.sleep(1)
        time_out -= 1
    
    print("Downloading export")
    objects = download_export()

    output_dir = "config-hub-export"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)    
    os.mkdir(output_dir)
    with open(f"{output_dir}/bulk_objects.json", "w") as f:
        json.dump(objects, f, indent=4, sort_keys=True)
    for object in objects:
        print("Writing object to file: " + object["self"]["name"])
        with open(f"{output_dir}/{object['self']['name']}.json", "w") as f:
            json.dump(object, f, indent=4, sort_keys=True)
    