#!/usr/bin/python

import sys
import os
import requests
import threading
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from models.netseer_test_icmp import TestIcmpModel
from models.netseer_test_tcp import TestTcpModel
from models.netseer_test_http import TestHttpModel
from models.netseer_test_dns import TestDnsModel

# -----------
# basic setup
# -----------
if os.getenv('DOCKER_CONTAINER') == '1':
    token = os.getenv('TOKEN')
    if os.getenv('AGENT_ENV') == 'dev':
        api_host = os.getenv('API_URL_HOST')
        api_port = '8080'
        if api_host is None:
            print('you need to specify API_URL_HOST, such as http://localhost')
    else:
        api_host = 'http://netseerapi.tools.ash.netops.tmcs'
        api_port = '80'
else:
# ---------------------------------------------------------------------------
# example: python netseer_test_agent.py  -t <agent-token> -h http://127.0.0.1
# ---------------------------------------------------------------------------
    token = sys.argv[2]
    print(token)
    api_host = sys.argv[4]

api_endpoint = 'graphql/'
url = '{}:{}/{}'.format(api_host, api_port, api_endpoint)
expected_retries = 3


# -------------------------------------
# get agent name ie. agent1.end2end.phx
# -------------------------------------
def get_agent_name(token):
    client = Client(
        transport=RequestsHTTPTransport(url=url),
        retries=expected_retries
        )
    query = gql('''
    mutation {
      verifyToken (input: {token: "''' + token + '''"}) {
        payload
      }
    }
    ''')
    return client.execute(query)


# ---------------------
# get agent test config
# ---------------------
def get_agent_test_cfg(agent_name, token):
    client = Client(
        transport=RequestsHTTPTransport(
            url=url,
            headers={'Authorization': 'JWT {}'.format(token)},
            ),
        retries=expected_retries
        )
    query = gql('''
    {
      agents(agentName:"''' + agent_name + '''") {
        edges {
          node {
            id
            agentName
            agentType
            dateModified
            status
            enabled
            agentSite
            agentLabels {
              edges {
                node {
                  id
                  color
                  dateModified
                  description
                  agentLabelName
                  tests {
                    edges {
                      node {
                        id
                        testName
                        testType
                        target
                        targetSite
                        port
                        interval
                        testLabels {
                          edges {
                            node {
                              id
                              description
                              dateModified
                              color
                              description
                              testLabelName
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    ''')
    return client.execute(query)

# -----------------------------------
# executes tests in a mthread fashion
# -----------------------------------
def test_it_mthread(agent_info, agent_labels):
    for label in agent_labels:
        label_name = label['node']['agentLabelName']
        tests = label['node']['tests']['edges']
        for test in tests:
            test_info = dict(
                test_name=test['node']['testName'],
                agent=agent_info['agentName'],
                agent_site=agent_info['agentSite'],
                target=test['node']['target'],
                target_site=test['node']['targetSite'],
                interval=test['node']['interval'],
                port=test['node']['port'],
                test_type=test['node']['testType'],
            )
            if test_info['test_type'] == 'icmp':
                t =  TestIcmpModel(test_info)
            if test_info['test_type'] == 'tcp':
                t =  TestTcpModel(test_info)
            if test_info['test_type'] == 'http':
                t =  TestHttpModel(test_info)
            if test_info['test_type'] == 'dns':
                t =  TestDnsModel(test_info)
            if t:
                my_thread = threading.Thread(target=t.execute)
                my_thread.start()
    main_thread = threading.currentThread()
    for some_thread in threading.enumerate():
        if some_thread != main_thread:
            some_thread.join()


if __name__ == '__main__':

    req_name = get_agent_name(token)
    agent_name = req_name['verifyToken']['payload'].get('username')

    while agent_name is not None:
        print('{}, request agent {} test info from {}'.format(
            datetime.now(),
            agent_name,
            url)
        )
        req_cfg = get_agent_test_cfg(agent_name, token)
        print("{}, received agent {} test info from {}".format(
            datetime.now(),
            agent_name,
            url)
        )
        try:
            agent_info = req_cfg['agents']['edges'][0]['node']
            agent_extant = 1 if agent_info.get('agentName') else 0
            enabled = agent_info.get('enabled')
        except:
            agent_extant = 0
            enabled = 0
        if enabled and agent_extant:
            print('{}, agent: {}, status: {}, enabled: {}, agent_site: {}'.format(
                    datetime.now(),
                    agent_info['agentName'],
                    agent_info['status'],
                    agent_info['enabled'],
                    agent_info['agentSite'],
                ))

            agent_labels = [i for i in agent_info['agentLabels']['edges']]

            test_it_mthread(agent_info, agent_labels)
        else:
            print('{}, {} may not be configured in Netseer'.format(
                datetime.now(),
                agent_name
                )
            )
            break
