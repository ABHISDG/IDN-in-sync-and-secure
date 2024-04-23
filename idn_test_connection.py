import os
import requests
import argparse
from anybadge import Badge
from junit_xml import TestSuite, TestCase
import shutil

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
    
def get_sources():
    try:
        response = requests.get(base_url + "/beta/sources", headers={"Authorization": "Bearer " + access_token})
        if response.status_code != 200:
            raise Exception("Unable to get sources list" + response.text)
        else:
            return response.json()
    except Exception as e:
        print("Unable to get sources list")
        print(e)
        return None
    
def test_connection(sources):
    test_results = []
    for source in sources:
        print(f"Testing connection for {source['name']}")
        try:
            response = requests.post(base_url + f"/beta/sources/{source['id']}/connector/test-configuration", headers={"Authorization": "Bearer " + access_token})
            if response.status_code != 200:
                print("Unable to test connection")
                if response.json()['errorMessage'] == "This application does not support CloudConnector.":
                    print("This connector does not support test connection.")
                    test_results.append({"name": source['name'], "id": source['id'], "status": "SUCCESS", "details": "This connector does not support test connection."})
                else:
                    print(response.text)
            else:
                # print(f"{source['name']} - {response.json()['status']} - {response.json()['details']}")
                test_results.append({"name": source['name'], "id": source['id'], "status": response.json()['status'], "details": response.json()['details']})
        except Exception as e:
            print("Crash when trying to make request.")
            print(e)
            return None
    return test_results

def generate_junit_xml(entries):
    try:
        test_case_list = []
        for entry in entries:
            link = f"{''.join(base_url.split('.api'))}/ui/a/admin/connections/sources/{entry['id']}/menu/base_configuration"
            if entry['status'] != "SUCCESS":
                test_case = TestCase(name=entry['name'], classname='Test Connection', elapsed_sec=0.0, stdout=entry['details'], file=link)
                test_case.add_failure_info(message=entry['details'], output=f"{entry['details']}\n{link}")
            else:
                test_case = TestCase(name=entry["name"], classname="Test Connection", elapsed_sec=0.0, file=link, status="success")
            test_case_list.append(test_case)

        test_suite = TestSuite("Test Connection", test_case_list)
        # print(TestSuite.to_xml_string([test_suite]))
        with open ("junit-test.xml", "w") as f:
            TestSuite.to_file(f, [test_suite], prettyprint=True)
    except Exception as e:
        print("Unable to generate junit xml")
        print(e)

def generate_badge(number_of_failures):
    if os.path.isdir("badges"):
        shutil.rmtree("badges")
    os.mkdir("badges")
    test_connection_badge = Badge(
        label="Test Connection Failures",
        value=number_of_failures,
        thresholds={9999: 'red', 1: 'green'},
        num_value_padding_chars=1
    )
    test_connection_badge.write_badge("badges/test_connection_badge.svg")

