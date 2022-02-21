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


''' HELPER FUNCTIONS '''


''' COMMAND FUNCTIONS '''


def test_module(client: Client) -> str:
    code, text = client.login()
    if code == 200:
        return 'ok'
    return f"Code: {code}: {text}"


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

    # Log exceptions and return errors
    except Exception as e:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute {demisto.command()} command.\nError:\n{str(e)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
