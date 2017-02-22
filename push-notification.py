#!/usr/bin/env python3
from prometheus_client import CollectorRegistry, Counter, push_to_gateway
import boto3
import botocore.exceptions
import os
import sys
import urllib.error

registry = CollectorRegistry()

if len(sys.argv) == 2:
    print('[I] Using profile %s'%sys.argv[1])
    session = boto3.session.Session(
            profile_name = sys.argv[1],
            region_name  = 'eu-west-1',
            )
else:
    print('[I] Using either environment var or instance profile')
    session = boto3.session.Session()


if not session.region_name:
    print('[C] Critical error in script: no region_name set')
    error = Counter('aws_event_checker_fails', 'Errors with script', registry=registry)
    error.inc()
    try:
        print('[I] Pushing to prometheus')
        push_to_gateway('pushgateway.metrics:9091', job='AWS_States', registry=registry)
    except urllib.error.URLError:
        print('[C] Unable to push to Prometheus')
    sys.exit(1)


ec2_client = session.client('ec2')

ec2_events = Counter('aws_ec2_events', 'Events on AWS EC2 instances', ['instance_id', 'event_code'], registry=registry)

events = ec2_client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']
print('[I] %i instances'%len(events))
for status in events:
    if 'Events' in status:
        print('[I] Found: scheduled maintenance')
        if any('stop' in s['Code'] for s in status['Events']) or any('retire' in s['Code'] for s in status['Events']):
            print('[W]  Is a retirement (%s)'%status['InstanceId'])
            ec2_events.labels(status['InstanceId'], 'termination').inc()
        elif any('reboot' in s['Code'] for s in status['Events']):
            print('[I]  Is a reboot (%s)'%status['InstanceId'])
            ec2_events.labels(status['InstanceId'], 'reboot').inc()
        else:
            print(status['Events'])
    if status['InstanceState']['Name'] == 'running':
        if status['SystemStatus']['Status'] == 'impaired':
            ec2_events.labels(status['InstanceId'], 'system_impaired').inc()
            print('[I] Found: impaired system')
        if status['InstanceStatus']['Status'] == 'impaired':
            ec2_events.labels(status['InstanceId'], 'instance_impaired').inc()
            print('[I] Found: impaired instance')

try:
    print('[I] Pushing to prometheus')
    push_to_gateway('pushgateway.metrics:9091', job='AWS_States', registry=registry)
except urllib.error.URLError:
    print('[C] Unable to push to Prometheus')


sys.exit(0)
