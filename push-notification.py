#!/usr/bin/env python3
from prometheus_client import CollectorRegistry, Counter, push_to_gateway
import boto3
import os
import sys
import urllib.error

if len(sys.argv) == 2:
    session = boto3.session.Session(
            profile_name = sys.argv[1],
            region_name  = 'eu-west-1',
            )
    print('[I] Using profile %s'%sys.argv[1])
else:
    session = boto3.session.Session(
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name=os.environ['AWS_REGION_NAME'],
            )
    print('[I] Using AWS key %s'%os.environ['AWS_ACCESS_KEY_ID'])

ec2_client = session.client('ec2')
registry = CollectorRegistry()

scheduled_downtime = Counter('aws_scheduled_downtime', 'AWS scheduled downtimes', registry=registry)
scheduled_retire   = Counter('aws_scheduled_retire', 'AWS scheduled retirements', registry=registry)
impaired_systems   = Counter('aws_impaired_systems', 'AWS running systems with bad state', registry=registry)
impaired_instances = Counter('aws_impaired_instances', 'AWS running instances with bad state', registry=registry)

events = ec2_client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']
print('[I] %i instances'%len(events))
for status in events:
    if 'Events' in status:
        print('[I] Found: scheduled maintenance')
        if any('stop' in s['Code'] for s in status['Events']) or any('retire' in s['Code'] for s in status['Events']):
            print('[W]  Is a retirement')
            scheduled_retire.inc()
        else:
            print('[I]  Is a reboot')
            scheduled_downtime.inc()
    if status['InstanceState']['Name'] == 'running':
        if status['SystemStatus']['Status'] == 'impaired':
            impaired_systems.inc()
            print('[I] Found: impaired system')
        if status['InstanceStatus']['Status'] == 'impaired':
            impaired_instances.inc()
            print('[I] Found: impaired instance')

try:
    print('[I] Pushing to prometheus')
    push_to_gateway('pushgateway.metrics:9091', job='AWS_States', registry=registry)
except urllib.error.URLError:
    print('[C] Unable to push to Prometheus')

sys.exit(0)
