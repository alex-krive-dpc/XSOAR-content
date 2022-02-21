from typing import Dict, Any
import traceback
from io import StringIO
import csv, json

''' STANDALONE FUNCTION '''

def generate_csv_data(data: list, domainList: list):
    out = []
    out.append([
        "Hostname",
        "Instance Org",
        "InList",
        "SenderName",
        "SenderVerified",
        "SenderVerifiedStatus",
        "Policy",
        "BlockedMailCount",
        "DKIM.alignCount",
        "DKIM.failCount",
        "DKIM.misalignCount",
        "DKIM.neutralCount",
        "DKIM.passAlignCount",
        "DKIM.passCount",
        "DKIM.totalCount",
        "DMARC.doublePassCount",
        "DMARC.failCount",
        "DMARC.passCount",
        "SPF.alignCount",
        "SPF.failCount",
        "SPF.misalignCount",
        "SPF.neutralCount",
        "SPF.passAlignCount",
        "SPF.passCount",
        "SPF.totalCount",
        "TotalMailCount"
    ])  # header row

    newdata = data
    goodDomainList = []
    for server in data:
        goodDomainList.append(server["Hostname"])

    for domain in domainList:
        if not domain in goodDomainList:
            newdata.append({
                "Hostname": domain,
                "InList": False,
                "InstanceName": "N/A"
            })

    for server in newdata:
        row = [
            server["Hostname"],
            server["InstanceName"],
            server["Hostname"] in domainList
        ]

        if "SenderName" in server.keys():
            row.append(server["SenderName"])
            row.append(server["SenderVerified"])
            row.append(server["SenderVerifiedStatus"])
        else:
            for i in range(3):
                row.append("")

        if "Policy" in server.keys():
            row.append(server["Policy"])
        else:
            row.append("")

        if "BlockedMailCount" in server.keys():
            row.append(server["BlockedMailCount"])
        else:
            row.append("")

        if "DKIM" in server.keys():
            row.append(server["DKIM"]["alignCount"] or "")
            row.append(server["DKIM"]["failCount"] or "")
            row.append(server["DKIM"]["misalignCount"] or "")
            row.append(server["DKIM"]["neutralCount"] or "")
            row.append(server["DKIM"]["passAlignCount"] or "")
            row.append(server["DKIM"]["passCount"] or "")
            row.append(server["DKIM"]["totalCount"] or "")
        else:
            for i in range(7):
                row.append("")

        if "DMARC" in server.keys():
            row.append(server["DMARC"]["doublePassCount"] or "")
            row.append(server["DMARC"]["failCount"] or "")
            row.append(server["DMARC"]["passCount"] or "")
        else:
            for i in range(3):
                row.append("")

        if "SPF" in server.keys():
            row.append(server["SPF"]["alignCount"] or "")
            row.append(server["SPF"]["failCount"] or "")
            row.append(server["SPF"]["misalignCount"] or "")
            row.append(server["SPF"]["neutralCount"] or "")
            row.append(server["SPF"]["passAlignCount"] or "")
            row.append(server["SPF"]["passCount"] or "")
            row.append(server["SPF"]["totalCount"] or "")
        else:
            for i in range(7):
                row.append("")

        if "TotalMailCount" in server.keys():
            row.append(server["TotalMailCount"])
        else:
            row.append("")

        out.append(row)

    return out

''' COMMAND FUNCTION '''

''' MAIN FUNCTION '''


def main():
    try:
        data = demisto.context()["Proofpoint"]["DMARC"]
        domain_list = json.loads(demisto.executeCommand("getList", {"listName": "dmarc-domains"})[0]["Contents"])
        
        csv_data = generate_csv_data(data, domain_list)
        f = StringIO()
        csv.writer(f).writerows(csv_data)

        return_results(
            fileResult(
                filename=f'report.csv',
                data=f.getvalue(),
                file_type=entryTypes['entryInfoFile']
            )
        )
    except Exception as ex:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute BaseScript. Error: {str(ex)}')


''' ENTRY POINT '''


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()

