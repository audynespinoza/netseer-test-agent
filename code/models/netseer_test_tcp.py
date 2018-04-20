import time
from datetime import datetime
import socket
from pprint import pprint
import subprocess
from models.push_gw import PushGwModel


class TestTcpModel():
    def __init__(self, test_info):
        self.test_name = test_info['test_name']
        self.agent=test_info['agent']
        self.agent_site=test_info['agent_site']
        self.target = test_info['target']
        self.target_site = test_info['target_site']
        self.port = test_info['port']
        self.interval = test_info['interval']
        self.test_type = test_info['test_type']

    def execute(self):
        print('{}, begin test: {}, target: {}, port: {}, interval: {}s, type: {}, agent: {}'.format(
                datetime.now(),
                self.test_name,
                self.target,
                self.port,
                self.interval,
                self.test_type,
                self.agent,
            )
        )

        timeout = 5
        test_exec_count = self.interval / timeout

        socket.setdefaulttimeout(timeout)
        conn_success = []
        conn_setup_time = []

        for i in range(int(test_exec_count)):
            try:
                s  = socket.socket()
                start = time.time()
                s.connect((self.target, self.port))
                end = time.time()
                diff = end - start
                conn_success.append(1.0)
                conn_setup_time.append(diff)
                print('{}, test: {}, tcp conn  {} of {} successful; time to connect: {}ms, agent: {}'.format(
                    datetime.now(),
                    self.test_name,
                    i + 1,
                    int(test_exec_count),
                    int(diff * 1000),
                    self.agent
                    )
                )
                if diff < 5:
                    time.sleep(5 - diff)
            except:
                conn_success.append(0.0)
                conn_setup_time.append(5.0)
                print('{}, test: {}, tcp conn {} of {} unsuccessful; timeout: 5sec, agent: {}'.format(
                    datetime.now(),
                    self.test_name,
                    i + 1,
                    int(test_exec_count),
                    self.agent
                    )
                )

        final_metrics = {
           'metrics': [
                            {
                                'metric_name': 'availability_tcp',
                                'description': '% of uptime based on multiple tcp tests performed within specified interval',
                                'value': int(sum(conn_success)/len(conn_success) * 100)
                            },
                            {
                                'metric_name': 'avg_conn_setup_time_tcp',
                                'description': 'avg time it takes to establish a tcp connection based on multiple tests performed within specified interval',
                                'value': int(sum(conn_setup_time)/len(conn_setup_time) * 1000)
                            },
                            {
                                'metric_name': 'min_conn_setup_time_tcp',
                                'description': 'minimum time it takes to establish a tcp connection based on multiple tests performed within specified interval',
                                'value': int(min(conn_setup_time) * 1000)
                            },
                            {
                                'metric_name': 'max_conn_setup_time_tcp',
                                'description': 'maximum time it takes to establish a tcp connection based on multiple tests performed within specified interval',
                                'value': int(max(conn_setup_time) * 1000)
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
