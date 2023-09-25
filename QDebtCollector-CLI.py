#!/usr/bin/env python3
import os
import requests
import urllib3
import json
import time
import logging
import paramiko
import urllib.parse

## Configuration Options ##
domain = "Fugitivetest-Cli"  # Customer name {To be used in the logging}
domain_IP = "https://10.111.2.33/api" # ADE Rules API endpoint URL {Change the IP or FQDN only}
security_token = "c37ab29e-6e33-403b-93d7-651d24e9311d"  # Security token for authentication tenant n/a and {admin/admin}
ssh_ip = "10.111.2.33"  # SSH IP address
ssh_username = "root"  # SSH username
ssh_password = "Ncode!@#45-2021"  # SSH password
#rule_list = ["encode", "test", "Encode RO: Windows - Suspicious Account Creation", "errorr"]
rule_list = [
            "Encode RO: Windows - Suspicious Account Enabled",
            "Encode RO: Windows - Log Deletion",
            "Encode RO: Windows - Suspicious Account Creation",
            "Encode R: Windows - Audit Policy Changed",
            "errorr",
            "Encode RO: Windows - Domain Trust Added or Removed",
            "non-existance Rule"
            ]
## End of Configuration ##


# Get the current directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Set up logging
log_file = os.path.join(script_dir, f"{domain}_Rules.log")
logging.basicConfig(filename=log_file, level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

# Disable SSL verification and warnings
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

api_endpoint = f"{domain_IP}/analytics/rules"  # Rules API endpoint URL

def connect_to_ssh():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(ssh_ip, username=ssh_username, password=ssh_password)
        print("Connected to SSH successfully!")
        logging.debug("Connected to SSH successfully!")
        return ssh_client
    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your SSH credentials.")
        logging.error("Authentication failed. Please check your SSH credentials.")
    except paramiko.SSHException as ssh_exception:
        print(f"Unable to establish SSH connection: {str(ssh_exception)}")
        logging.error(f"Unable to establish SSH connection: {str(ssh_exception)}")
    except paramiko.Exception as e:
        print(f"An error occurred: {str(e)}")
        logging.error(f"An error occurred: {str(e)}")

    return None

def delete_rule_with_id(rule_id, rule_name, ssh_client):
    command = f'psql -U qradar -c "delete from custom_rule where id={rule_id}"'

    try:
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if "DELETE 1" in output:
            print(f"Deleted rule {rule_name} with ID {rule_id} successfully")
            logging.info(f"Deleted rule {rule_name} with ID {rule_id} successfully")
        else:
            print(f"Failed to delete rule {rule_name} with ID {rule_id}")
            logging.error(f"Failed to delete rule {rule_name} with ID {rule_id}")

    except paramiko.SSHException as ssh_exception:
        print(f"Error occurred while executing SSH command: {str(ssh_exception)}")
        logging.error(f"Error occurred while executing SSH command: {str(ssh_exception)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        logging.error(f"An error occurred: {str(e)}")

def fetch_rule_ids(rule_names):
    try:
        # Send a GET request to retrieve the list of rules names, IDs which match the provided rule names
        # Encode the rule names in the filter parameter
        filter_param = urllib.parse.quote(f'name="{",".join(rule_names)}"')
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "SEC": security_token
        }
        response = requests.get(f"{api_endpoint}?fields=id&filter={filter_param}", headers=headers, verify=False)

        if response.status_code == 200:
            # Parse the JSON response
            json_data = response.json()
            rule_ids = [rule["id"] for rule in json_data]
            logging.info(f"Succesfully retrieved rules. Status code: {response.status_code}")
            return rule_ids

        else:
            print(f"Failed to retrieve rules. Status code: {response.status_code}")
            logging.error(f"Failed to retrieve rules. Status code: {response.status_code}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while retrieving rules: {str(e)}")
        logging.error(f"An error occurred while retrieving rules: {str(e)}")
        return []

# Connect to SSH
ssh_client = connect_to_ssh()

# Fetch rule IDs for the specified rule names
rule_ids = fetch_rule_ids(rule_list)
print("Rule IDs:", rule_ids)

# Perform SSH delete for each rule ID
if ssh_client:
    for rule_name in rule_list:
        rule_ids = fetch_rule_ids([rule_name])
        if rule_ids:
            delete_rule_with_id(rule_ids[0], rule_name, ssh_client)
            logging.info(f"Deleted rule {rule_name} with ID {rule_id} successfully")
        else:
            print(f"Failed to retrieve ID for rule {rule_name}")
            logging.error(f"Failed to retrieve ID for rule {rule_name}")

    ssh_client.close()