def push_badge_to_gitlab():
    test_connection_badge = None
    print("Checking if badge exists")
    try:
        response = requests.get(f"{os.environ['CI_SERVER_URL']}/api/v4/projects/{os.environ['CI_PROJECT_ID']}/badges", headers={"PRIVATE-TOKEN": os.environ['PAT']})
        if response.status_code == 200:
            print("Found badges")
            print(response.json())
        else:
            print("Unable to get badges")
            print(response.text)
        print("Getting badge ids")
        for item in response.json():
            print("Badge name: " + item['name'])
            if item['name'] == "Test Connection Badge":
                test_connection_badge = item['id']
        print("Beginning Badge Provisioning...")
        if test_connection_badge is None:
            print("No Test Connection Badge found. Creating new badge...")
            response  = requests.post(f"{os.environ['CI_SERVER_URL']}/api/v4/projects/{os.environ['CI_PROJECT_ID']}/badges",
                                      headers={"PRIVATE-TOKEN": os.environ['PAT']},
                                      data={
                                        "link_url": f"{os.environ['CI_PROJECT_URL']}/-/pipelines/{os.environ['CI_PIPELINE_ID']}/test_report",
                                        "image_url": f"{os.environ['CI_PROJECT_URL']}/-/jobs/artifacts/{os.environ['CI_DEFAULT_BRANCH']}/raw/badges/test_connection_badge.svg?job={os.environ['CI_JOB_NAME']}",
                                        "name": "Test Connection Badge"
                                      })
            if response.status_code == 201:
                print("Successfully created Test Connection Badge")
            else:
                print("Possible failure creating badge")
                print(response.status_code)
                print(response.text)
        else:
            print("Found existing Test Connection Badge. Updating badge...")
            response = requests.put(f"{os.environ['CI_SERVER_URL']}/api/v4/projects/{os.environ['CI_PROJECT_ID']}/badges/{str(test_connection_badge)}",
                                    headers={"PRIVATE-TOKEN": os.environ['PAT']},
                                    data={
                                        "link_url": f"{os.environ['CI_PROJECT_URL']}/-/pipelines/{os.environ['CI_PIPELINE_ID']}/test_report",
                                        "image_url": f"{os.environ['CI_PROJECT_URL']}/-/jobs/artifacts/{os.environ['CI_DEFAULT_BRANCH']}/raw/badges/test_connection_badge.svg?job={os.environ['CI_JOB_NAME']}",
                                        "name": "Test Connection Badge"
                                    })
            if response.status_code == 200:
                print("Successfully updated Test Connection Badge")
            else:
                print("Possible failure updating badge")
                print(response.status_code)
                print(response.text)

    except Exception as e:
        print("Unable to push badge to gitlab")
        print(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Connection to SailPoint IdentityNow Sources')
    parser.add_argument('-sci','--sail_client_id', help='Client ID for IdentityNow API used as the SAIL_CLIENT_ID environment variable')
    parser.add_argument('-scs', '--sail_client_secret', help='Client Secret for IdentityNow API used as the SAIL_CLIENT_SECRET environment variable')
    parser.add_argument('-sbu', '--sail_base_url', help='Base URL for IdentityNow API used as the SAIL_BASE_URL environment variable')

    args = parser.parse_args()

    client_id = None
    client_secret = None
    base_url = None

    if "SAIL_CLIENT_ID" not in os.environ:
        print("SAIL_CLIENT_ID environment variable not set")
    else:
        client_id = os.environ["SAIL_CLIENT_ID"]
    if "SAIL_CLIENT_SECRET" not in os.environ:
        print("SAIL_CLIENT_SECRET environment variable not set")
    else:
        client_secret = os.environ["SAIL_CLIENT_SECRET"]
    if "SAIL_BASE_URL" not in os.environ:
        print("SAIL_BASE_URL environment variable not set")
    else:
        base_url = os.environ["SAIL_BASE_URL"]
    
    if args.sail_client_id:
        print("Setting client id from argument")
        client_id = args.sail_client_id
    if args.sail_client_secret:
        print("Setting client secret from argument")
        client_secret = args.sail_client_secret
    if args.sail_base_url:
        print("Setting base url from argument")
        base_url = args.sail_base_url
    
    if client_id is None or client_secret is None or base_url is None:
        print("Missing required arguments")
        parser.print_help()
        exit(1)

    print("Getting Access Token")
    access_token = get_bearer_token()

    print("Getting Sources")
    sources = get_sources()

    print("Starting Connection Tests")
    test_results = test_connection(sources)

    print("Printing Results:")
    failed_tests = []
    for result in test_results:
        print(f"{result['name']} - {result['id']} - {result['status']} - {result['details']}\n")
        if result['status'] != "SUCCESS":
            failed_tests.append(result)

    generate_junit_xml(test_results)
    generate_badge(len(failed_tests))

    if "CI" in os.environ:
        print("Running in GitLab pipeline, attempting to push badging to repo")
        push_badge_to_gitlab()

