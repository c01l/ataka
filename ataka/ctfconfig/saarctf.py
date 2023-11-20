import logging

from ataka.common.flag_status import FlagStatus

import json
import requests
import telnetlib
import socket

ATAKA_HOST = "10.2.0.25"

RUNLOCAL_TARGETS = [
    "10.32.1.2",
]

# Config for framework
ROUND_TIME = 120

# format: regex, group where group 0 means the whole regex
FLAG_REGEX = r"SAAR\{[A-Za-z0-9_-]{32}\}", 0

FLAG_BATCHSIZE = 500

FLAG_RATELIMIT = 0.5  # Wait in seconds between each call of submit_flags()

START_TIME = 1700312400 # Saturday, November 18, 2023 2:00:00 PM GMT+01:00
# IPs that are always excluded from attacks.
STATIC_EXCLUSIONS = {"10.32.91.2"}

SUBMIT_DOM = '10.32.250.2'
SUBMIT_PORT = 31337
FLAGID_URL = 'https://scoreboard.ctf.saarland/attack.json'
EDITION = 2023


def get_targets():
    try:
        dt = requests.get(FLAGID_URL).json()
        #dt = json.loads('{"teams":[{"id":1,"name":"NOP","ip":"10.32.1.2"},{"id":2,"name":"saarsec","ip":"10.32.2.2"}],"flag_ids":{"service_1":{"10.32.1.2":{"15":["username1","username1.2"],"16":["username2","username2.2"]},"10.32.2.2":{"15":["username3","username3.2"],"16":["username4","username4.2"]}}}}')

        flag_ids = dt['flag_ids']
        teams = dt['teams']
        targets = {
            service: [
                {
                    'ip': ip,
                    'extra': json.dumps(ip_info),
                }
                for ip, ip_info in service_info.items()
            ]
            for service, service_info in flag_ids.items()
        }

        return targets
    except Exception as e:
        print(f"Error while getting targets: {e}")
        return {service: [] for service in get_services()}


def submit_flags(flags):
    results = []
    try:
        conn = telnetlib.Telnet(SUBMIT_DOM, SUBMIT_PORT, 2)

        for flag in flags:
            conn.write((flag + '\n').encode())
            resp = conn.read_until(b"\n").decode()
            if resp == '[OK]\n':
                status = FlagStatus.OK
            elif 'format' in resp:
                status = FlagStatus.INVALID
            elif 'Invalid flag' in resp:
                status = FlagStatus.INVALID
            elif 'Expired' in resp:
                status = FlagStatus.INACTIVE
            elif 'Already submitted' in resp:
                status = FlagStatus.DUPLICATE
            elif 'NOP team' in resp:
                status = FlagStatus.NOP
            elif 'own flag' in resp:
                status = FlagStatus.OWNFLAG
            else:
                status = FlagStatus.ERROR
            results.append(status)

        conn.get_socket().shutdown(socket.SHUT_WR)
        conn.read_all()
        conn.close()
    except Exception as e:
        print(f"Error while submitting flags: {e}")
        results += [FlagStatus.ERROR]*(len(flags)-len(results))

    return results


logger = logging.getLogger()

if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(get_targets())
    pp.pprint(submit_flags([
        'test_flag_1',
        'test_flag_2',
    ]))
