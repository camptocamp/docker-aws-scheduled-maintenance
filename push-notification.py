#!/usr/bin/env python3
from prometheus_client import CollectorRegistry, Counter, push_to_gateway
import boto3
import os
import sys

if len(sys.argv) == 2:
    session = boto3.session.Session(
            profile_name = sys.argv[1],
            region_name  = 'eu-west-1',
            )
else:
    session = boto3.session.Session(
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name=os.environ['AWS_REGION_NAME'],
            )
ec2_client = session.client('ec2')
registry = CollectorRegistry()

scheduled_downtime = Counter('aws_scheduled_downtime', 'AWS scheduled downtimes', registry=registry)
impaired_systems   = Counter('aws_impaired_systems', 'AWS running systems with bad state', registry=registry)
impaired_instances = Counter('aws_impaired_instances', 'AWS running instances with bad state', registry=registry)

for status in ec2_client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']:
    if 'Events' in status:
        scheduled_downtime.inc()
    if status['InstanceState']['Name'] == 'running':
        if status['SystemStatus']['Status'] == 'impaired':
            impaired_systems.inc()
        if status['InstanceStatus']['Status'] == 'impaired':
            impaired_instances.inc()

push_to_gateway('pushgateway.metrics:9091', job='AWS_States', registry=registry)

sys.exit(0)
