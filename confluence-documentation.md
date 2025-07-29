# AWS Control Tower Config Customization Solution

## Executive Summary

The AWS Control Tower Config Customization solution provides an automated approach to exclude specific AWS resource types from AWS Config recording across all Control Tower managed accounts. This implementation specifically excludes EC2 Fleet and EC2 Spot Fleet resources, which are commonly used for dynamic compute workloads and can generate excessive Config recording costs without providing significant compliance value.

### Key Benefits
- **Cost Optimization**: Reduces AWS Config costs by excluding high-volume, transient resources
- **Automated Management**: Applies exclusions automatically to all existing and new Control Tower accounts
- **Compliance Maintained**: Preserves Control Tower baseline compliance while customizing Config recording
- **Scalable Solution**: Works seamlessly as new accounts are added to the organization

## Architecture Overview

### Solution Components

The solution implements a Producer-Consumer Lambda pattern that responds to Control Tower lifecycle events:

**Architecture Flow:**

| Step | Component | Action | Next Step |
|------|-----------|--------|-----------|
| 1 | **Control Tower Lifecycle Events** | Triggers when accounts are created/updated | → Producer Lambda |
| 2 | **Producer Lambda (Event Handler)** | Receives events via EventBridge | → SQS Queue |
| 3 | **SQS Queue (Message Buffer)** | Stores account processing requests | → Consumer Lambda |
| 4 | **Consumer Lambda (Config Updater)** | Processes messages from queue | → Target Account |
| 5 | **Target Account Config Recorder** | Updated with exclusion settings | ✓ Complete |

**Detailed Component Flow:**
```
Control Tower Events --> Producer Lambda --> SQS Queue --> Consumer Lambda --> Config Recorder Updates
```

**Event Types Processed:**
- Account creation events
- Account update events
- Landing Zone update events

### Component Details

1. **Producer Lambda Function**
   - Monitors Control Tower lifecycle events via EventBridge
   - Triggers on: Account creation, Account updates, Landing Zone updates
   - Filters excluded accounts (Management, Log Archive, Audit)
   - Sends account information to SQS queue for processing

2. **Consumer Lambda Function**
   - Processes messages from SQS queue
   - Assumes AWSControlTowerExecution role in target accounts
   - Updates Config recorder settings to exclude specified resource types
   - Applies daily recording frequency for specific resource types

3. **SQS Queue**
   - Provides reliable message delivery between Lambda functions
   - Enables retry logic and error handling
   - Decouples event processing from Config updates

## Environment Configuration

### AWS Control Tower Setup
| Parameter | Value |
|-----------|--------|
| Management Account | 891377069955 |
| Log Archive Account | 058264522153 |
| Audit Account | 211125586359 |
| Control Tower Home Region | us-east-2 |
| AWS CLI Profile | org-admin |
| CloudFormation Stack Name | ControlTowerConfigCustomization |

### Excluded Resource Types
The solution excludes the following resource types from AWS Config recording:

| Resource Type | Description | Status |
|---------------|-------------|---------|
| AWS::EC2::EC2Fleet | EC2 Fleet configurations | ✅ Newly Added |
| AWS::EC2::SpotFleet | EC2 Spot Fleet configurations | ✅ Newly Added |
| AWS::HealthLake::FHIRDatastore | HealthLake FHIR datastores | Existing |
| AWS::Pinpoint::Segment | Pinpoint segments | Existing |
| AWS::Pinpoint::ApplicationSettings | Pinpoint application settings | Existing |

## Prerequisites

Before deploying the solution, ensure you have:

1. **AWS CLI Configuration**
   - AWS CLI installed (version 2.x recommended)
   - Configured with appropriate credentials
   - Profile `org-admin` with Control Tower management account access

2. **Required Permissions**
   - Access to Control Tower management account (891377069955)
   - Permissions to create CloudFormation stacks
   - IAM permissions for Lambda and SQS resource creation

3. **Python Environment**
   - Python 3.x installed
   - boto3 library available (`pip install boto3`)
   - Access to run Python scripts from command line

4. **Control Tower Status**
   - Control Tower fully deployed and operational
   - All managed accounts enrolled successfully
   - Landing Zone version is current

