# -*- coding: utf-8 -*-
from CommonServerPython import *


def load_mock_response(file_name):
    """
    Load mock file that simulates an API response.

    Args:
        file_name (str): Name of the mock response JSON file to return.

    Returns:
        str: Mock file content.

    """
    with open('test_data/' + file_name, mode='r') as f:
        return json.loads(f.read())


def test_get_incidents(requests_mock, mocker):
    """
    Given:
        - An incident with non-ascii character in its documentation

    When:
        - Running get incidents command

    Then:
        - Ensure command run without failing on UnicodeError
        - Verify the non-ascii character appears in the human readable output as expected
    """
    mocker.patch.object(
        demisto,
        'params',
        return_value={
            'APIKey': 'API_KEY',
            'ServiceKey': 'SERVICE_KEY',
            'FetchInterval': 'FETCH_INTERVAL',
            'DefaultRequestor': 'DefaultRequestor'
        }
    )
    from PagerDuty import get_incidents_command
    requests_mock.get(
        'https://api.pagerduty.com/incidents?include%5B%5D=assignees&statuses%5B%5D=triggered&statuses%5B%5D'
        '=acknowledged&include%5B%5D=first_trigger_log_entries&include%5B%5D=assignments&time_zone=UTC',
        json={
            'incidents': [{
                'first_trigger_log_entry': {
                    'channel': {
                        'details': {
                            'Documentation': '•'
                        }
                    }
                }
            }]
        }
    )
    res = get_incidents_command()
    assert '| Documentation: • |' in res['HumanReadable']


def test_add_responders(requests_mock, mocker):
    """
    Given:
        - a responder request.

    When:
        - Running PagerDuty-add-responders command.

    Then:
        - Ensure command returns the correct output.
    """
    mocker.patch.object(
        demisto,
        'params',
        return_value={
            'APIKey': 'API_KEY',
            'ServiceKey': 'SERVICE_KEY',
            'FetchInterval': 'FETCH_INTERVAL',
            'DefaultRequestor': 'P09TT3C'
        }
    )
    mocker.patch.object(
        demisto,
        'args',
        return_value={
            "incident_id": "PXP12GZ",
            "message": "Please help with issue - join bridge at +1(234)-567-8910",
            "user_requests": "P09TT3C,PAIXXX"
        }
    )
    requests_mock.post(
        'https://api.pagerduty.com/incidents/PXP12GZ/responder_requests',
        json=load_mock_response('responder_requests.json').get('specific_users')
    )

    from PagerDuty import add_responders_to_incident
    res = add_responders_to_incident(**demisto.args())
    expected_users_requested = ','.join([x.get("ID") for x in res.outputs])
    assert demisto.args().get('incident_id') == res.outputs[0].get('IncidentID')
    assert demisto.args().get('message') == res.outputs[0].get('Message')
    assert demisto.params().get('DefaultRequestor') == res.outputs[1].get('RequesterID')
    assert demisto.args().get('user_requests') == expected_users_requested


def test_add_responders_default(requests_mock, mocker):
    """
    Given:
        - a responder request without specifying responders.

    When:
        - Running add_responders_to_incident function.

    Then:
        - Ensure the function returns the correct output.
    """
    mocker.patch.object(
        demisto,
        'params',
        return_value={
            'APIKey': 'API_KEY',
            'ServiceKey': 'SERVICE_KEY',
            'FetchInterval': 'FETCH_INTERVAL',
            'DefaultRequestor': 'P09TT3C'
        }
    )
    mocker.patch.object(
        demisto,
        'args',
        return_value={
            "incident_id": "PXP12GZ",
            "message": "Please help with issue - join bridge at +1(234)-567-8910"
        }
    )
    requests_mock.post(
        'https://api.pagerduty.com/incidents/PXP12GZ/responder_requests',
        json=load_mock_response('responder_requests.json').get('default_user')
    )

    from PagerDuty import add_responders_to_incident
    res = add_responders_to_incident(**demisto.args())
    expected_users_requested = ','.join([x.get("ID") for x in res.outputs])
    assert demisto.args().get('incident_id') == res.outputs[0].get('IncidentID')
    assert demisto.args().get('message') == res.outputs[0].get('Message')
    assert demisto.params().get('DefaultRequestor') == res.outputs[0].get('RequesterID')
    assert demisto.params().get('DefaultRequestor') == expected_users_requested


def test_play_response_play(requests_mock, mocker):
    """
    Given:
        - a responder request without specifying responders.

    When:
        - Running PagerDuty-run-response-play function.

    Then:
        - Ensure the function returns a valid status.
    """
    mocker.patch.object(
        demisto,
        'params',
        return_value={
            'APIKey': 'API_KEY',
            'ServiceKey': 'SERVICE_KEY',
            'FetchInterval': 'FETCH_INTERVAL',
            'DefaultRequestor': 'P09TT3C'
        }
    )
    mocker.patch.object(
        demisto,
        'args',
        return_value={
            "incident_id": "PXP12GZ",
            "from_email": "john.doe@example.com",
            "response_play_uuid": "response_play_id",
        }
    )
    requests_mock.post(
        'https://api.pagerduty.com/response_plays/response_play_id/run',
        json={"status": "ok"}
    )

    from PagerDuty import run_response_play
    res = run_response_play(**demisto.args())

    assert res.raw_response == {"status": "ok"}
