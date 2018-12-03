#!/usr/bin/python

import boto3
import datetime
import locale
import os
from dateutil.relativedelta import *
from datetime import date, timedelta
import json
import time

# This is AWS Devbox Environment account ID
AccountId='xxxxxxxx'


def lambda_handler(event, context):

    cw = boto3.client('cloudwatch')

    ec = boto3.client('elasticache')
    cc = ec.describe_cache_clusters()

    for cluster in cc.get('CacheClusters'):
     print(cluster.get('CacheClusterId'))
     response = cw.get_metric_statistics(
        Period=1209600,
        StartTime=datetime.datetime.utcnow() - datetime.timedelta(seconds=600),
        EndTime=datetime.datetime.utcnow(),
        MetricName='CurrConnections',
        Namespace='AWS/ElastiCache',
        Statistics=['Average'],
        Dimensions=[{'Name':'CacheClusterId', 'Value':cluster.get('CacheClusterId')}]
        )
     print response["Datapoints"][0]["Average"]
    return 'Hello from Lambda'

if __name__ == '__main__':
    lambda_handler('event', 'handler')
