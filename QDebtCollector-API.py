#!/usr/bin/env python3

import os
import requests
import urllib3
import json
import time
import logging
from tqdm import tqdm

## Configuration Options ##
domain = "FugitiveLAB"  # Customer name {To be used in the logging}
domain_IP = "https://10.111.2.33/api" # ADE Rules API endpoint URL {Change the IP or FQDN only}
security_token = "c37ab29e-6e33-403b-93d7-651d24e9311d"  # Security token for authentication tenant n/a and {admin/admin}
##End of Configuration ##

api_endpoint = f"{domain_IP}/analytics/rules"  # Rules API endpoint URL 
ade_endpoint = f"{domain_IP}/analytics/ade_rules"  # ade Rules API endpoint URL 
BB_endpoint = f"{domain_IP}/analytics/building_blocks"  # BB API endpoint URL
CEP_endpoint = f"{domain_IP}/config/event_sources/custom_properties"    ## CEP API endpoint URL


# Get the current directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Set up logging
log_file = os.path.join(script_dir, f"{domain}_Rules.log")
logging.basicConfig(filename=log_file, level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

# Disable SSL verification and warnings
session = requests.Session()
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Phase One Deleting Rules
def phase1():
    try:
        # Send a GET request to retrieve the list of rules names, IDs which were created by USER
        headers = {"Range": "items=0-5", "Accept": "application/json", "Content-Type": "application/json", "SEC": security_token}
        headers2 = {"Accept": "application/json", "Content-Type": "application/json", "SEC": security_token}
        response = session.get(f"{api_endpoint}?fields=id%2Cname&filter=origin%20%3D%20%22USER%22", headers=headers)

        if response.status_code == 200:
            # Parse the JSON response
            json_data = response.json()
            total_rules = len(json_data)
            #print(len(json_data))
            #print(json_data)
            successful_deletes = 0
            unsuccessful_deletes = 0

            # Phase 1: Delete Rules
            print("\nPhase 1 of Obrela Debt Collector ...\n")  # Add the header line
            logging.info('Phase 1 of Obrela Debt Collector - Deleting Rules')

            with tqdm(total=total_rules, desc="Deleting Rules", unit="rule",
                      postfix={"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes}) as progress_bar:
                start_time = time.time()  # Start the timer

                for rule in json_data:
                    rule_name = rule["name"]
                    rule_id = rule["id"]

                    # Time to wait for the rule to be deleted, otherwise break
                    timeout = 600

                    if time.time() - start_time > timeout:
                        logging.error('Rule "{}" with id {} was not deleted within the timeout -10 Mins-. Exiting...'.format(rule_name, rule_id))
                        break

                    delete_url = f'{api_endpoint}/{rule_id}'
                    response = session.delete(delete_url, headers=headers2)

                    if response.status_code == 202:
                        delete_command_status = response.json()
                        task_id = delete_command_status["id"]
                        logging.info('Rule "{}" with id {} delete command was accepted. Task ID: {}'.format(rule_name, rule_id, task_id))
                    else:
                        logging.error('Failed to delete rule "{}" with id {}. Response code: {}'.format(rule_name, rule_id, response.status_code))
                        unsuccessful_deletes += 1
                        progress_bar.set_postfix({"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes})
                        progress_bar.update(1)
                        continue

                    task_status_url = f'{api_endpoint}/rule_delete_tasks/{task_id}'
                    while True:
                        response = session.get(task_status_url, headers=headers2)
                        if response.status_code == 200:
                            task_status = response.json()["status"]
                            task_message = response.json()["message"]
                            logging.debug('Rule "{}" with id {} deletion status: {}'.format(rule_name, rule_id, task_status))
                            if task_status == "COMPLETED":
                                successful_deletes += 1
                                logging.info('Rule "{}" with id {} has been successfully deleted.'.format(rule_name, rule_id))
                                break
                            elif task_status == "QUEUED":
                                logging.debug('Waiting in the queue for rule "{}" with id {}. Task status: {}'.format(rule_name, rule_id, task_status))
                                time.sleep(5)  # Wait for 5 seconds before checking the status again
                                continue
                            else:
                                logging.error('Rule "{}" with id {} was not deleted. Error message: {}'.format(rule_name, rule_id, task_message))
                                unsuccessful_deletes += 1
                                break
                        else:
                            logging.error('Failed to retrieve the deletion task status of rule "{}" with id {}. Response code: {}'.format(rule_name, rule_id, response.status_code))
                            break

                    progress_bar.set_postfix({"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes})
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


#Phase Two Deleting Ade Rules
def phase2():
    try:
        # Send a GET request to retrieve the list of ade_rules names, IDs which were created by USER
        ade_headers = {"Range": "items=0-3", "Accept": "application/json", "Content-Type": "application/json", "SEC": security_token}
        ade_headers2 = {"Accept": "application/json", "Content-Type": "application/json", "SEC": security_token}
        response = session.get(f"{ade_endpoint}?fields=id%2Cname", headers=ade_headers)
        #print(response.status_code)

        if response.status_code == 200:
            # Parse the JSON response
            json_data = response.json()
            total_ade_rules = len(json_data)
            #print(len(json_data))
            #print(json_data)
            successful_deletes = 0
            unsuccessful_deletes = 0

            # Phase 2: Delete ade_Rules
            print("\nPhase 2 of Obrela Debt Collector ...\n")  # Add the header line
            logging.info('Phase 2 of Obrela Debt Collector - Deleting ade_Rules')

            with tqdm(total=total_ade_rules, desc="Deleting ade_Rules", unit="rule",
                      postfix={"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes}) as progress_bar:
                start_time = time.time()  # Start the timer

                for rule in json_data:
                    rule_name = rule["name"]
                    rule_id = rule["id"]

                    # Time to wait for the rule to be deleted, otherwise break
                    timeout = 600

                    if time.time() - start_time > timeout:
                        logging.error('ade_Rule "{}" with id {} was not deleted within the timeout -10 Mins-. Exiting...'.format(rule_name, rule_id))
                        break

                    delete_url = f'{ade_endpoint}/{rule_id}'
                    response = session.delete(delete_url, headers=ade_headers2)

                    if response.status_code == 202:
                        delete_command_status = response.json()
                        task_id = delete_command_status["id"]
                        logging.info('ade_Rule "{}" with id {} delete command was accepted. Task ID: {}'.format(rule_name, rule_id, task_id))
                    else:
                        logging.error('Failed to delete ade_rule "{}" with id {}. Response code: {}'.format(rule_name, rule_id, response.status_code))
                        unsuccessful_deletes += 1
                        progress_bar.set_postfix({"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes})
                        progress_bar.update(1)
                        continue

                    task_status_url = f'{ade_endpoint}/ade_rule_delete_tasks/{task_id}'
                    while True:
                        response = session.get(task_status_url, headers=ade_headers2)
                        if response.status_code == 200:
                            task_status = response.json()["status"]
                            task_message = response.json()["message"]
                            logging.debug('ade_Rule "{}" with id {} deletion status: {}'.format(rule_name, rule_id, task_status))
                            if task_status == "COMPLETED":
                                successful_deletes += 1
                                logging.info('ade_Rule "{}" with id {} has been successfully deleted.'.format(rule_name, rule_id))
                                break
                            elif task_status == "QUEUED":
                                logging.debug('Waiting in the queue for ade_rule "{}" with id {}. Task status: {}'.format(rule_name, rule_id, task_status))
                                time.sleep(5)  # Wait for 5 seconds before checking the status again
                                continue
                            else:
                                logging.error('ade_Rule "{}" with id {} was not deleted. Error message: {}'.format(rule_name, rule_id, task_message))
                                unsuccessful_deletes += 1
                                break
                        else:
                            logging.error('Failed to retrieve the deletion task status of ade_rule "{}" with id {}. Response code: {}'.format(rule_name, rule_id, response.status_code))
                            break

                    progress_bar.set_postfix({"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes})
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


#Phase Three Deleting BB 
def phase3():
    try:
        # Send a GET request to retrieve the list of Building Blocks names, IDs which were created by USER
        BB_headers = {"Range": "items=0-2", "Accept": "application/json", "Content-Type": "application/json", "SEC": security_token}
        BB_headers2 = {"Accept": "application/json", "Content-Type": "application/json", "SEC": security_token}
        response = session.get(f"{BB_endpoint}?fields=id%2Cname&filter=origin%20%3D%20%22USER%22", headers=BB_headers)

        if response.status_code == 200:
            # Parse the JSON response
            json_data = response.json()
            total_BB = len(json_data)
            #print(len(json_data))
            successful_deletes = 0
            unsuccessful_deletes = 0

            # Phase 3: Delete BB
            print("\nPhase 3 of Obrela Debt Collector ...\n")  # Add the header line
            logging.info('Phase 3 of Obrela Debt Collector - Deleting Building Blocks')

            with tqdm(total=total_BB, desc="Deleting Building Blocks", unit="BB",
                      postfix={"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes}) as progress_bar:
                start_time = time.time()  # Start the timer

                for BB in json_data:
                    BB_name = BB["name"]
                    BB_id = BB["id"]

                    # Time to wait for the BB to be deleted, otherwise break
                    timeout = 600

                    if time.time() - start_time > timeout:
                        logging.error('BB "{}" with id {} was not deleted within the timeout -10 Mins-. Exiting...'.format(BB_name, BB_id))
                        break

                    delete_url = f'{BB_endpoint}/{BB_id}'
                    response = session.delete(delete_url, headers=BB_headers2)

                    if response.status_code == 202:
                        delete_command_status = response.json()
                        task_id = delete_command_status["id"]
                        logging.info('BB "{}" with id {} delete command was accepted. Task ID: {}'.format(BB_name, BB_id, task_id))
                    else:
                        logging.error('Failed to delete BB "{}" with id {}. Response code: {}'.format(BB_name, BB_id, response.status_code))
                        unsuccessful_deletes += 1
                        progress_bar.set_postfix({"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes})
                        progress_bar.update(1)
                        continue

                    task_status_url = f'{BB_endpoint}/building_block_delete_tasks/{task_id}'
                    while True:
                        response = session.get(task_status_url, headers=BB_headers2)
                        if response.status_code == 200:
                            task_status = response.json()["status"]
                            task_message = response.json()["message"]
                            logging.debug('BB "{}" with id {} deletion status: {}'.format(BB_name, BB_id, task_status))
                            if task_status == "COMPLETED":
                                successful_deletes += 1
                                logging.info('BB "{}" with id {} has been successfully deleted.'.format(BB_name, BB_id))
                                break
                            elif task_status == "QUEUED":
                                logging.debug('Waiting in the queue for BB "{}" with id {}. Task status: {}'.format(BB_name, BB_id, task_status))
                                time.sleep(5)  # Wait for 5 seconds before checking the status again
                                continue
                            else:
                                logging.error('BB "{}" with id {} was not deleted. Error message: {}'.format(BB_name, BB_id, task_message))
                                unsuccessful_deletes += 1
                                break
                        else:
                            logging.error('Failed to retrieve the deletion task status of BB "{}" with id {}. Response code: {}'.format(BB_name, BB_id, response.status_code))
                            break

                    progress_bar.set_postfix({"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes})
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


#Phase Four Deleting Deleting Custom Event Properties (CEPs) 
def phase4():
    try:
        # Send a GET request to retrieve the list of CEPs names, IDs which were created by USER
        CEP_headers = {"Range": "items=0-2", "Accept": "application/json", "Content-Type": "application/json", "SEC": security_token}
        CEP_headers2 = {"Accept": "application/json", "Content-Type": "application/json", "SEC": security_token}
        response = session.get(f"{CEP_endpoint}/regex_properties?fields=identifier%2Cname", headers=CEP_headers)

        if response.status_code == 200:
            # Parse the JSON response
            json_data = response.json()
            total_CEP = len(json_data)
            print(len(json_data))
            successful_deletes = 0
            unsuccessful_deletes = 0

            # Phase 4: Delete CEPs
            print("\nPhase 4 of Obrela Debt Collector ...\n")  # Add the header line
            logging.info('Phase 4 of Obrela Debt Collector - Deleting CEPs')

            with tqdm(total=total_CEP, desc="Deleting CEPs", unit="CEP",
                      postfix={"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes}) as progress_bar:
                start_time = time.time()  # Start the timer

                for CEP in json_data:
                    CEP_name = CEP["name"]
                    CEP_id = CEP["identifier"]

                    # Time to wait for the CEP to be deleted, otherwise break
                    timeout = 600

                    if time.time() - start_time > timeout:
                        logging.error('CEP "{}" was not deleted within the timeout -10 Mins-. Exiting...'.format(CEP_name, CEP_id))
                        break

                    delete_url = f'{CEP_endpoint}/regex_properties/{CEP_id}'
                    response = session.delete(delete_url, headers=CEP_headers2)

                    if response.status_code == 202:
                        delete_command_status = response.json()
                        task_id = delete_command_status["id"]
                        logging.info('CEP"{}" delete command was accepted. Task ID: {}'.format(CEP_name, task_id))
                    else:
                        logging.error('Failed to delete CEP "{}". Response code: {}'.format(CEP_name, response.status_code))
                        unsuccessful_deletes += 1
                        progress_bar.set_postfix({"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes})
                        progress_bar.update(1)
                        continue

                    task_status_url = f'{CEP_endpoint}/regex_property_delete_tasks/{task_id}'
                    while True:
                        response = session.get(task_status_url, headers=CEP_headers2)
                        if response.status_code == 200:
                            task_status = response.json()["status"]
                            task_message = response.json()["message"]
                            logging.debug('CEP "{}" deletion status: {}'.format(CEP_name, task_status))
                            if task_status == "COMPLETED":
                                successful_deletes += 1
                                logging.info('CEP "{}" has been successfully deleted.'.format(CEP_name))
                                break
                            elif task_status == "QUEUED":
                                logging.debug('Waiting in the queue for cep "{}". Task status: {}'.format(CEP_name, task_status))
                                time.sleep(5)  # Wait for 5 seconds before checking the status again
                                continue
                            else:
                                logging.error('CEP "{}" was not deleted. Error message: {}'.format(CEP_name, task_message))
                                unsuccessful_deletes += 1
                                break
                        else:
                            logging.error('Failed to retrieve the deletion task status of CEP "{}". Response code: {}'.format(CEP_name, response.status_code))
                            break

                    progress_bar.set_postfix({"Successful Deletes": successful_deletes, "Unsuccessful Deletes": unsuccessful_deletes})
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
            logging.critical('Failed to connect to {} console and retrieve the list of CEPs. Response code: {}'.format(domain, response.status_code))

    except requests.exceptions.RequestException as e:
        logging.exception('Connection to {} console error: {}'.format(domain, str(e)))


def start_all_phases():
    phase1()
    phase2()
    phase3()
    phase4()

def main():
    while True:
        print(" Obrela DebtCollector - Please choose an option:")
        print("     1. Start Phase 1 - Delete All Custom Rules")
        print("     2. Start Phase 2 - Delete ADE Rules")
        print("     3. Start Phase 3 - Delete Building Blocks (BB)")
        print("     4. Start Phase 4 - Delete Custom Event Properties (CEPs)")
        print("     5. Start All Phases")
        print("     0. Exit")
        choice = input("  Enter your choice: ")

        if choice == "1":
            phase1()
        elif choice == "2":
            phase2()
        elif choice == "3":
            phase3()
        elif choice == "4":
           phase4()
        elif choice == "5":
            start_all_phases()
        elif choice == "0":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
