import os
import boto3
from datetime import datetime, timezone, timedelta
from dateutil import parser
from botocore.exceptions import ClientError

# Whitelist
WHITELIST = os.environ['WhiteList'].split(';')
allow_deletion = os.environ['AllowDeletion']
reset_date_tag = os.environ['ResetDateTag']
min_terminate = int(os.environ['MinTerminate'])
max_terminate = int(os.environ['MaxTerminate'])
mail_warning_delta = int(os.environ['MailWarningDelta'])

sender = os.environ['Sender']
environment = os.environ['EnvironmentName']

# current datetime
current_timestamp = datetime.now(timezone.utc).date()
minimum_day_timestamp = current_timestamp + timedelta(days=min_terminate)
max_day_timestamp = current_timestamp + timedelta(days=max_terminate)

# boto3 client
ec2 = boto3.client('ec2')


def lambda_handler(event, context):
    """
    Examine all Ec2 instances and check to see if their expiration date has passed.
    :return:
    """
    # retrieve the instances
    try:
        description = ec2.describe_instances()
    except Exception as e:
        print(str(e))
        return

    if 'Reservations' not in description:
        print("ERROR:  unable to retrieve Reservations from description.")
        return

    # loop over each reservation
    count_no_name = 0
    for reservation in description['Reservations']:

        if 'Instances' not in reservation:
            print("ERROR:  no instances found under description reservation.")
            continue

        # loop over each instance in the reservation instances
        for instance in reservation['Instances']:

            # skip terminated instances
            if str(instance['State']['Name']) == 'terminated':
                continue

            name_tag = get_tag(instance, 'Name')
            date_tag = get_tag(instance, 'Expiration_Date')
            email_name = get_tag(instance, 'NotificationEmail')
            date_timestamp = date_to_datetime(date_tag)
            print_instance_info(instance, name_tag, date_tag, email_name)

            # check the whitelist
            if in_whitelist(name_tag):
                print("    On the whitelist and is ignored.")
                continue

            # first check No name tag
            if name_tag is None:
                no_name_tag_handling(instance, date_timestamp, email_name)
                count_no_name += 1
            else:
                with_name_tag_handling(instance, date_timestamp, email_name, name_tag)
    print("Instances with no name tags: ", count_no_name)


def no_name_tag_handling(instance, date_timestamp, email_name):
    """
    For instances with no name tag, either set their expiration date or terminate them
    :param instance:
    :param date_timestamp:
    :param email_name:
    :return:
    """
    # if no name tag, check for no date tag
    if date_timestamp is None or \
            reset_date_tag == 'True' or \
            date_timestamp > minimum_day_timestamp:
        if reset_date_tag == 'True':
            print("    Resetting expiration date tag.")
        else:
            print("    No name tag and no expiration date tag.")
        print('    New Expiration_Date: ', str(minimum_day_timestamp))
        ec2.create_tags(Resources=[instance['InstanceId']],
                        Tags=[{'Key': 'Expiration_Date', 'Value': str(minimum_day_timestamp)}])
    else:
        # check to see if date has expired
        if date_timestamp < current_timestamp:
            print("    No name tag and EC2 HAS EXPIRED.")
            if allow_deletion:
                print("    EC2: ", instance['InstanceId'], " has been terminated.")
                # terminate the ec2
                ec2.terminate_instances(InstanceIds=[instance['InstanceId']], DryRun=False)
                send_mail(email_name, instance['InstanceId'], 'deletion')


def with_name_tag_handling(instance, date_timestamp, email_name, name_tag):
    """
    For instances with name tags either set their expiration date or terminate them
    :param instance:
    :param date_timestamp:
    :param email_name:
    :param name_tag:
    :return:
    """
    # has name tag: check for no date tag, date tag that is too many days,
    # or if we are resetting all date tags
    if date_timestamp is None or \
            reset_date_tag == 'True' or \
            date_timestamp > max_day_timestamp:
        if reset_date_tag == 'True':
            print("    Resetting expiration date tag.")
        else:
            print("    Name tag found but no expiration date tag.")
        print('    New Expiration_Date: ', str(max_day_timestamp))
        ec2.create_tags(Resources=[instance['InstanceId']],
                        Tags=[{'Key': 'Expiration_Date', 'Value': str(max_day_timestamp)}])
    elif date_timestamp == (current_timestamp+timedelta(days=mail_warning_delta)):
        print("    EC2: ", name_tag, " has been Warned.")
        send_mail(email_name, name_tag, 'warning')
    else:
        # check to see if date has expired
        if date_timestamp < current_timestamp:
            print("    Name tag found but EC2 HAS EXPIRED.")
            if allow_deletion:
                print("    EC2: ", name_tag, " has been terminated.")
                # terminate the ec2
                ec2.terminate_instances(InstanceIds=[instance['InstanceId']], DryRun=False)
                send_mail(email_name, name_tag, 'deletion')
            else:
                print("    EC2: ", name_tag, "was NOT deleted, deletion is OFF.")


def get_tag(instance, tag_name):
    """
    Get the value of the tag
    :param instance:
    :param tag_name:
    :return: The value of the tag or None
    """
    if 'Tags' in instance:
        for tag in instance['Tags']:
            if tag['Key'] == tag_name:
                return tag['Value']

    return None


