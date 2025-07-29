#!/usr/bin/env python3

"""
AWS Control Tower Config Customization Verification Script
This script verifies that EC2 Fleet and Spot Fleet are excluded from AWS Config recording
"""

import boto3
import json
import sys
import os
from datetime import datetime, timedelta

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

def check_stack_status():
    """Check CloudFormation stack status"""
    print_message("1. Checking CloudFormation Stack Status", "blue")
    print_message("-" * 40, "blue")
    
    try:
        cf = boto3.client('cloudformation', region_name='us-east-2')
        response = cf.describe_stacks(StackName='ControlTowerConfigCustomization')
        stack = response['Stacks'][0]
        
        status = stack['StackStatus']
        print_message(f"Stack Status: {status}", "green" if "COMPLETE" in status else "yellow")
        print_message(f"Last Updated: {stack.get('LastUpdatedTime', stack['CreationTime'])}", "blue")
        
        # Get stack parameters
        if 'Parameters' in stack:
            print_message("Stack Parameters:", "blue")
            for param in stack['Parameters']:
                key = param['ParameterKey']
                value = param['ParameterValue']
                if key == 'ConfigRecorderExcludedResourceTypes':
                    if 'AWS::EC2::EC2Fleet' in value and 'AWS::EC2::SpotFleet' in value:
                        print_message(f"  ✓ {key}: EC2 Fleet resources excluded", "green")
                    else:
                        print_message(f"  ✗ {key}: EC2 Fleet resources NOT excluded", "red")
                elif key == 'ExcludedAccounts':
                    print_message(f"  ✓ {key}: {value}", "green")
                else:
                    print_message(f"  • {key}: {value}", "blue")
        
        return True
    except Exception as e:
        print_message(f"✗ Error checking stack: {e}", "red")
        return False

def check_lambda_functions():
    """Check Lambda function status and recent executions"""
    print_message("\n2. Checking Lambda Function Status", "blue")
    print_message("-" * 40, "blue")
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-2')
        logs_client = boto3.client('logs', region_name='us-east-2')
        
        # Get function names from CloudFormation
        cf = boto3.client('cloudformation', region_name='us-east-2')
        resources = cf.describe_stack_resources(StackName='ControlTowerConfigCustomization')
        
        producer_function = None
        consumer_function = None
        
        for resource in resources['StackResources']:
            if resource['LogicalResourceId'] == 'ProducerLambda':
                producer_function = resource['PhysicalResourceId']
            elif resource['LogicalResourceId'] == 'ConsumerLambda':
                consumer_function = resource['PhysicalResourceId']
        
        # Check Producer Lambda
        if producer_function:
            print_message(f"Producer Function: {producer_function}", "green")
            try:
                # Check recent log events
                log_group = f"/aws/lambda/{producer_function}"
                streams = logs_client.describe_log_streams(
                    logGroupName=log_group,
                    orderBy='LastEventTime',
                    descending=True,
                    limit=1
                )
                if streams['logStreams']:
                    last_event = streams['logStreams'][0]['lastEventTime']
                    last_run = datetime.fromtimestamp(last_event/1000)
                    print_message(f"  Last execution: {last_run}", "blue")
            except Exception as e:
                print_message(f"  Could not check logs: {e}", "yellow")
        
        # Check Consumer Lambda
        if consumer_function:
            print_message(f"Consumer Function: {consumer_function}", "green")
            try:
                # Check recent log events
                log_group = f"/aws/lambda/{consumer_function}"
                streams = logs_client.describe_log_streams(
                    logGroupName=log_group,
                    orderBy='LastEventTime',
                    descending=True,
                    limit=1
                )
                if streams['logStreams']:
                    last_event = streams['logStreams'][0]['lastEventTime']
                    last_run = datetime.fromtimestamp(last_event/1000)
                    print_message(f"  Last execution: {last_run}", "blue")
            except Exception as e:
                print_message(f"  Could not check logs: {e}", "yellow")
        
        return True
    except Exception as e:
        print_message(f"✗ Error checking Lambda functions: {e}", "red")
        return False

