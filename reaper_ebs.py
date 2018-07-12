import boto3


ec2 = boto3.resource('ec2')


def lambda_handler(event, context):
    print('Checking for unused EBS volumes')
    for volume in ec2.volumes.all():
        if volume.state == 'available':
            if volume.tags is None:
                volume_id = volume.id
                volume_to_delete = ec2.Volume(volume.id)
                try:
                    volume_to_delete.delete()
                    print("deleted unattached volume: " + str(volume_id))
                except Exception as e:
                    print('FAILED to delete volume: ' + str(volume_id))
                    print(str(e))
                continue

            for tag in volume.tags:
                if tag['Key'] == 'Name':
                    value = tag['Value']
                    if value != 'do not delete' and volume.state == 'available':
                        volume_id = volume.id
                        volume_to_delete = ec2.Volume(volume.id)
                        try:
                            volume_to_delete.delete()
                            print("deleted unattached volume: " + str(volume_id))
                        except Exception as e:
                            print('FAILED to delete volume: ' + str(volume_id))
                            print(str(e))