## Deployment Instructions

### Step 1: Clone or Download the Solution

Ensure you have the solution files in your local environment:
```bash
cd config-customization/aws-control-tower-config-customization
```

### Step 2: Review Configuration

Verify the deployment configuration in `deploy.py`:
- Stack Name: ControlTowerConfigCustomization
- Excluded Accounts: Management, Log Archive, Audit accounts
- Excluded Resource Types: EC2 Fleet and Spot Fleet resources

### Step 3: Deploy the Solution

Execute the deployment script with the configured AWS profile:

```bash
AWS_PROFILE=org-admin python3 deploy.py
```

The deployment script will:
1. Verify AWS credentials
2. Create/Update the CloudFormation stack
3. Deploy Lambda functions and supporting resources
4. Configure EventBridge rules for Control Tower events
5. Wait for deployment completion

Expected output:
```
AWS Control Tower Config Customization Deployment
============================================================
✓ AWS credentials verified
  Account: 891377069955
  User/Role: arn:aws:iam::891377069955:user/admin
Configuration:
  Stack Name: ControlTowerConfigCustomization
  Region: us-east-2
  Excluded Accounts: ['891377069955', '058264522153', '211125586359']
  Excluded Resource Types: EC2Fleet, SpotFleet (and others)
Creating new stack 'ControlTowerConfigCustomization'...
✓ Stack create initiated successfully
Waiting for stack operation to complete...
✓ Stack deployment completed successfully!
```

### Step 4: Verify Deployment

Run the verification script to confirm successful deployment:

```bash
AWS_PROFILE=org-admin python3 verify.py
```

For complete verification including a managed account check:
```bash
export TARGET_ACCOUNT="123456789012"  # Replace with your managed account ID
AWS_PROFILE=org-admin python3 verify.py
```

## Verification Procedures

### Automated Verification

The `verify.py` script performs the following checks:

1. **CloudFormation Stack Status**
   - Confirms stack is in COMPLETE state
   - Verifies stack parameters include EC2 Fleet exclusions
   - Shows last update timestamp

2. **Lambda Function Status**
   - Checks Producer and Consumer Lambda deployment
   - Reviews recent execution logs
   - Confirms EventBridge rule configuration

3. **Config Recorder Settings** (if TARGET_ACCOUNT specified)
   - Assumes role in target account
   - Retrieves Config recorder configuration
   - Confirms exclusion list contains EC2 Fleet resources

### Manual Verification

#### Option 1: AWS Console
1. Navigate to AWS Config in any managed account
2. Click "Settings" in the left navigation menu
3. Select the "Recording" tab
4. Verify the exclusion list contains:
   - AWS::EC2::EC2Fleet
   - AWS::EC2::SpotFleet

#### Option 2: AWS CLI
```bash
# Assume role in managed account
aws sts assume-role \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/AWSControlTowerExecution \
  --role-session-name ConfigCheck

# Check Config recorder settings
aws configservice describe-configuration-recorders \
  --region us-east-2 \
  --query 'ConfigurationRecorders[0].recordingGroup.exclusionByResourceTypes.resourceTypes'
```

### Monitoring Lambda Executions

View real-time Lambda logs:
```bash
# Get Lambda function names
aws cloudformation describe-stack-resources \
  --stack-name ControlTowerConfigCustomization \
  --region us-east-2 \
  --profile org-admin \
  --query 'StackResources[?ResourceType==`AWS::Lambda::Function`].PhysicalResourceId'

# Tail logs for Producer Lambda
aws logs tail /aws/lambda/[ProducerFunctionName] --follow --region us-east-2 --profile org-admin

# Tail logs for Consumer Lambda
aws logs tail /aws/lambda/[ConsumerFunctionName] --follow --region us-east-2 --profile org-admin
```

## Troubleshooting Guide

### Common Issues and Resolutions

#### 1. Deployment Fails with "No updates are to be performed"
**Cause**: Stack is already up-to-date with no changes
**Resolution**: This is expected behavior. The stack is already deployed correctly.

#### 2. Consumer Lambda Fails with Access Denied
**Cause**: AWSControlTowerExecution role missing in target account
**Resolution**: 
- Verify account is enrolled in Control Tower
- Check Control Tower dashboard for enrollment status
- Re-enroll account if necessary