def in_whitelist(name_tag):
    """
    check to see if id starts with whitelisted qualifier
    :param name_tag:
    :return:
    """
    for whitelist_name in WHITELIST:
        if whitelist_name != '' and name_tag is not None and name_tag.startswith(whitelist_name):
            return True
    return False


def date_to_datetime(date_string):
    try:
        new_datetime = parser.parse(date_string).date()
    except Exception as e:
        new_datetime = None

    return new_datetime


def print_instance_info(instance, name_tag, date_tag, email_name):
    """
    Print out instance information
    :param instance:
    :param name_tag:
    :param date_tag:
    :param email_name:
    :return:
    """
    print("Instance ID: ", instance['InstanceId'])
    print('    Name: ', name_tag)
    print('    Email Name: ', email_name)
    print('    Launched: ', str(instance['LaunchTime']))
    print('    State: ', str(instance['State']))
    print('    Initial Expiration_Date: ', date_tag)


def send_mail(email_name, ec2_name, mail_type):
    """
    Send a mail to the user with a link to Scope, and CC GCOTechDevOpsSupportDL
    """

    # if no email account, return
    if email_name is None:
        return
    email_name = 'xxxx@gmail.com'

    ses = boto3.client('ses')
    destinations = {'ToAddresses': [email_name]}

    # set up mail message depending on mail type
    if mail_type == 'deletion':
        mail_message = mail_deletion(ec2_name)
    elif mail_type == 'warning':
        mail_message = mail_warning(ec2_name)
    else:
        return

    # send out mail
    try:
        ses.send_email(Source=sender, Destination=destinations, Message=mail_message,
                       ReplyToAddresses=[sender], ReturnPath=sender)
        print('    Notification mail sent to: ', email_name)
    except ClientError as ce:
        if type(ce).__name__ == 'MessageRejected':
            print("FAILED the email address you're attempting to use (", sender,
                  ")hasn't been verified yet. Full error details below")
            print(str(type(ce).__name__), ce.args)
        else:
            print('FAILED sending email to: ' + email_name)
            print(str(type(ce).__name__), ce.args)
    except Exception as e:
        print('FAILED sending email to: ', email_name, '. A general expection was caught. Full error details below')
        print(str(e))


def mail_warning(ec2_name):
    """
    Create mail message for warning of ec2 deletion
    :param ec2_name:
    :return:
    """
    mail_subject = 'AWS EC2 instance WARNING in the GCO ' + environment + ' Environment'
    html_body = "<h1>AWS GCO " + environment + " EC2 instance : " + str(ec2_name) + " is " + \
                str(mail_warning_delta) + " days from termination date." \
                "</h1><h2>Your EC2 Instance has been active for " + str(max_terminate-mail_warning_delta) + \
                " days. </h2><p>To keep your EC2 instance active for longer than " + str(max_terminate) + \
                " days, update the Expiration Date tag for the EC2 instance on a regular schedule.</p>" + \
                "<p>If your EC2 instance needs to be active for more than " + str(max_terminate) + \
                " days please contact GCO Tech DevOps and request for your EC2 instance to be whitelisted.<p>" +\
                "<h3>For any questions, please email GCO Tech DevOps: " + sender + "</h3>"
    text_body = "AWS GCO " + environment + \
                " Warning of impending termination of EC2 instance: " + str(ec2_name) + \
                ".  For any questions, please email GCO Tech DevOps: " + sender

    mail_message = {'Subject': {'Data': mail_subject, 'Charset': 'utf8'},
                    'Body': {'Text': {'Data': text_body, 'Charset': 'utf8'},
                             'Html': {'Data': html_body, 'Charset': 'utf8'}}}

    return mail_message


def mail_deletion(ec2_name):
    """
    Create mail message for rds deletion
    :param ec2_name:
    :return:
    """
    mail_subject = 'Termination of AWS EC2 instance in the GCO ' + environment + ' Environment'
    html_body = "<h1>AWS GCO " + environment + " EC2 instance : " + str(ec2_name) + " has been terminated." \
                "</h1><h2>Your EC2 Instance has been active for " + str(max_terminate) + " days. </h2>" + \
                "<p>To keep your EC2 instance active for longer than " + str(max_terminate) + \
                " days in the future, update the Expiration Date tag for the EC2 instance on a regular " + \
                "schedule.</p><p>If your EC2 instance needs to be active for more than 60 days please contact " + \
                "GCO Tech DevOps and request for your RDS instance to be whitelisted.<p>" +\
                "<h3>For any questions, please email GCO Tech DevOps: " + sender + "</h3>"
    text_body = "AWS GCO " + environment + \
                " Termination of EC2 instance: " + str(ec2_name) + \
                ".  For any questions, please email GCO Tech DevOps: " + sender

    mail_message = {'Subject': {'Data': mail_subject, 'Charset': 'utf8'},
                    'Body': {'Text': {'Data': text_body, 'Charset': 'utf8'},
                             'Html': {'Data': html_body, 'Charset': 'utf8'}}}

    return mail_message


if __name__ == '__main__':
    lambda_handler(event=None, context=None)
