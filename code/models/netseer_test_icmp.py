from datetime import datetime
import socket
from pprint import pprint
import subprocess
from models.push_gw import PushGwModel


class TestIcmpModel():
    def __init__(self, test_info):
        self.test_name = test_info['test_name']
        self.agent=test_info['agent']
        self.agent_site=test_info['agent_site']
        self.target = test_info['target']
        self.target_site = test_info['target_site']
        self.interval = test_info['interval']
        self.test_type = test_info['test_type']

    def execute(self):
        print('{}, begin test: {}, target: {}, interval: {}s, type: {}, agent: {}' .format(
            datetime.now(),
            self.test_name,
            self.target,
            self.interval,
            self.test_type,
            self.agent,
            )
        )

        cmd = 'ping -c {0} -W {0} {1}'.format(self.interval, self.target)
        results = subprocess.getoutput(cmd).splitlines()

        if 'cannot resolve' not in results[-1]:
            packet_loss = int(float(results[-2].split()[6].replace('%','')))
            availability = 100 - packet_loss
            latency =  results[-1].split('=')[-1].split('/')
            latency_avg = int(latency[1].split('.')[0])
            latency_min = int(latency[0].split('.')[0])
            latency_max = int(latency[2].split('.')[0])

            final_metrics = {
                'metrics':  [
                                {
                                    'metric_name': 'availability_icmp',
                                    'description': '% of uptime based on multiple ping tests performed within specified interval',
                                    'value': availability
                                },
                                {
                                    'metric_name': 'packet_loss_icmp',
                                    'description': '% of downtime based on multiple ping tests performed within specified interval',
                                    'value': packet_loss
                                },
                                {
                                    'metric_name': 'latency_avg_icmp',
                                    'description': 'avg time it takes to rx a ping response based on multiple tests performed within specified interval',
                                    'value': latency_avg
                                },
                                {
                                    'metric_name': 'latency_min_icmp',
                                    'description': 'minimum time it takes to rx a ping response based on multiple tests performed within specified interval',
                                    'value': latency_min
                                },
                                {
                                    'metric_name': 'latency_max_icmp',
                                    'description': 'maximum time it takes to rx a ping response based on multiple tests performed within specified interval',
                                    'value': latency_max
                                }
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

        else:
            print('{}, fail test: {}, cannot resolve {}, agent: {}'.format(
                datetime.now(),
                self.target,
                self.agent
                )
            )
