#!/usr/bin/python

"""
    About Lambda Function:
    It is designed to track/identify EBS Orphaned volumes list and notifying alerts if EBS Orphaned volumes finds.
    It will get executed on every 3-day.And sending notification to "Team DL group" if Any EBS volumes available.

    AWS Cloudwatch Event(triggers) ---> Lambda Function(executes)---> IAM Role Policy(required permissions to exexute functions) ---> SES (sending email to teams)

"""

import boto3
import logging
from datetime import *
import pdb

ses = boto3.client('ses')

email_from = 'example@gmail.com'
#email_to = 'xxxxx@gmail.com'
#email_cc = ['xxxxxx@gmail.com']
#email_cc = ['example@gmail.com', 'xxxxx@gmail.com', 'xxxxx@gmail.com', 'xxxxx@gmail.com']
email_bcc = ['example@gmail.com','allexample@gmail.com']

emaiL_subject = 'AWS Devbox:EBS Orphaned/Unattached Volumes List'
#report = "The Following Devbox-EBS Volumes were found as Orphaned/Unattached,Will be deleted within 10days: \n"
report = "The Following Devbox-EBS Volumes were found as Orphaned/Unattached, in 7 days: \n"\
        "Note: If the volume needs to reuse before clean-up then please feel free to reach out to 'example@gmail.com' within the period of time." + "\n"


# setup simple logging for INFO
logger = logging.getLogger()
logger.setLevel(logging.WARNING)

# Get a boto session ready
session = boto3.session.Session(region_name="us-west-2")
ec2 = session.client('ec2')


def lambda_handler(event, context):

    # Report header.
    volume_count = 0
    no_iops = False

    # Start a pagination object for the describe_volumes
    paginator = ec2.get_paginator('describe_volumes')

    # Create filter for only available therefore deemed 'orphaned' volumes.
    filters = [
        {
            'Name': 'status',
            'Values': ['available']
        },
    ]
    operation_parameters = {
        'Filters': filters,
    }

    # Unpack operation parameters with the filters
    page_iterator = paginator.paginate(**operation_parameters)

    global report

    # Loop each page of results
    for page in page_iterator:
        # Loop each volume in each page.
        for volume in page['Volumes']:
            if volume['State'] == 'available':
                # Register with the counter
                volume_count = volume_count + 1
                # Report addition
                try:
                    volume['Iops']
                except KeyError:
                    no_iops = True
                    pass
                report = report + "\n" + "VolumeId: {} | State: {} | Size: {} | VolumeType: {} | Iops: {} | CreateTime: {}\n".format(
                    str(volume['VolumeId']),
                    str(volume['State']),
                    str(volume['Size']),
                    str(volume['VolumeType']),
                    '' if no_iops else str(volume['Iops']),
                    str(volume['CreateTime'])
                )
                #Pls dont enable the below 3-lines.This is just for notifying about EBS available volumes to team
            #ec2.delete_volume(
               # VolumeId=volume['VolumeId']
                # )

    if volume_count == 0:
        print("Nothing to report")
    else:
        response = ses.send_email(
        Source = email_from,
        Destination={
            #'ToAddresses': [
            #    email_to,

          #  ],
              # 'CcAddresses': email_cc,
               'BccAddresses': email_bcc,

        },
        Message={
            'Subject': {
                'Data': emaiL_subject
            },
            'Body': {
                'Text': {
                    'Data': report
                }
            }
        }
        )
        print(report)
        report = "The Following Devbox account EBS Volumes were found as Orphaned/Unattached,Will be deleted within 7 days: \n"\
        "Note: If the volume needs to reuse before clean-up then please feel free to reach out to 'example@gmail.com' within the period of time." + "\n"
