import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401


import traceback
import requests
from typing import Any, Dict, Tuple, List, Optional, Union, cast

''' CONSTANTS '''


''' CLIENT CLASS '''


class Client(BaseClient):
    def __init__(self, username, password, client_id, client_secret, login_url):
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.login_url = login_url

    def login(self):
        url = self.login_url + "/services/oauth2/token"
        headers = {"User-Agent": "DPC XSOAR", "Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        r = requests.post(url, data=data, headers=headers)
        return [r.status_code, r.json()]

    def get_campaign(self, bearer_token, instance_url, campaign_id):
        url = instance_url + "/services/data/v54.0/sobjects/Campaign/" + campaign_id
        headers = {"User-Agent": "DPC XSOAR", "Authorization": "Bearer " + bearer_token}
        r = requests.get(url, headers=headers)
        return [r.status_code, r.json()]

    def get_campaign_members(self, bearer_token, instance_url, campaign_id):
        url = instance_url + "/services/data/v54.0/query/"
        headers = {"User-Agent": "DPC XSOAR", "Authorization": "Bearer " + bearer_token}
        data = {
            "q": f"SELECT Id,ContactId,Name,Email,CompanyOrAccount from CampaignMember WHERE CampaignId='{campaign_id}'"
        }
        r = requests.get(url, params=data, headers=headers)
        return [r.status_code, r.json()]

    def get_campaign_member_data(self, bearer_token, instance_url, member_id):
        url = instance_url + "/services/data/v54.0/sobjects/CampaignMember/" + member_id
        headers = {"User-Agent": "DPC XSOAR", "Authorization": "Bearer " + bearer_token}
        r = requests.get(url, headers=headers)
        return [r.status_code, r.json()]

    def get_member_data(self, bearer_token, instance_url, member_id):
        url = instance_url + "/services/data/v54.0/sobjects/Contact/" + member_id
        headers = {"User-Agent": "DPC XSOAR", "Authorization": "Bearer " + bearer_token}
        r = requests.get(url, headers=headers)
        return [r.status_code, r.json()]

    def query(self, bearer_token, instance_url, query):
        url = instance_url + "/services/data/v54.0/query/"
        headers = {"User-Agent": "DPC XSOAR", "Authorization": "Bearer " + bearer_token}
        data = {
            "q": query
        }
        r = requests.get(url, params=data, headers=headers)
        return [r.status_code, r.json()]

    def list_objects(self, bearer_token, instance_url):
        url = instance_url + "/services/data/v54.0/sobjects/"
        headers = {"User-Agent": "DPC XSOAR", "Authorization": "Bearer " + bearer_token}
        r = requests.get(url, headers=headers)
        return [r.status_code, r.json()]


''' HELPER FUNCTIONS '''


def trim_resp(data):
    new_data = {}
    for key in data.keys():
        if data[key] != None and key != "attributes":
            new_data.update({key: data[key]})
    return new_data


''' COMMAND FUNCTIONS '''


def test_module(client: Client) -> str:
    code, data = client.login()
    if code != 200:
        return str(data)

    code2, data2 = client.list_objects(data["access_token"], data["instance_url"])
    if code2 != 200:
        return str(data)
    return 'ok'


def get_campaign_command(client: Client, args: Dict[str, Any]):
    campaign_id = args.get('campaignId', None)
    if not campaign_id:
        raise ValueError('name not specified')

    login_code, login_data = client.login()
    if login_code != 200:
        raise Exception("Failed to login: " + str(login_data))

    code, data = client.get_campaign(login_data["access_token"], login_data["instance_url"], campaign_id)
    if code != 200:
        raise Exception("Failed to execute: " + str(data))

    new_data = trim_resp(data)
    return CommandResults(
        outputs_prefix='Salesforce.Campaign',
        readable_output=new_data,
        outputs=new_data
    )


def get_campaign_members_command(client: Client, args: Dict[str, Any]):
    campaign_id = args.get('campaignId', None)
    if not campaign_id:
        raise ValueError('name not specified')

    login_code, login_data = client.login()
    if login_code != 200:
        raise Exception("Failed to login: " + str(login_data))

    code, data = client.get_campaign_members(login_data["access_token"], login_data["instance_url"], campaign_id)
    if code != 200:
        raise Exception("Failed to execute: " + str(data))

    out = []
    for item in data["records"]:
        out.append(trim_resp(item))
    return CommandResults(
        outputs_prefix='Salesforce.CampaignMember',
        readable_output=out,
        outputs=out
    )


def get_campaign_member_data_command(client: Client, args: Dict[str, Any]):
    memberId = args.get('memberId', None)
    if not memberId:
        raise ValueError('name not specified')

    login_code, login_data = client.login()
    if login_code != 200:
        raise Exception("Failed to login: " + str(login_data))

    code, data = client.get_campaign_member_data(login_data["access_token"], login_data["instance_url"], memberId)
    if code != 200:
        raise Exception("Failed to execute: " + str(data))

    new_data = trim_resp(data)
    return CommandResults(
        outputs_prefix='Salesforce.CampaignMemberData',
        readable_output=new_data,
        outputs=new_data
    )


def get_member_data_command(client: Client, args: Dict[str, Any]):
    memberId = args.get('memberId', None)
    if not memberId:
        raise ValueError('name not specified')

    login_code, login_data = client.login()
    if login_code != 200:
        raise Exception("Failed to login: " + str(login_data))

    code, data = client.get_member_data(login_data["access_token"], login_data["instance_url"], memberId)
    if code != 200:
        raise Exception("Failed to execute: " + str(data))

    new_data = trim_resp(data)
    return CommandResults(
        outputs_prefix='Salesforce.MemberData',
        readable_output=new_data,
        outputs=new_data
    )


def query_command(client: Client, args: Dict[str, Any]):
    query = args.get('query', None)
    if not query:
        raise ValueError('name not specified')

    login_code, login_data = client.login()
    if login_code != 200:
        raise Exception("Failed to login: " + str(login_data))

    code, data = client.query(login_data["access_token"], login_data["instance_url"], query)
    if code != 200:
        raise Exception("Failed to execute: " + str(data))

    new_data = trim_resp(data)
    return CommandResults(
        outputs_prefix='Salesforce.QueryResponse',
        readable_output=new_data,
        outputs=new_data
    )


''' MAIN FUNCTION '''


def main() -> None:
    """main function, parses params and runs command functions

    :return:
    :rtype:
    """

    username = demisto.params().get('userpass', {}).get('identifier')
    password = demisto.params().get('userpass', {}).get('password')
    client_id = demisto.params().get('clientdata', {}).get('identifier')
    client_secret = demisto.params().get('clientdata', {}).get('password')
    login_url = demisto.params()["login_url"]

    try:
        client = Client(username, password, client_id, client_secret, login_url)

        if demisto.command() == 'test-module':
            # This is the call made when pressing the integration Test button.
            result = test_module(client)
            return_results(result)

        elif demisto.command() == 'sf-get-campaign':
            return_results(get_campaign_command(client, demisto.args()))

        elif demisto.command() == 'sf-get-campaign-members':
            return_results(get_campaign_members_command(client, demisto.args()))

        elif demisto.command() == 'sf-get-campaign-member-data':
            return_results(get_campaign_member_data_command(client, demisto.args()))

        elif demisto.command() == 'sf-get-member-data':
            return_results(get_member_data_command(client, demisto.args()))

        elif demisto.command() == 'sf-query':
            return_results(query_command(client, demisto.args()))

    # Log exceptions and return errors
    except Exception as e:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute {demisto.command()} command.\nError:\n{str(e)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
