from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway


class PushGwModel():
    def __init__(self, final_metrics):
        self.final_metrics = final_metrics
        self.push_gateway_hostname = 'http://metrics.tools.ash.netops.tmcs'

    def send_to_push_gw(self):
        registry = CollectorRegistry()
        for metric in self.final_metrics['metrics']:
            try:
                send_metric_to_prom_pg = Gauge(
                    'netseer_{}'.format(metric['metric_name']),
                    metric['description'],
                    ['agent', 'agent_site', 'target', 'target_site', 'test_name', 'test_type'],
                    registry=registry
                )
            except ValueError:
                pass

            send_metric_to_prom_pg.labels(
                agent=self.final_metrics['agent'],
                agent_site=self.final_metrics['agent_site'],
                target=self.final_metrics['target'],
                target_site=self.final_metrics['target_site'],
                test_name=self.final_metrics['test_name'],
                test_type=self.final_metrics['test_type']
            ).set(metric['value'])

            pushadd_to_gateway(
                '{}'.format(self.push_gateway_hostname),
                job='{}.{}'.format(
                    self.final_metrics['agent'],
                    self.final_metrics['test_name']),
                registry=registry
            )

            print('{}, test: {}, pushed {} to push gateway {}, agent: {}'.format(
                datetime.now(),
                self.final_metrics['test_name'],
                metric['metric_name'],
                metric['value'],
                self.final_metrics['agent'],
                self.push_gateway_hostname
                )
            )
