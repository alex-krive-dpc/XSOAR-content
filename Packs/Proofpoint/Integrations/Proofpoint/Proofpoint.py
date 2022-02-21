import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401


import urllib3
import traceback
import requests
import csv
import time
from requests.structures import CaseInsensitiveDict
from collections import Counter
from io import StringIO

# Disable insecure warnings
requests.packages.urllib3.disable_warnings()
urllib3.disable_warnings()

''' CONSTANTS '''

''' CLIENT CLASS '''


class Client(BaseClient):
    """Client class to interact with the service API

    This Client implements API calls, and does not contain any Demisto logic.
    Should only do requests and return data.
    It inherits from BaseClient defined in CommonServer Python.
    Most calls use _http_request() that handles proxy, SSL verification, etc.
    For this HelloWorld implementation, no special attributes defined
    """

    def __init__(self, base_url, api_string, instance_name):
        self.base_url = base_url
        self.api_string = api_string
        self.instance_name = instance_name

    def get_domains(self):
        # Returns a list of all domains associated with the proofpoint system linked to the API

        headers = CaseInsensitiveDict()  # type: CaseInsensitiveDict
        headers["Authorization"] = "Basic " + self.api_string

        resp = requests.get(self.base_url + "/domains/names", headers=headers)
        if resp.status_code == 200:
            domains = resp.json()["data"]
            out = []  # type: list
            for domain in domains:
                out.append(domain)
            return out
        else:
            return []

    def get_dmarc_policies(self):
        headers = CaseInsensitiveDict()  # type: CaseInsensitiveDict
        headers["Authorization"] = "Basic " + self.api_string

        resp = requests.get(self.base_url + "/domains", headers=headers)
        policy_data = resp.json()["data"]

        policies = {}
        for line in policy_data:
            policies.update({line["domainName"]: line["dmarc"]["policy"]})
        return policies

    def get_data_for_all(self, previous_days: str):
        """
        Gets the DMARC Pass and Fail count for a list of domains
        Does a single API request for all data and searches through it, rather than seperate calls per domain
        """

        headers = CaseInsensitiveDict()  # type: CaseInsensitiveDict
        headers["Authorization"] = "Basic " + self.api_string
        params = {
            "data_source": "consumer",
            "order_by": "domain",
            "order_dir": "asc",
            "previous_days": previous_days
        }
        url = self.base_url + "/aggregate-results"
        resp = requests.get(url, params=params, headers=headers)

        if resp.status_code != 200:
            return []

        output = []  # type: list
        data = resp.json()["data"]
        policies = self.get_dmarc_policies()

        for entry in data:
            hostname = entry["domainName"]
            result = {
                "Hostname": hostname,
                "InstanceName": self.instance_name,
                "TotalMailCount": entry["totalMailCount"] or 0,
                "BlockedMailCount": entry["blockedMailCount"] or 0,
                "DMARC": entry["dmarc"] or {},
                "SPF": entry["spf"] or {},
                "DKIM": entry["dkim"] or {},
                "Policy": policies.get(hostname) or "N/A"
            }
            if "sender" in entry.keys() and entry["sender"] != None:
                result.update({
                    "SenderName": entry["sender"]["name"] or "N/A",
                    "SenderVerified": entry["sender"]["verified"] or "N/A",
                    "SenderVerifiedStatus": entry["sender"]["verifiedStatus"] or "N/A",
                })
            else:
                result.update({
                    "SenderName":"N/A", 
                    "SenderVerified": "N/A",
                    "SenderVerifiedStatus": "N/A"
                })
            
            output.append(result)

        return output

    def check_api(self):

        headers = CaseInsensitiveDict()  # type: CaseInsensitiveDict
        headers["Authorization"] = "Basic " + self.api_string

        resp = requests.get(self.base_url + "/domains/names", headers=headers)
        return resp.status_code == 200


''' HELPER FUNCTIONS '''

def wait_rate_limit():
    time.sleep(250 / 1000)


''' COMMAND FUNCTIONS '''


def test_module(clients: list) -> str:
    """Tests API connectivity and authentication'

    Returning 'ok' indicates that the integration works like it is supposed to.
    Connection to the service is successful.
    Raises exceptions if something goes wrong.

    :type client: ``Client``
    :param Client: HelloWorld client to use

    :type name: ``str``
    :param name: name to append to the 'Hello' string

    :return: 'ok' if test passed, anything else will fail the test.
    :rtype: ``str``
    """

    # INTEGRATION DEVELOPER TIP
    # Client class should raise the exceptions, but if the test fails
    # the exception text is printed to the Cortex XSOAR UI.
    # If you have some specific errors you want to capture (i.e. auth failure)
    # you should catch the exception here and return a string with a more
    # readable output (for example return 'Authentication Error, API Key
    # invalid').
    # Cortex XSOAR will print everything you return different than 'ok' as
    # an error

    for client in clients:
        if not client.check_api():
            return f"Authorization Error for {client.instance_name}"
        wait_rate_limit()

    return 'ok'


def get_domains_command(clients: list) -> CommandResults:
    domains = []
    for client in clients:
        domains += client.get_domains()
        wait_rate_limit()

    return CommandResults(
        outputs_prefix='Proofpoint.Domains',
        readable_output=domains,
        outputs=domains
    )


def get_list_command(clients: list) -> CommandResults:
    dmarc_list = clients[0].get_dmarc_list()
    dmarc_list = demisto.context()["lists"]["test-list2"]
    return CommandResults(
        outputs_prefix='Proofpoint.List',
        readable_output=dmarc_list,
        outputs=dmarc_list
    )


def get_all_dmarc_command(clients: list, previous_days: str) -> CommandResults:
    data = []
    for client in clients:
        data += client.get_data_for_all(previous_days)
        wait_rate_limit()

    return CommandResults(
        outputs_prefix='Proofpoint.DMARC',
        readable_output=data,
        outputs=data
    )


''' MAIN FUNCTION '''


def main() -> None:
    """main function, parses params and runs command functions

    :return:
    :rtype:
    """

    # if your Client class inherits from BaseClient, system proxy is handled
    # out of the box by it, just pass ``proxy`` to the Client constructor
    base_url = demisto.params().get("url")
    previous_days = demisto.args().get("previous_days")
    if previous_days == None:
        previous_days = demisto.params().get("previous_days")

    # INTEGRATION DEVELOPER TIP
    # You can use functions such as ``demisto.debug()``, ``demisto.info()``,
    # etc. to print information in the XSOAR server log. You can set the log
    # level on the server configuration
    # See: https://xsoar.pan.dev/docs/integrations/code-conventions#logging
    try:
        api_data = demisto.params().get('api_data').splitlines()
        clients = []
        for api in api_data:
            split = api.split(",")
            api_string = base64.b64encode("{}:{}".format(split[1], split[2]).encode()).decode()
            clients.append(Client(base_url=base_url, api_string=api_string, instance_name=split[0]))

        if demisto.command() == 'test-module':
            # This is the call made when pressing the integration Test button.
            result = test_module(clients)
            return_results(result)

        elif demisto.command() == 'proofpoint-get-domains':
            return_results(get_domains_command(clients))

        elif demisto.command() == 'proofpoint-get-dmarc-all':
            return_results(get_all_dmarc_command(clients, previous_days))

        elif demisto.command() == 'proofpoint-get-list':
            return_results(get_list_command(clients))

    # Log exceptions and return errors
    except Exception as e:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute {demisto.command()} command.\nError:\n{str(e)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