#### 3. Config Recorder Not Updated After Deployment
**Cause**: Processing delay or Lambda execution failure
**Resolution**:
- Wait 5-10 minutes for propagation
- Check Lambda logs for errors
- Manually trigger update by updating stack with new timestamp

#### 4. Stack Creation Fails with IAM Error
**Cause**: Insufficient permissions in deployment account
**Resolution**:
- Verify using Control Tower management account
- Ensure AWS profile has AdministratorAccess
- Check AWS Organizations SCPs for restrictions

### Debug Commands

```bash
# Check SQS queue for pending messages
aws sqs get-queue-attributes \
  --queue-url [QueueURL] \
  --attribute-names ApproximateNumberOfMessages \
  --region us-east-2 \
  --profile org-admin

# View recent Control Tower events
aws events list-rules \
  --name-prefix ControlTower \
  --region us-east-2 \
  --profile org-admin

# Check Lambda function configuration
aws lambda get-function-configuration \
  --function-name [FunctionName] \
  --region us-east-2 \
  --profile org-admin
```

## Rollback Procedures

### Option 1: Complete Stack Deletion (Recommended)

Remove the solution and restore Control Tower defaults:

```bash
aws cloudformation delete-stack \
  --stack-name ControlTowerConfigCustomization \
  --region us-east-2 \
  --profile org-admin

# Monitor deletion
aws cloudformation wait stack-delete-complete \
  --stack-name ControlTowerConfigCustomization \
  --region us-east-2 \
  --profile org-admin
```

### Option 2: Modify Exclusion List

Update the stack to remove specific exclusions:

1. Edit `template.yaml`
2. Modify the `ConfigRecorderExcludedResourceTypes` parameter default value
3. Remove "AWS::EC2::EC2Fleet,AWS::EC2::SpotFleet" from the list
4. Redeploy: `AWS_PROFILE=org-admin python3 deploy.py`

### Post-Rollback Verification

After rollback, verify Config recorders have reverted:
```bash
# Check a managed account
aws configservice describe-configuration-recorders \
  --region us-east-2 \
  --query 'ConfigurationRecorders[0].recordingGroup'
```

## Best Practices and Recommendations

### 1. Testing Strategy
- Always test in a non-production Control Tower environment first
- Verify with a subset of accounts before organization-wide deployment
- Monitor Config costs before and after implementation

### 2. Maintenance Guidelines
- Review excluded resource types quarterly
- Monitor Lambda function errors via CloudWatch
- Keep Python scripts updated with latest boto3 version

### 3. Security Considerations
- Solution uses existing Control Tower execution roles
- No additional IAM permissions required in member accounts
- All actions are logged in CloudTrail

### 4. Cost Optimization Tips
- Consider excluding additional high-volume resource types
- Monitor Config usage in Cost Explorer
- Set up billing alerts for Config service

## Additional Resources

### AWS Documentation
- [AWS Config Supported Resource Types](https://docs.aws.amazon.com/config/latest/developerguide/resource-config-reference.html) - REFERENCE(context7:aws-config-resource-types)
- [AWS Control Tower User Guide](https://docs.aws.amazon.com/controltower/latest/userguide/) - REFERENCE(context7:control-tower-user-guide)
- [AWS Config Pricing](https://aws.amazon.com/config/pricing/) - REFERENCE(context7:aws-config-pricing)

### Solution Files
- **template.yaml** - CloudFormation template with Lambda functions and resources
- **deploy.py** - Python deployment script with pre-configured values
- **verify.py** - Comprehensive verification script
- **ct_configrecorder_override_producer.py** - Producer Lambda source code
- **ct_configrecorder_override_consumer.py** - Consumer Lambda source code

### Support Contacts
For issues or questions:
1. Check CloudFormation stack events for deployment errors
2. Review Lambda CloudWatch logs for execution issues
3. Verify IAM permissions and Control Tower status
4. Contact your AWS TAM or Solutions Architect for advanced support

---

*Last Updated: January 2025*
*Version: 1.0 - EC2 Fleet Exclusion Implementation*