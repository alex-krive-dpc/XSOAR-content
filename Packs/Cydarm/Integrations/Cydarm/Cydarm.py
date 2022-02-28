import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401


import json
import requests
import base64
import dateparser

''' CONSTANTS '''


''' CLIENT CLASS '''


class Client(BaseClient):

    def __init__(self, username, password, endpoint):
        self.endpoint = endpoint
        self.username = username
        self.password = password

    def login(self) -> str:
        username = base64.b64encode(self.username.encode()).decode("utf-8")
        password = base64.b64encode(self.password.encode()).decode("utf-8")

        url = self.endpoint + "/cydarm-api/auth/password"
        headers = {"User-Agent": "DPC XSOAR", "Content-Type": "application/json", "Accept": "application/json"}
        data = json.dumps({"username": username, "password": password})

        r = requests.post(url, data=data, headers=headers)

        if r.status_code == 200:
            return [r.status_code, r.headers["Access-Token"]]
        return [r.status_code, r.text]

    def logout(self, token: str):
        jti = json.loads(base64.b64decode(token.split(".")[1] + "==="))["jti"]
        url = self.endpoint + "/cydarm-api/auth/session/" + jti
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": token}
        r = requests.delete(url, headers=headers)
        return r.status_code == 200

    def getCaseByLocator(self, locator: str):
        url = self.endpoint + "/cydarm-api/case/locator/" + locator
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")

        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            self.logout(login_token)
            return r.json()
        raise Exception("Failed to get Case: " + r.text)
    
    def getCaseActions(self, uuid: str):
        url = self.endpoint + f"/cydarm-api/case/{uuid}/action"
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            self.logout(login_token)
            return r.json()
        raise Exception("Failed to get Actions: " + r.text)
    
    def getUserInfo(self):
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        jti = json.loads(base64.b64decode(login_token.split(".")[1] + "==="))["jti"]
        url = self.endpoint + "/cydarm-api/auth/session/" + jti
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            self.logout(login_token)
            return r.json()
        raise Exception("Failed to get User data: " + r.text)
    
    def getCaseDataStubs(self, uuid: str):
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        url = self.endpoint + f"/cydarm-api/case/{uuid}/data"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            self.logout(login_token)
            return r.json()
        raise Exception("Failed to get Case data: " + r.text)

    def addCaseData(self, uuid: str, dataString: str, dataSource: str):
        pass


''' HELPER FUNCTIONS '''


''' COMMAND FUNCTIONS '''


def test_module(client: Client) -> str:
    code, text = client.login()
    if code == 200:
        if client.logout(text):
            return 'ok'
        return "Failed to logout??"
    return f"Failed to login - Code: {code}: {text}"


def get_case_by_locator(client: Client, locator: str) -> dict:
    data = client.getCaseByLocator(locator)
    values = ["uuid", "locator", "description", "created", "modified", "org", "assignee", "metadata", "status", "severity", "tags", "closed", "acl"]
    new_data = {key: data[key] for key in values}

    return CommandResults(
        outputs_prefix='Cydarm.Case',
        readable_output=new_data,
        outputs=new_data
    )

def get_case_actions(client: Client, uuid: str):
    data = client.getCaseActions(uuid)

    return CommandResults(
        outputs_prefix='Cydarm.CaseActions',
        readable_output=data,
        outputs=data
    )

def get_user_info(client: Client):
    data = client.getUserInfo()
    values = [""]
    return CommandResults(
        outputs_prefix='Cydarm.CaseActions',
        readable_output=data,
        outputs=data
    )

''' MAIN FUNCTION '''


def main() -> None:
    """main function, parses params and runs command functions

    :return:
    :rtype:
    """

    username = demisto.params().get('login', {}).get('identifier')
    password = demisto.params().get('login', {}).get('password')
    base_url = demisto.params()["endpoint"]

    demisto.debug(f'Command being called is {demisto.command()}')
    try:
        client = Client(
            endpoint=base_url,
            username=username,
            password=password)

        if demisto.command() == 'test-module':
            # This is the call made when pressing the integration Test button.
            result = test_module(client)
            return_results(result)
        elif demisto.command() == "cydarm-case-by-locator":
            result = get_case_by_locator(client, demisto.args()["locator"])
            return_results(result)
        elif demisto.command() == "cydarm-case-actions":
            result = get_case_actions(client, demisto.args()["uuid"])
            return_results(result)

    # Log exceptions and return errors
    except Exception as e:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute {demisto.command()} command.\nError:\n{str(e)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
