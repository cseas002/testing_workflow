import requests
import json
import codecs
import time
import zipfile
import io
import re

def decode_logs(raw_logs):
    try:
        # Decode using UTF-8
        decoded_logs = codecs.decode(raw_logs, 'utf-8', 'replace')

        # Parse JSON if the logs are in JSON format
        parsed_logs = json.loads(decoded_logs)

        # Print the parsed logs
        print(parsed_logs)

    except Exception as e:
        # Handle decoding or parsing errors
        print(f"Error processing logs: {e}")
        print("Raw Logs:")
        print(raw_logs)

# Define the repository dispatch event payload
payload = {
    "event_type": "trigger-workflow",

}

# Encode payload as JSON
payload_json = json.dumps(payload)

token = "TOKEN"
repo_owner = "cseas002"
repo_name = "testing_workflow"
workflow_name = "python.yml"  
output_file_name = "output.txt"   

# Define GitHub API endpoint
url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches"

# Add your GitHub personal access token
headers = {
    "Accept": "application/vnd.github.everest-preview+json",
    "Authorization": f"token {token}"
}

# Send POST request to trigger workflow
response = requests.post(url, headers=headers, data=payload_json)

# Check if the request was successful
if response.status_code == 204:
    print("Workflow triggered successfully!")

    # Retrieve latest workflow run ID
    url_workflow_runs = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_name}/runs"
    response_runs = requests.get(url_workflow_runs, headers=headers)

    if response_runs.status_code == 200:
        latest_run_id = response_runs.json()["workflow_runs"][0]["id"]
        print(f"Latest Workflow Run ID: {latest_run_id}")

        
        # Set the maximum number of retries
        max_retries = 10
        # Initialize retry counter
        retries = 0
        seconds_waiting = 4
         # Loop until the artifact is available or max retries is reached
        while retries < max_retries:
            # Download artifact
            url_download_artifact = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{latest_run_id}/artifacts"
            response_artifact = requests.get(url_download_artifact, headers=headers)


            print(url_download_artifact)

            if response_artifact.status_code == 200:
                artifacts = response_artifact.json().get("artifacts", [])
                print("Waiting to retrieve the output...")

                if artifacts:
                    # Get the archive_download_url from the API response
                    archive_download_url = artifacts[0]["archive_download_url"]

                    # Download the artifact
                    response_download = requests.get(archive_download_url, headers=headers)

                    if response_download.status_code == 200:
                        # Save the downloaded artifact to a local file
                        with open("downloaded_artifact.zip", "wb") as file:
                            file.write(response_download.content)
                        # Unzip the artifact content
                        with zipfile.ZipFile(io.BytesIO(response_download.content), 'r') as zip_ref:
                            # Extract all contents to a temporary directory
                            zip_ref.extractall('temp_dir')

                        # Print the content of output.txt
                        output_path = f"temp_dir/{output_file_name}"
                        with open(output_path, 'r') as output_file:
                            content = output_file.read()
                            print(f"Content of {output_file_name}: {content}")

                        print("Artifact downloaded and extracted successfully.")
                    else:
                        print(f"Failed to download artifact: {response_download.status_code} - {response_download.text}")
                    
                    break
                
                time.sleep(seconds_waiting)  # Wait and send it again

    else:
        print(f"Failed to retrieve workflow run ID: {response_runs.status_code} - {response_runs.text}")
else:
    print(f"Failed to trigger workflow: {response.status_code} - {response.text}")
