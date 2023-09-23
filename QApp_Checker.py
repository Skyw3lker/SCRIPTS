#!/usr/bin/python3

import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#QRadar API endpoint and token
#ca_bundle = "C:\\Users\\p.merkourakis\\Desktop\\qradar43_enclabs_xyz.crt"
qradar_url = "https://201.210.11.84/api/gui_app_framework/"
qradar_token = "67f0992b-edd3-46a1-aa53-4adcf8c7a6fy"

# XForce-Portal
xforce_url = "https://api.xforce.ibmcloud.com"
xforce_key = "240226ed-8973-42e0-aa86-8cc9cba6167c"
xforce_pass = "0fc97606-db8c-47e9-965c-b323159cc13f"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {"Accept": "application/json", "SEC": qradar_token}
session = requests.Session()
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

qr_applications = []
xf_applications = []
latest_apps = []
count = 0

try:
    response = session.get('{}/applications'.format(qradar_url), headers=headers)

    if response.status_code == 200:
        json_data = json.loads(response.text)
        seen_names = set()
        print("\n")
        print("Current Applications Installed on SIEM------->\n")
        for item in json_data:
            manifest = item.get('manifest', {})
            name = manifest.get('name', '')
            version = manifest.get('version', '')
            if name and name not in seen_names: #instances are coming as diff apps
                seen_names.add(name)
                count += 1
                name = name.replace('V2', '') # Remove 'V2' from the app name
                name = name.replace('V3', '')
                name = name.replace('V4', '')
                name = name.replace('V5', '')
                print(f"Name: {name}, Version: {version}")
                qr_applications.append({'name': name, 'version': version})
    else:
        print("Error:", response.status_code, response.content)
    
except requests.exceptions.RequestException as e:
    logger.exception('Connection error: {}'.format(str(e)))
print("\n\n")


#XFORCE

proxies = {
   'http': 'http://172.24.5.99:3128',
   'https': 'http://172.24.5.99:3128',
}

URL = "https://api.xforce.ibmcloud.com/hub/extensions/brand/QRADAR_APP"
auth = (xforce_key, xforce_pass)
headers = {
    "Accept": "application/json"
}
response = requests.get(URL, auth=auth, headers=headers, proxies=proxies)

    

if response.status_code == 200:
    data = json.loads(response.text)
    xf_applications.append(data)
    latest_apps = []
    for app in xf_applications[0]['extensions']:
        app_name = app['value']['app_details']['locale']['en']['extension_name']
        app_versions = app['value']['app_versions']
        latest_version = sorted(app_versions.items(), key=lambda x: x[1]['status_date'], reverse=True)[0]
        for qr_app in qr_applications:
            if qr_app['name'].lower() in app_name.lower() and latest_version[0] > qr_app['version']: #case insensitive
                latest_apps.append({'name': app_name, 'latest_version': latest_version[0], 'current_version': qr_app['version']})
                break
    print("Proceed On Upgrading the Following:------->\n")            
    if latest_apps:
        for app in latest_apps:
            print(f"{app['name']}, Current Version -->[{app['current_version']}], Latest Version: -->[{app['latest_version']}]")
    else:
        print("No updates found.")

else:
    print(f"Error {response.status_code}: {response.text}")

