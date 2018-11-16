import boto3
import logging
from datetime import *
import pdb

ses = boto3.client('ses')

email_from = 'knowledgeshare99@gmail.com'
email_to = 'knowledgeshare99@gmail.com'
email_cc = ['knowledgeshare99@gmail.com', 'knowledgeshare99@gmail.com']
emaiL_subject = 'EBS Orphaned volumes Report'
report = "The Following Volumes were found as Orphaned and deleted those volumes :\n"

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
                report = report + "VolumeId: {} | State: {} | Size: {} | VolumeType: {} | Iops: {} | CreateTime: {}\n".format(
                    str(volume['VolumeId']),
                    str(volume['State']),
                    str(volume['Size']),
                    str(volume['VolumeType']),
                    '' if no_iops else str(volume['Iops']),
                    str(volume['CreateTime'])
                )
                # Take some action?
                #Deleting Unattached EBS Volumes
            ec2.delete_volume(
               VolumeId=volume['VolumeId']
               )

    if volume_count == 0:
        print("Nothing to report")
    else:
        response = ses.send_email(
        Source = email_from,
        Destination={
            'ToAddresses': [
                email_to,
            ],
            'CcAddresses': email_cc
            
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
        report = "The Following Volumes were found as Orphaned and deleted those volumes:\n"
