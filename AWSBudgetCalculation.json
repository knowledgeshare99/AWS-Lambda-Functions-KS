#!/usr/bin/python

"""
    This Lambda function is designed to keep track of AWS account expenses.
    This Lambda will get executed on first date of every month.
    This Lambda will take costs of the previous 3 months, get average of last 3 months costs and set that average as Budget for current month.
    This Lambda will set notification alerts if your expense crosses 110% of the current month budget.
"""

import boto3
import datetime
import locale
import os
from dateutil.relativedelta import *
from datetime import date, timedelta
import json
import time

# This is AWS Devbox Environment account ID
AccountId='xxxxxxxxx'

# This function is to get first date of a month. Input will be any date of month.
def get_first_day(dt, d_years=0, d_months=0):
    y, m = dt.year + d_years, dt.month + d_months
    a, m = divmod(m-1, 12)
    return date(y+a, m+1, 1)

#This function is to get last date of a month. Input will be any date of month.
def get_last_day(dt):
    return get_first_day(dt, 0, 1) + timedelta(-1)

# This function is to delete previous budget and create new budget.
def lambda_handler(context,event):
    ce = boto3.client('ce')
    budgetClient = boto3.client('budgets')

    responseStatus = 'SUCCESS'
    responseData = {}

    # Here we are listing existing budgets.
    print "first list the existing budgets"
    response = budgetClient.describe_budgets(AccountId=AccountId, MaxResults= 99)
    print response

    # Here we will delete previous budget with same name.
    print "deleting the budget"
    try:
        response = budgetClient.delete_budget(AccountId=AccountId, BudgetName='AWS_Budget_DEV')
        print response
    except:
        pass

    # To get average cost of last 3 months, we are getting first date of last third month and
    # we are taking end date as todays date.
    Start_Date=str(datetime.date.today() - relativedelta(months=3))
    End_Date=str(datetime.date.today())

    startdt = get_first_day(datetime.date.today())
    enddt = get_last_day(datetime.date.today() + relativedelta(days=1))
    start= int(time.mktime(startdt.timetuple()))
    end= int(time.mktime(enddt.timetuple()))

    #using get_cost_and_usage api to calculate AWS resource costs
    response = ce.get_cost_and_usage(TimePeriod={ 'Start': Start_Date, 'End': End_Date}, Granularity= 'MONTHLY', Metrics= ['BlendedCost'])

    #Here we are collecting last 3 months cost data for API response came from previous API call.
    amt1=(response["ResultsByTime"][0]["Total"]["BlendedCost"]["Amount"])
    amt2=(response["ResultsByTime"][1]["Total"]["BlendedCost"]["Amount"])
    amt3=(response["ResultsByTime"][2]["Total"]["BlendedCost"]["Amount"])

    # Calculate average costs of last 3 moths, that average amount will go as next budget amount.
    avg= (int(locale.atof(amt1))+int(locale.atof(amt2))+int(locale.atof(amt3)))/3

    """
        In this call we are going to create new budget with average of last 3 months
        and we are going to set notification if budget reaches 110% of actual budget.
        For notification we are using SNS topic, which is already created.
    """
    response = budgetClient.create_budget(
    AccountId=AccountId,
    Budget={
        'BudgetName': 'AWS_Budget_DEV',
        'BudgetLimit': {
            'Amount': str(avg),
            'Unit': 'USD'
        },
        'CostFilters': {
            "AZ": ["us-west-2"]

        },
        'CostTypes': {
            'IncludeTax': True,
            'IncludeSubscription': True,
            'UseBlended': False,
            'IncludeRefund': True,
            'IncludeCredit': True,
            'IncludeUpfront': True,
            'IncludeRecurring': True,
            'IncludeOtherSubscription': True,
            'IncludeSupport': True,
            'IncludeDiscount': True,
            'UseAmortized': True
        },
        'TimeUnit': 'MONTHLY',
        'TimePeriod': {
            'Start': start,
            'End': end
        },
        'BudgetType': 'COST'
    },
    NotificationsWithSubscribers=[
        {
            'Notification': {
                'NotificationType': 'ACTUAL',
                'ComparisonOperator': 'GREATER_THAN',
                'Threshold': 110,
                'ThresholdType': 'PERCENTAGE'
            },
            'Subscribers': [
                {
                    'SubscriptionType': 'SNS',
                    'Address': 'arn:aws:sns:us-west-2:xxxxxxx:AWS_Budget_DEV'
                },
            ]
        }
    ]
    )
    return 'BudgetLambda Executed'


if __name__ == '__main__':
    lambda_handler('event', 'handler')
