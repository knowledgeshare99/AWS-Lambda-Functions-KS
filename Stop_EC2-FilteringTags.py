from __future__ import print_function
import json
import boto3
import time
from datetime import datetime



def lambda_handler(event, context):
    # Use the filter() method of the instances collection to retrieve
    # all running EC2 instances.
    filters = [{'Name': 'tag:AutoOff', 'Values': ['True']}, {'Name': 'instance-state-name', 'Values': ['running']}]

    try:
        #define the connection
        ec2 = boto3.resource('ec2')

        # filter the instances
        instances = ec2.instances.filter(Filters=filters)

        # locate all running instances
        running_instances = [instance.id for instance in instances]

        #print the instances for logging purposes
        print('EC2 running instance(s) detected: ' + str(running_instances))

        # make sure there are actually instances to shut down.
        if len(running_instances) > 0:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # perform the shutdown
            ec2.instances.filter(InstanceIds=running_instances).stop()
            ec2.create_tags(Resources=running_instances, Tags=[{'Key': 'StoppedOn', 'Value': current_time}])
            print('EC2 stopping instance(s): ' + str(running_instances))
            print('EC2 stopped count: ' + str(len(running_instances)))
        else:
            print("EC2 no instances to stop")
    except Exception as e:
        logger.error('EC2 error stopping instance(s): ' + str(e))
        return False
