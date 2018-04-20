import time
from datetime import datetime
import socket
from pprint import pprint
import subprocess
from models.push_gw import PushGwModel


class TestDnsModel():
    def __init__(self, test_info):
        self.test_name = test_info['test_name']
        self.agent=test_info['agent']
        self.agent_site=test_info['agent_site']
        self.target = test_info['target']
        self.target_site = test_info['target_site']
        self.interval = test_info['interval']
        self.test_type = test_info['test_type']

    def execute(self):
        print('{}, begin test: {}, target: {}, interval: {}s, type: {}, agent: {}'.format(
            datetime.now(),
            self.test_name,
            self.target,
            self.interval,
            self.test_type,
            self.agent,
            )
        )

        timeout = 5
        test_exec_count = self.interval / timeout

        conn_success_all = []
        time_dns_all  = []

        for i in range(int(test_exec_count)):
            start = time.time()
            cmd = 'dig {} +noall +comments +stats +answer +tries=1 +time=5'.format(self.target)
            results = subprocess.getoutput(cmd).splitlines()

            if len(results) == 14 and 'ANSWER: 1' in results[-9]:
                time_dns = int(results[-4].split()[-2])
                conn_success = 1
            else:
                conn_success = 0
                time_dns = 5000

            end = time.time()
            diff = end - start

            if conn_success == 1:
                print('{}, test: {}, dns query {} of {} successful; time to connect: {:.2f}ms, agent: {}'.format(
                    datetime.now(), self.test_name, i + 1, int(test_exec_count), time_dns, self.agent)
                )
            else:
                print('{}, test: {}, dns query {} of {} unsuccessful; timeout: {:.2f}s, agent: {}'.format(
                    datetime.now(), self.test_name, i + 1, int(test_exec_count), timeout, self.agent)
                )

            if diff < 5:
                time.sleep(5 - diff)

            conn_success_all.append(conn_success)
            time_dns_all.append(time_dns)

        availability = int(sum(conn_success_all)/len(conn_success_all) * 100)

        avg_time_dns = int(sum(time_dns_all)/len(time_dns_all))
        min_time_dns = min(time_dns_all)
        max_time_dns = max(time_dns_all)
        final_metrics = {
           'metrics': [
                            {
                                'metric_name': 'availability',
                                'description': '% of uptime based on multiple tcp tests performed within specified interval',
                                'value': int(sum(conn_success_all)/len(conn_success_all) * 100)
                            },
                            {
                                'metric_name': 'avg_time_dns',
                                'description': 'avg time it takes to rx a dns query response',
                                'value': int(sum(time_dns_all)/len(time_dns_all))
                            },
                            {
                                'metric_name': 'min_time_dns',
                                'description': 'min time it takes to rx a dns query response',
                                'value': min(time_dns_all)
                            },
                            {
                                'metric_name': 'max_time_dns',
                                'description': 'max time it takes to rx a dns query response',
                                'value': max(time_dns_all)
                            },
                        ],
            'agent': self.agent,
            'agent_site': self.agent_site,
            'target': self.target,
            'target_site': self.target_site,
            'test_name': self.test_name,
            'test_type': self.test_type,
        }

        print('{}, completed test: {}, target: {}, interval: {}s, type: {}, agent: {}'.format(
            datetime.now(),
            self.test_name,
            self.target,
            self.interval,
            self.test_type,
            self.agent,
            )
        )
        push = PushGwModel(final_metrics)
        push.send_to_push_gw()
