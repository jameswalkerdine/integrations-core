# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

from copy import deepcopy

from datadog_checks.errors import CheckException
from datadog_checks.checks.prometheus import PrometheusCheck


EVENT_TYPE = SOURCE_TYPE_NAME = 'kubedns'

class KubeDNSCheck(PrometheusCheck):
    """
    Collect kube-dns metrics from Prometheus
    """
    def __init__(self, name, init_config, agentConfig, instances=None):
        generic_instances = create_generic_instances(self, instances)
        super(KubeDNSCheck, self).__init__(name, init_config, agentConfig, instances=generic_instances)

    def check(self, instance):
        endpoint = instance.get('prometheus_endpoint')
        if endpoint is None:
            raise CheckException("Unable to find prometheus_endpoint in config file.")

        self.process(instance, config)

    def _create_kube_dns_instance(self, instance):
        """
        """

        kube_dns_instance = deepcopy(instance)
        kube_dns_instance.update({
            'namespace': 'kubedns',
            'metrics': [{
                # metrics have been renamed to kubedns in kubernetes 1.6.0
                'kubedns_kubedns_dns_response_size_bytes': 'response_size.bytes',
                'kubedns_kubedns_dns_request_duration_seconds': 'request_duration.seconds',
                # metrics names for kubernetes < 1.6.0
                'skydns_skydns_dns_response_size_bytes': 'response_size.bytes',
                'skydns_skydns_dns_request_duration_seconds': 'request_duration.seconds',
                # Note: the count metrics were moved to specific functions below to be submitted as both gauges and monotonic_counts
            }]
        })

        return kube_dns_instance

    def submit_as_gauge_and_monotonic_count(self, metric_suffix, message, **kwargs):
        """
        submit a kube_dns metric both as a gauge (for compatibility) and as a monotonic_count
        """
        metric_name = self.NAMESPACE + metric_suffix
        for metric in message.metric:
            _tags = []
            for label in metric.label:
                _tags.append('{}:{}'.format(label.name, label.value))
            # submit raw metric
            self.gauge(metric_name, metric.counter.value, _tags)
            # submit rate metric
            self.monotonic_count(metric_name + '.count', metric.counter.value, _tags)

    # metrics names for kubernetes >= 1.6.0
    def kubedns_kubedns_dns_request_count_total(self, message, **kwargs):
        self.submit_as_gauge_and_monotonic_count('.request_count', message, **kwargs)

    def kubedns_kubedns_dns_error_count_total(self, message, **kwargs):
        self.submit_as_gauge_and_monotonic_count('.error_count', message, **kwargs)

    def kubedns_kubedns_dns_cachemiss_count_total(self, message, **kwargs):
        self.submit_as_gauge_and_monotonic_count('.cachemiss_count', message, **kwargs)

    # metrics names for kubernetes < 1.6.0
    def skydns_skydns_dns_request_count_total(self, message, **kwargs):
        self.kubedns_kubedns_dns_request_count_total(message, **kwargs)

    def skydns_skydns_dns_error_count_total(self, message, **kwargs):
        self.kubedns_kubedns_dns_error_count_total(message, **kwargs)

    def skydns_skydns_dns_cachemiss_count_total(self, message, **kwargs):
        self.kubedns_kubedns_dns_cachemiss_count_total(message, **kwargs)
