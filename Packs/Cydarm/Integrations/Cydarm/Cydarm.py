from asyncore import read
import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401


import json
import requests
import base64
import dateparser

''' CONSTANTS '''


''' CLIENT CLASS '''


class Client(BaseClient):

    def __init__(self, username, password, endpoint, org):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.org = org

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

    def getDataObject(self, uuid: str):
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        url = self.endpoint + f"/cydarm-api/data/{uuid}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            self.logout(login_token)
            js = r.json()
            data = base64.b64decode(js["bytedata"]).decode()
            js.pop("bytedata")
            js.update({"data": data})
            return js
        return {}
    
    def createCase(self, args: dict):
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        args.update({"org": self.org})

        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        url = self.endpoint + f"/cydarm-api/case"

        if "severity" in args.keys():
            args.update({"severity": int(args["severity"])})

        r = requests.post(url, data=json.dumps(args), headers=headers)

        if r.status_code == 201:
            self.logout(login_token)
            return r.json()
        raise Exception(f"Failed to create case - {r.status_code}: {r.text}")
    
    def addCaseMetadata(self, uuid: str, name: str, value: str):
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        url = self.endpoint + f"/cydarm-api/case/{uuid}/meta"
        data = {
            "create": [
                {
                    "name": name,
                    "value": value
                }
            ]
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        if r.status_code == 204:
            self.logout(login_token)
            return {}
        raise Exception(f"Failed to add Metadata - {r.status_code}: {r.text}")
    
    def addCaseTag(self, uuid: str, tag: str):
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        url = self.endpoint + f"/cydarm-api/case/{uuid}/tag"
        data = {
            "tagValue": tag,

        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        if r.status_code == 200:
            self.logout(login_token)
            return r.json()
        raise Exception(f"Failed to add Tag - {r.status_code}: {r.text}")
    
    def updateCase(self, uuid: str, args: dict):
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        url = self.endpoint + f"/cydarm-api/case/{uuid}"
        r = requests.put(url, headers=headers, data=json.dumps(args))
        if r.status_code == 204:
            self.logout(login_token)
            return {}
        raise Exception(f"Failed to set case status - {r.status_code}: {r.text}")
    
    def createComment(self, uuid: str, data: str, significance: str):
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        url = self.endpoint + f"/cydarm-api/case/{uuid}/data"
        data = {
            "mimeType": "text/plain",
            "significance": significance,
            "data": base64.b64encode(data.encode()).decode()
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        if r.status_code == 201:
            self.logout(login_token)
            return r.json()
        raise Exception(f"Failed to add comment - {r.status_code}: {r.text}")
    
    def createFileComment(self, uuid: str, fileEntryId: str, mimeType: str):
        file_meta = demisto.getFilePath(fileEntryId)
        file_data = open(file_meta["path"], "rb").read()

        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        url = self.endpoint + f"/cydarm-api/case/{uuid}/data"
        data = {
            "mimeType": mimeType,
            "significance": "Comment",
            "data": base64.b64encode(file_data).decode(),
            "fileName": file_meta["name"]
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        if r.status_code == 201:
            self.logout(login_token)
            return r.json()
        raise Exception(f"Failed to add file comment - {r.status_code}: {r.text}")
    
    def uploadStix(self, case_url: str, data_str: str):
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        url = self.endpoint + f"/cydarm-api{case_url}"
        data = {
            "mimeType": "application/stix+json;version=2.1",
            "data": base64.b64encode(data_str.encode()).decode()
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        if r.status_code == 201:
            self.logout(login_token)
            return r.json()
        raise Exception(f"Failed to add comment - {r.status_code}: {r.text}")
    
    def replyComment(self, case_url: str, text: str):
        login_status, login_token = self.login()
        if login_status != 200:
            raise Exception("Failed to login!")
        
        headers = {"User-Agent": "DPC XSOAR", "Accept": "application/json", "x-cydarm-authz": login_token}
        url = self.endpoint + f"/cydarm-api{case_url}"
        data = {
            "mimeType": "text/plain",
            "significance": "Comment",
            "data": base64.b64encode(text.encode()).decode()
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        if r.status_code == 201:
            self.logout(login_token)
            return r.json()
        raise Exception(f"Failed to add comment - {r.status_code}: {r.text}")


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

def get_case_data_stubs(client: Client, uuid: str):
    data = client.getCaseDataStubs(uuid)

    return CommandResults(
        outputs_prefix="Cydarm.CaseDataStub",
        readable_output=data,
        outputs=data
    )

def get_data_object(client: Client, uuid: str):
    data = client.getDataObject(uuid)

    return CommandResults(
        outputs_prefix="Cydarm.CaseData",
        readable_output=data,
        outputs=data
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
        outputs_prefix='Cydarm.UserInfo',
        readable_output=data,
        outputs=data
    )

def create_case(client: Client, args: dict):
    if type(args) != dict:
        raise Exception("Invalid Arguments, not dict type")
    
    if "tags" in args.keys():
        args.update({"tags": args["tags"].split(",")})
    
    data = client.createCase(args)
    return CommandResults(
        outputs_prefix='Cydarm.NewCase',
        readable_output=data,
        outputs=data
    )

def add_case_meta(client: Client, uuid: str, name: str, value: str):
    data = client.addCaseMetadata(uuid, name, value)

    return CommandResults(
        outputs_prefix='Cydarm.CaseMeta',
        readable_output=data,
        outputs=data
    )

def add_case_tag(client: Client, uuid: str, tag: str):
    data = client.addCaseTag(uuid, tag)

    return CommandResults(
        outputs_prefix='Cydarm.CaseTag',
        readable_output=data,
        outputs=data
    )

def update_case(client: Client, uuid: str, args: dict):
    args.pop("uuid")
    data = client.updateCase(uuid, args)

    return CommandResults(
        outputs_prefix='Cydarm.UpdatedCase',
        readable_output=data,
        outputs=data
    )
    
def create_comment(client: Client, uuid: str, significance: str, data: str):
    data = client.createComment(uuid, data, significance)
    return CommandResults(
        outputs_prefix='Cydarm.NewComment',
        readable_output=data,
        outputs=data
    )

def create_file_comment(client: Client, uuid: str, fileEntryId: str, mimeType: str):
    data = client.createFileComment(uuid, fileEntryId, mimeType)
    return CommandResults(
        outputs_prefix='Cydarm.NewComment',
        readable_output=data,
        outputs=data
    )

def create_stix(client: Client, url: str, data_str: str):
    data = client.uploadStix(url, data_str)
    return CommandResults(
        outputs_prefix='Cydarm.StixBundle',
        readable_output=data,
        outputs=data
    )

def reply_comment(client: Client, case_url: str, data_str: str):
    data = client.replyComment(case_url, data_str)
    return CommandResults(
        outputs_prefix='Cydarm.NewComment',
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
    org_name = demisto.params()["org_name"]

    demisto.debug(f'Command being called is {demisto.command()}')
    try:
        client = Client(
            endpoint=base_url,
            username=username,
            password=password,
            org=org_name)

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
        elif demisto.command() == "cydarm-case-data-stubs":
            result = get_case_data_stubs(client, demisto.args()["uuid"])
            return_results(result)
        elif demisto.command() == "cydarm-get-data-object":
            result = get_data_object(client, demisto.args()["uuid"])
            return_results(result)
        elif demisto.command() == "cydarm-get-user":
            result = get_user_info(client)
            return_results(result)
        elif demisto.command() == "cydarm-create-case":
            result = create_case(client, demisto.args())
            return_results(result)
        elif demisto.command() == "cydarm-case-add-meta":
            result = add_case_meta(client, demisto.args()["uuid"], demisto.args()["name"], demisto.args()["value"])
            return_results(result)
        elif demisto.command() == "cydarm-case-add-tag":
            result = add_case_tag(client, demisto.args()["uuid"], demisto.args()["tag"])
            return_results(result)
        elif demisto.command() == "cydarm-case-update":
            result = update_case(client, demisto.args()["uuid"], demisto.args())
            return_results(result)
        elif demisto.command() == "cydarm-case-add-comment":
            result = create_comment(client, demisto.args()["uuid"], demisto.args()["significance"], demisto.args()["data"])
            return_results(result)
        elif demisto.command() == "cydarm-case-add-file-comment":
            result = create_file_comment(client, demisto.args()["uuid"], demisto.args()["file_entryId"], demisto.args()["mime_type"])
            return_results(result)
        elif demisto.command() == "cydarm-case-create-stix":
            result = create_stix(client, demisto.args()["url"], demisto.args()["data"])
            return_results(result)
        elif demisto.command() == "cydarm-reply-comment":
            result = reply_comment(client, demisto.args()["url"], demisto.args()["data"])
            return_results(result)

    # Log exceptions and return errors
    except Exception as e:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute {demisto.command()} command.\nError:\n{str(e)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
