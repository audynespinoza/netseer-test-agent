import time
from datetime import datetime
import socket
from pprint import pprint
import subprocess
from models.push_gw import PushGwModel


class TestHttpModel():
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

        conn_success_all = []
        time_dns_all  = []
        time_tcp_conn_all  = []
        time_server_resp_all  = []

        for i in range(int(test_exec_count)):
            start = time.time()
            cmd = 'curl -w "@curl-format" --connect-timeout {} -o /dev/null -s http://{}:{}'.format(
                timeout, self.target, self.port)
            response = subprocess.getoutput(cmd).splitlines()
            results = {i.split(':')[0]:float(i.split(':')[1]) for i in response}

            resp_code = int(results['resp_code'])
            conn_success = 1 if resp_code > 0 and resp_code < 399 else 0
            time_dns = int(results['time_dns'] * 1000)
            time_tcp_conn = int((results['time_tcp_conn'] - results['time_dns']) * 1000)
            time_server_resp = int((results['time_resp_code_recv'] - results['time_req_sent']) * 1000)
            end = time.time()
            diff = end - start

            if conn_success == 1:
                print('{}, test: {}, http conn {} of {} successful; time to connect: {:.2f}s, agent: {}' .format(
                    datetime.now(),
                    self.test_name,
                    i + 1,
                    int(test_exec_count),
                    diff,
                    self.agent
                    )
                )
            else:
                print('{}, test: {}, http conn {} of {} unsuccessful; unsuccessful; timeout: {:.2f}s, agent: {}'.format(
                    datetime.now(),
                    self.test_name,
                    i + 1,
                    int(test_exec_count),
                    timeout,
                    self.agent
                    )
                )

            if diff < 5:
                time.sleep(5 - diff)

            conn_success_all.append(conn_success)
            time_dns_all.append(time_dns)
            time_tcp_conn_all.append(time_tcp_conn)
            time_server_resp_all.append(time_server_resp)

        final_metrics = {
           'metrics': [
                            {
                                'metric_name': 'availability_http',
                                'description': '% of uptime based on multiple http tests performed within specified interval',
                                'value': int(sum(conn_success_all)/len(conn_success_all) * 100)
                            },
                            {
                                'metric_name': 'avg_time_dns_http',
                                'description': 'avg time it takes to rx a dns query response',
                                'value': int(sum(time_dns_all)/len(time_dns_all))
                            },
                            {
                                'metric_name': 'avg_time_tcp_conn_http',
                                'description': 'avg time it takes to establish a tcp connection based on multiple tests performed within specified interval',
                                'value': int(sum(time_tcp_conn_all)/len(time_tcp_conn_all))
                            },
                            {
                                'metric_name': 'avg_time_server_resp_http',
                                'description': 'avg time it takes to rx a http response code based on multiple tests performed within specified interval',
                                'value': int(sum(time_server_resp_all)/len(time_server_resp_all))
                            },
                            {
                                'metric_name': 'min_time_dns_http',
                                'description': 'min time it takes to rx a dns query response',
                                'value': min(time_dns_all)
                            },
                            {
                                'metric_name': 'min_time_tcp_conn_http',
                                'description': 'min time it takes to establish a tcp connection based on multiple tests performed within specified interval',
                                'value': min(time_tcp_conn_all)
                            },
                            {
                                'metric_name': 'min_time_server_resp_http',
                                'description': 'min time it takes to rx a http response code based on multiple tests performed within specified interval',
                                'value': min(time_server_resp_all)
                            },
                            {
                                'metric_name': 'max_time_dns_http',
                                'description': 'max time it takes to rx a dns query response',
                                'value': max(time_dns_all)
                            },
                            {
                                'metric_name': 'max_time_tcp_conn_http',
                                'description': 'max time it takes to establish a tcp connection based on multiple tests performed within specified interval',
                                'value': max(time_tcp_conn_all)
                            },
                            {
                                'metric_name': 'max_time_server_resp_http',
                                'description': 'max time it takes to rx a http response code based on multiple tests performed within specified interval',
                                'value': max(time_server_resp_all)
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
