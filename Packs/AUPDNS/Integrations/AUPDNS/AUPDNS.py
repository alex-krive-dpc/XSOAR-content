import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
import dns.resolver
from typing import Any, Dict, Tuple, List, Optional, Union, cast

# Disable insecure warnings

''' HELPER FUNCTIONS '''

''' COMMAND FUNCTIONS '''


def test_module(resolver) -> str:
    try:
        resolver.query("google.com")
    except Exception as e:
        return "Invalid DNS Servers"
    return 'ok'


def domain_reputation_command(resolver, args: Dict[str, Any]) -> List[CommandResults]:
    domains = argToList(args.get('domain'))
    if len(domains) == 0:
        raise ValueError('domain(s) not specified')

    # Initialize an empty list of CommandResults to return,
    # each CommandResult will contain context standard for Domain
    command_results: List[CommandResults] = []

    for domain in domains:
        score = Common.DBotScore.GOOD
        result = "Good"
        try:
            d = list(resolver.resolve(domain, "CNAME"))[0]
            if str(d.target) == "iss.aupdns.com.au.":
                score = Common.DBotScore.BAD
                result = "Bad"
        except:
            pass

        dbot_score = Common.DBotScore(
            indicator=domain,
            integration_name='AUPDNS',
            indicator_type=DBotScoreType.DOMAIN,
            score=score,
            malicious_description=f'AUPDNS DNS Server returned {score}'
        )

        # Create the Domain Standard Context structure using Common.Domain and
        # add dbot_score to it.
        domain_standard_context = Common.Domain(
            domain=domain,
            dbot_score=dbot_score
        )

        command_results.append(CommandResults(
            outputs_prefix='AUPDNS.Domain',
            outputs_key_field='domain',
            outputs={"Result": result, "Name": domain},
            indicator=domain_standard_context
        ))
    return command_results


''' MAIN FUNCTION '''


def main() -> None:
    """main function, parses params and runs command functions

    :return:
    :rtype:
    """
    nameservers = []

    ns1 = demisto.params().get('nameserver1')
    if "nameserver2" in demisto.params().keys():
        nameservers.append(demisto.params().get("nameserver2"))

    resolver = dns.resolver.Resolver()
    resolver.nameservers = nameservers

    try:
        if demisto.command() == 'test-module':
            # This is the call made when pressing the integration Test button.
            result = test_module(resolver)
            return_results(result)
        elif demisto.command() == 'domain':
            return_results(domain_reputation_command(resolver, demisto.args()))

    # Log exceptions and return errors
    except Exception as e:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute {demisto.command()} command.\nError:\n{str(e)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