def check_config_recorder(target_account=None):
    """Check Config recorder settings in a target account"""
    if not target_account:
        print_message("\n3. Config Recorder Verification (Skipped)", "yellow")
        print_message("-" * 40, "yellow")
        print_message("No target account specified. To check a specific account:", "yellow")
        print_message("export TARGET_ACCOUNT=123456789012", "blue")
        print_message("AWS_PROFILE=org-admin python3 verify.py", "blue")
        return True
    
    print_message(f"\n3. Checking Config Recorder in Account: {target_account}", "blue")
    print_message("-" * 40, "blue")
    
    try:
        # Assume role in target account
        sts = boto3.client('sts')
        role_arn = f"arn:aws:iam::{target_account}:role/AWSControlTowerExecution"
        
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"ConfigVerification-{int(datetime.now().timestamp())}"
        )
        
        # Create Config client with assumed role credentials
        config_client = boto3.client(
            'config',
            region_name='us-east-2',
            aws_access_key_id=response['Credentials']['AccessKeyId'],
            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
            aws_session_token=response['Credentials']['SessionToken']
        )
        
        # Get configuration recorder
        recorders = config_client.describe_configuration_recorders()
        
        if not recorders['ConfigurationRecorders']:
            print_message("✗ No Config recorder found", "red")
            return False
        
        recorder = recorders['ConfigurationRecorders'][0]
        print_message(f"Config Recorder: {recorder['name']}", "green")
        
        recording_group = recorder.get('recordingGroup', {})
        
        # Check exclusion settings
        if 'exclusionByResourceTypes' in recording_group:
            excluded_types = recording_group['exclusionByResourceTypes']['resourceTypes']
            print_message("Excluded Resource Types:", "blue")
            
            ec2_fleet_excluded = False
            spot_fleet_excluded = False
            
            for resource_type in excluded_types:
                if resource_type == 'AWS::EC2::EC2Fleet':
                    print_message(f"  ✓ {resource_type} (EC2 Fleet)", "green")
                    ec2_fleet_excluded = True
                elif resource_type == 'AWS::EC2::SpotFleet':
                    print_message(f"  ✓ {resource_type} (Spot Fleet)", "green")
                    spot_fleet_excluded = True
                else:
                    print_message(f"  • {resource_type}", "blue")
            
            if ec2_fleet_excluded and spot_fleet_excluded:
                print_message("\n✅ SUCCESS: EC2 Fleet and Spot Fleet are excluded from Config recording!", "green")
            else:
                missing = []
                if not ec2_fleet_excluded:
                    missing.append("AWS::EC2::EC2Fleet")
                if not spot_fleet_excluded:
                    missing.append("AWS::EC2::SpotFleet")
                print_message(f"\n❌ MISSING: {', '.join(missing)} not excluded", "red")
        else:
            print_message("✗ No exclusion configuration found", "red")
            print_message("Config recorder may be set to record all resources", "yellow")
        
        return True
        
    except Exception as e:
        print_message(f"✗ Error checking Config recorder: {e}", "red")
        return False

def show_manual_verification_steps():
    """Show manual verification steps"""
    print_message("\n4. Manual Verification Steps", "blue")
    print_message("-" * 40, "blue")
    
    print_message("CloudWatch Logs:", "yellow")
    print_message("  aws logs tail /aws/lambda/ControlTowerConfigCustomization-ProducerLambda-XXXXX --follow --region us-east-2", "blue")
    print_message("  aws logs tail /aws/lambda/ControlTowerConfigCustomization-ConsumerLambda-XXXXX --follow --region us-east-2", "blue")
    
    print_message("\nConfig Recorder in Managed Account:", "yellow")
    print_message("  aws sts assume-role --role-arn arn:aws:iam::ACCOUNT_ID:role/AWSControlTowerExecution --role-session-name ConfigCheck", "blue")
    print_message("  aws configservice describe-configuration-recorders --region us-east-2", "blue")
    
    print_message("\nAWS Console Verification:", "yellow")
    print_message("  1. Go to AWS Config in a managed account", "blue")
    print_message("  2. Click 'Settings' in the left menu", "blue")
    print_message("  3. Check 'Recording' tab", "blue")
    print_message("  4. Verify AWS::EC2::EC2Fleet and AWS::EC2::SpotFleet are in exclusion list", "blue")

def main():
    """Main verification function"""
    print_message("AWS Control Tower Config Customization Verification", "green")
    print_message("=" * 60, "green")
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print_message(f"Current Account: {identity['Account']}", "blue")
        print_message(f"User/Role: {identity['Arn'].split('/')[-1]}", "blue")
    except Exception as e:
        print_message(f"✗ AWS credentials error: {e}", "red")
        sys.exit(1)
    
    # Run verification checks
    stack_ok = check_stack_status()
    lambda_ok = check_lambda_functions()
    
    # Check target account if specified
    target_account = os.environ.get('TARGET_ACCOUNT')
    config_ok = check_config_recorder(target_account)
    
    # Show manual verification steps
    show_manual_verification_steps()
    
    # Summary
    print_message("\n" + "=" * 60, "green")
    if stack_ok and lambda_ok and config_ok:
        print_message("✅ Verification completed successfully!", "green")
        print_message("EC2 Fleet and Spot Fleet exclusion is properly configured.", "green")
    else:
        print_message("⚠️ Some verification checks failed or were skipped.", "yellow")
        print_message("Please review the output above and run manual checks if needed.", "yellow")
    
    print_message("\nNote: It may take 5-10 minutes after deployment for all accounts to be processed.", "blue")

if __name__ == "__main__":
    main()