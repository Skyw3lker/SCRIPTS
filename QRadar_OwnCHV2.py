#!/usr/bin/env python3

import os
import requests
import urllib3
import json
import time
import logging
from tqdm import tqdm

## Configuration Options ##
## Remove Range limitation from headers in case of Prod. ##

domain = "Ergo"  # Customer name {To be used in the logging}
domain_IP = "https://qradar.XXXXX.encodemss.soc/api" # ADE Rules API endpoint URL {Change the IP or FQDN only}
security_token = "960cd7a8-d52c-XXXX-XXXX-259683132b33"  # Security token for authentication tenant n/a and {admin/admin}
new_owner = "admin"  # Set the new Owner Name #case sensrivie, must be an exsisted account on the Console
##End of Configuration ##

api_endpoint = f"{domain_IP}/analytics/rules"  # Rules API endpoint URL 
ade_endpoint = f"{domain_IP}/analytics/ade_rules"  # ade Rules API endpoint URL 
BB_endpoint = f"{domain_IP}/analytics/building_blocks"  # BB API endpoint URL


# Get the current directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Set up logging
log_file = os.path.join(script_dir, f"{domain}_OwnCh.log")
logging.basicConfig(filename=log_file, level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

# Disable SSL verification and warnings
session = requests.Session()
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Phase One Changing Custom Rules Owner
def phase1():
    try:
        # Send a GET request to retrieve the list of rules names, IDs which were created by USER
        ## Remove Range limitation from headers in case of Prod. ##
        headers = {"Accept": "application/json", "Content-Type": "application/json", "SEC": security_token}
        #response = session.get(f"{api_endpoint}?fields=id%2Cname&filter=origin%20%3D%20%22USER%22", headers=headers)
        response = session.get(f"{api_endpoint}?fields=id%2Cname&filter=not%20origin%20%3D%20%22SYSTEM%22", headers=headers)

        if response.status_code == 200:
            # Parse the JSON response
            json_data = response.json()
            total_rules = len(json_data)
            print(len(json_data))
            #print(json_data)
            successful_changes = 0
            unsuccessful_changes = 0

            # Phase 1: Changing Rules Owner
            print("\033[1m"+"\nPhase 1 of Obrela Owner Changer [Changing Custom Rules Owner]"+"\033[0m"" ...\n")  # Add the header line
            logging.info('Phase 1 of Obrela Owner Changer - Changing Rules')

            with tqdm(total=total_rules, desc="Changing Rules", unit="rule",
                      postfix={"Successfully Changed": successful_changes, "Unsuccessfully Changed": unsuccessful_changes}) as progress_bar:
                start_time = time.time()  # Start the timer

                for rule in json_data:
                    rule_name = rule["name"]
                    rule_id = rule["id"]

                    # Time to wait for the rule owner to be changed, otherwise break
                    timeout = 600

                    if time.time() - start_time > timeout:
                        logging.error('Owner of Rule "{}" with id {} was not changed to {} within the timeout -10 Mins-. Exiting...'.format(rule_name, rule_id, new_owner))
                        continue
                        #break

                    owner_url = f'{api_endpoint}/{rule_id}'
                    data = {"owner": new_owner}
                    response = session.post(owner_url, headers=headers, json=data)

                    if response.status_code == 200:
                        successful_changes += 1
                        change_command_status = response.json()
                        logging.info('Rule "{}" with id {} owner changing to {} command was accepted.'.format(rule_name, rule_id, new_owner))
                    else:
                        logging.error('Failed to change owner of rule "{}" with id {} to be {}. Response code: {}'.format(rule_name, rule_id, new_owner, response.status_code))
                        unsuccessful_changes += 1

                    progress_bar.set_postfix({"Successfully Changed": successful_changes, "Unsuccessfully Changed": unsuccessful_changes})
                    progress_bar.update(1)                    



                #print(" Execution time = " "--- %.2f seconds ---" % (time.time() - start_time))
                execution_time = time.time() - start_time

                if execution_time < 60:
                    print(" Execution time = %.2f Seconds" % execution_time)
                else:
                    minutes = execution_time // 60
                    seconds = execution_time % 60
                    print(" Execution time = %.2f Minutes" % minutes)

        else:
            logging.critical('Failed to connect to {} console and retrieve the list of Rules. Response code: {}'.format(domain, response.status_code))

    except requests.exceptions.RequestException as e:
        logging.exception('Connection to {} console error: {}'.format(domain, str(e)))


#Phase Two Changing Ade Rules Owner
def phase2():
    try:
        # Send a GET request to retrieve the list of ade_rules names, IDs # ""ADE_Rules has no Origin filter""
        ## Remove Range limitation from headers in case of Prod. ##
        headers = {"Accept": "application/json", "Content-Type": "application/json", "SEC": security_token}
        response = session.get(f"{ade_endpoint}?fields=id%2Cname", headers=headers)
        #print(response.status_code)

        if response.status_code == 200:
            # Parse the JSON response
            json_data = response.json()
            total_ade_rules = len(json_data)
            #print(len(json_data))
            #print(json_data)
            successful_changes = 0
            unsuccessful_changes = 0

            # Phase 2: Changing ade_Rules Owner
            print("\033[1m"+"\nPhase 2 of Obrela Owner Changer [Changing Ade Rules Owner]"+"\033[0m"" ...\n")  # Add the header line
            logging.info('Phase 2 of Obrela Owner Changer - Changing ade_Rules Owner')

            with tqdm(total=total_ade_rules, desc="Changing ade_Rules", unit="rule",
                      postfix={"Successfully Changed": successful_changes, "Unsuccessfully Changed": unsuccessful_changes}) as progress_bar:
                start_time = time.time()  # Start the timer

                for rule in json_data:
                    rule_name = rule["name"]
                    rule_id = rule["id"]

                    # Time to wait for the rule to be deleted, otherwise break
                    timeout = 600

                    if time.time() - start_time > timeout:
                        logging.error('Owner of ade_Rule "{}" with id {} was not changed  to {} within the timeout -10 Mins-. Exiting...'.format(rule_name, rule_id, new_owner))
                        continue
                        #break

                    owner_url = f'{ade_endpoint}/{rule_id}'
                    data = {"owner": new_owner}
                    response = session.post(owner_url, headers=headers, json=data)

                    if response.status_code == 200:
                        successful_changes += 1                    
                        change_command_status = response.json()
                        logging.info('ade_Rule "{}" with id {} owner changing to {} command was accepted.'.format(rule_name, rule_id, new_owner))
                    else:
                        logging.error('Failed to change owner of ade_rule "{}" with id {} to be {}. Response code: {}'.format(rule_name, rule_id, new_owner, response.status_code))
                        unsuccessful_deletes += 1

                    progress_bar.set_postfix({"Successfully Changed": successful_changes, "Unsuccessfully Changed": unsuccessful_changes})
                    progress_bar.update(1)

                #print(" Execution time = " "--- %.2f seconds ---" % (time.time() - start_time))
                execution_time = time.time() - start_time

                if execution_time < 60:
                    print(" Execution time = %.2f Seconds" % execution_time)
                else:
                    minutes = execution_time // 60
                    seconds = execution_time % 60
                    print(" Execution time = %.2f Minutes" % minutes)

        else:
            logging.critical('Failed to connect to {} console and retrieve the list of ade_Rules. Response code: {}'.format(domain, response.status_code))

    except requests.exceptions.RequestException as e:
        logging.exception('Connection to {} console error: {}'.format(domain, str(e)))


#Phase Three Changing BB Owner
def phase3():
    try:
        # Send a GET request to retrieve the list of Building Blocks names, IDs which were created by USER
        ## Remove Range limitation from headers in case of Prod. ##
        headers = {"Accept": "application/json", "Content-Type": "application/json", "SEC": security_token}
        #response = session.get(f"{BB_endpoint}?fields=id%2Cname&filter=origin%20%3D%20%22USER%22", headers=BB_headers)
        response = session.get(f"{api_endpoint}?fields=id%2Cname&filter=not%20origin%20%3D%20%22SYSTEM%22", headers=headers)

        if response.status_code == 200:
            # Parse the JSON response
            json_data = response.json()
            total_BB = len(json_data)
            #print(len(json_data))
            successful_changes = 0
            unsuccessful_changes = 0

            # Phase 3: Delete BB
            print("\033[1m"+"\nPhase 3 of Obrela Owner Changer [Changing BB Owner]"+"\033[0m"" ...\n")  # Add the header line
            logging.info('Phase 3 of Obrela Owner Changer - Changing Building Blocks Owner')

            with tqdm(total=total_BB, desc="Changing Building Blocks Owner", unit="BB",
                      postfix={"Successfully Changed": successful_changes, "Unsuccessfully Changed": unsuccessful_changes}) as progress_bar:
                start_time = time.time()  # Start the timer

                for BB in json_data:
                    BB_name = BB["name"]
                    BB_id = BB["id"]

                    # Time to wait for the BB owner to be changed, otherwise break
                    timeout = 600

                    if time.time() - start_time > timeout:
                        logging.error('Owner of BB "{}" with id {} was not changed to {} within the timeout -10 Mins. Exiting...'.format(BB_name, BB_id, new_owner))
                        continue
                        #break

                    owner_url = f'{BB_endpoint}/{BB_id}'
                    data = {"owner": new_owner}
                    response = session.post(owner_url, headers=headers, json=data)

                    if response.status_code == 200:
                        successful_changes += 1
                        change_command_status = response.json()
                        logging.info('BB "{}" with id {} owner changing to {} command was accepted.'.format(BB_name, BB_id, new_owner))
                    else:
                        logging.error('Failed to change owner of BB "{}" with id {} to be {}. Response code: {}'.format(BB_name, BB_id, new_owner, response.status_code))
                        unsuccessful_changes += 1

                    progress_bar.set_postfix({"Successfully Changed": successful_changes, "Unsuccessfully Changed": unsuccessful_changes})
                    progress_bar.update(1)

                #print(" Execution time = " "--- %.2f seconds ---" % (time.time() - start_time))
                execution_time = time.time() - start_time

                if execution_time < 60:
                    print(" Execution time = %.2f Seconds" % execution_time)
                else:
                    minutes = execution_time // 60
                    seconds = execution_time % 60
                    print(" Execution time = %.2f Minutes" % minutes)


        else:
            logging.critical('Failed to connect to {} console and retrieve the list of Building Blocks. Response code: {}'.format(domain, response.status_code))

    except requests.exceptions.RequestException as e:
        logging.exception('Connection to {} console error: {}'.format(domain, str(e)))


def start_all_phases():
    phase1()
    phase2()
    phase3()

def main():
    while True:
        print("\033[1m"+" Obrela CRE Owner Changer - Please choose an option:"+"\033[0m")
        print("     1. Start Phase 1 - Change Owner of Custom Rules")
        print("     2. Start Phase 2 - Change Owner of ADE Rules")
        print("     3. Start Phase 3 - Change Owner of Building Blocks (BB)")
        print("     4. Start All Phases")
        print("     0. Exit\n")
        choice = input("  Enter your choice: ")

        if choice == "1":
            phase1()
        elif choice == "2":
            phase2()
        elif choice == "3":
            phase3()
        elif choice == "4":
            start_all_phases()
        elif choice == "0":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
