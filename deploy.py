#!/usr/bin/env python3

"""
AWS Control Tower Config Customization Deployment Script
This Python script deploys the solution to exclude EC2 Fleet and Spot Fleet from AWS Config recording
"""

import boto3
import json
import time
import sys
import os
from datetime import datetime

def print_message(message, color=""):
    """Print colored message"""
    colors = {
        "green": "\033[0;32m",
        "red": "\033[0;31m", 
        "yellow": "\033[1;33m",
        "blue": "\033[0;34m",
        "nc": "\033[0m"
    }
    color_code = colors.get(color, "")
    reset_code = colors["nc"]
    print(f"{color_code}{message}{reset_code}")

def check_aws_credentials():
    """Verify AWS credentials are working"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print_message(f"✓ AWS credentials verified", "green")
        print_message(f"  Account: {identity['Account']}", "blue")
        print_message(f"  User/Role: {identity['Arn']}", "blue")
        return identity['Account']
    except Exception as e:
        print_message(f"✗ AWS credentials error: {e}", "red")
        sys.exit(1)

def deploy_stack():
    """Deploy the CloudFormation stack"""
    
    # Configuration
    STACK_NAME = "ControlTowerConfigCustomization"
    EXCLUDED_ACCOUNTS = "['891377069955', '058264522153', '211125586359']"
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-2')
    EXCLUDED_RESOURCE_TYPES = "AWS::HealthLake::FHIRDatastore,AWS::Pinpoint::Segment,AWS::Pinpoint::ApplicationSettings,AWS::EC2::EC2Fleet,AWS::EC2::SpotFleet"
    
    print_message("AWS Control Tower Config Customization Deployment", "green")
    print_message("=" * 60, "green")
    
    # Check credentials
    current_account = check_aws_credentials()
    
    print_message(f"Configuration:", "yellow")
    print_message(f"  Stack Name: {STACK_NAME}", "blue")
    print_message(f"  Region: {AWS_REGION}", "blue")
    print_message(f"  Excluded Accounts: {EXCLUDED_ACCOUNTS}", "blue")
    print_message(f"  Excluded Resource Types: EC2Fleet, SpotFleet (and others)", "blue")
    
    # Initialize CloudFormation client
    try:
        cf = boto3.client('cloudformation', region_name=AWS_REGION)
    except Exception as e:
        print_message(f"✗ Failed to initialize CloudFormation client: {e}", "red")
        sys.exit(1)
    
    # Read template
    try:
        with open('template.yaml', 'r') as f:
            template_body = f.read()
    except FileNotFoundError:
        print_message("✗ template.yaml not found. Please run from the correct directory.", "red")
        sys.exit(1)
    
    # Prepare parameters
    parameters = [
        {
            'ParameterKey': 'ExcludedAccounts',
            'ParameterValue': EXCLUDED_ACCOUNTS
        },
        {
            'ParameterKey': 'ConfigRecorderExcludedResourceTypes', 
            'ParameterValue': EXCLUDED_RESOURCE_TYPES
        },
        {
            'ParameterKey': 'ConfigRecorderStrategy',
            'ParameterValue': 'EXCLUSION'
        },
        {
            'ParameterKey': 'CloudFormationVersion',
            'ParameterValue': str(int(time.time()))
        }
    ]
    
    # Check if stack exists
    stack_exists = False
    try:
        cf.describe_stacks(StackName=STACK_NAME)
        stack_exists = True
        print_message(f"Stack '{STACK_NAME}' exists, updating...", "yellow")
    except cf.exceptions.ClientError:
        print_message(f"Creating new stack '{STACK_NAME}'...", "yellow")
    
    try:
        if stack_exists:
            # Update existing stack
            response = cf.update_stack(
                StackName=STACK_NAME,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM']
            )
            operation = "update"
        else:
            # Create new stack
            response = cf.create_stack(
                StackName=STACK_NAME,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM']
            )
            operation = "create"
        
        print_message(f"✓ Stack {operation} initiated successfully", "green")
        print_message(f"  Stack ID: {response['StackId']}", "blue")
        
    except cf.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'ValidationError' and 'No updates are to be performed' in error_message:
            print_message("✓ Stack is already up to date", "green")
            return
        else:
            print_message(f"✗ Stack deployment failed: {error_message}", "red")
            sys.exit(1)
    
    # Wait for completion
    print_message("Waiting for stack operation to complete...", "yellow")
    
    waiter_name = 'stack_create_complete' if not stack_exists else 'stack_update_complete'
    waiter = cf.get_waiter(waiter_name)
    
    try:
        waiter.wait(
            StackName=STACK_NAME,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 40  # 20 minutes max
            }
        )
        print_message("✓ Stack deployment completed successfully!", "green")
        
        # Get stack outputs
        try:
            stack_info = cf.describe_stacks(StackName=STACK_NAME)
            stack = stack_info['Stacks'][0]
            print_message(f"  Stack Status: {stack['StackStatus']}", "green")
            
            if 'Outputs' in stack:
                print_message("Stack Outputs:", "blue")
                for output in stack['Outputs']:
                    print_message(f"  {output['OutputKey']}: {output['OutputValue']}", "blue")
        except Exception as e:
            print_message(f"Warning: Could not retrieve stack outputs: {e}", "yellow")
        
    except Exception as e:
        print_message(f"✗ Stack deployment failed or timed out: {e}", "red")
        
        # Get stack events to show what went wrong
        try:
            events = cf.describe_stack_events(StackName=STACK_NAME)
            print_message("Recent stack events:", "yellow")
            for event in events['StackEvents'][:5]:  # Show last 5 events
                timestamp = event['Timestamp'].strftime('%H:%M:%S')
                status = event.get('ResourceStatus', 'N/A')
                reason = event.get('ResourceStatusReason', 'N/A')
                resource = event.get('LogicalResourceId', 'N/A')
                print_message(f"  {timestamp} {resource}: {status} - {reason}", "yellow")
        except Exception:
            pass
            
        sys.exit(1)
    
    print_message("=" * 60, "green")
    print_message("Next steps:", "yellow")
    print_message("1. Wait 5-10 minutes for the solution to process all accounts", "blue")
    print_message("2. Run verification: AWS_PROFILE=org-admin python3 verify.py", "blue")
    print_message("3. Check specific accounts in AWS Config console", "blue")

if __name__ == "__main__":
    deploy_stack()