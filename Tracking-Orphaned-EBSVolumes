import boto3
import logging
from datetime import *

logger = logging.getLogger()
logger.setLevel(logging.WARNING)

ec2 = boto3.resource('ec2', region_name="us-west-2")
sns = boto3.resource('sns')
platform_endpoint = sns.PlatformEndpoint('arn:aws:sns:us-west-2:<AWS-Account-ID>:<SNS-Topic-Name>')

today = datetime.now().date()

def lambda_handler(event, context):

    #Collecting all the EBS volumes in AWS region
    volumes = ec2.volumes.all()
    MessageToReport = "The Following EBS Volumes are Orphaned.Please have a look at: \n"
    x = 0

    for vol in volumes:
        if vol.state == "available":
            MessageToReport = MessageToReport + "\n" + "Volume ID: " + str(vol.id) + " - Volume Size: " + str(vol.size) + " - Created Date: " + str(vol.create_time) + "\n"
            x= x + 1

    #only send a Message to report if there are any Unattached EBS Volume
    if x == 0:
        print "Nothing to Report"
    else:
        response = platform_endpoint.publish(
            Message=MessageToReport,
            Subject='EBS Orphaned Volumes Report: ' + str(today),
            MessageStructure='string',
        )

        print MessageToReport
