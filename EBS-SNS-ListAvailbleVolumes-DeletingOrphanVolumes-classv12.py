import boto3
import logging
from datetime import *

logger = logging.getLogger()
logger.setLevel(logging.WARNING)

ec2 = boto3.resource('ec2', region_name="us-west-2")
sns = boto3.resource('sns')
platform_endpoint = sns.PlatformEndpoint('arn:aws:sns:us-west-2:<your_accountid>:classv12-topic')

today = datetime.now().date()

def lambda_handler(event, context):

    #Collecting all the EBS volumes in AWS region
    volumes = ec2.volumes.all()
    MessageToReport = "The Following EBS Volumes are Orphaned and deleting the listed availble volumes : \n"
    x = 0

    for vol in volumes:
        if vol.state == "available":
            VolumeId = "Volume ID Available " + str(vol.id)
            #ebs_volume = str(vol.id)
            #print(ebs_valume)
            
            print(VolumeId)
            print(vol.id)
            MessageToReport = MessageToReport + "\n" + "Volume ID: " + str(vol.id) + " - Volume Size: " + str(vol.size) + " - Created Date: " + str(vol.create_time) + "\n"
           
            print('Deleting volume {0}'.format(vol.id))
            
            #MessageToReport = MessageToReport + "\n" + "Deleting the available EBS Volumes:"
            delete = vol.delete()
            
           
            
            x= x + 1


    #only send a Message to report if there are any Unattached EBS Volume
    if x == 0:
        print ("Nothing to Report")
        
    # ec2.delete_volume(
    # VolumeId=volume[vol.id])
    else:
        response = platform_endpoint.publish(
            Message=MessageToReport,
            Subject='EBS Orphaned Volumes Report: ' + str(today),
            MessageStructure='string',
        )

        print (MessageToReport)
