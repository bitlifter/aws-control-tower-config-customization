# AWS Control Tower Config Customization - EC2 Fleet Exclusion

This solution excludes EC2 Fleet and EC2 Spot Fleet resources from AWS Config recording in your AWS Control Tower environment.

## Current Environment Configuration

**Control Tower Environment:**
- Management Account: `891377069955`
- Log Archive Account: `058264522153`
- Audit Account: `211125586359`
- Control Tower Home Region: `us-east-2`
- AWS Profile: `org-admin`

## Prerequisites

1. **AWS CLI installed and configured** with appropriate permissions
2. **Control Tower Management Account access** - Deploy from your Control Tower management account (`891377069955`)
3. **AWS Profile configured** - The deployment uses the `org-admin` profile
4. **Python 3 and boto3 installed** - Required for the deployment and verification scripts

## Quick Start

### Step 1: Deploy the Solution (Recommended Method)

The simplest deployment method using the pre-configured Python script:

```bash
cd config-customization/aws-control-tower-config-customization
AWS_PROFILE=org-admin python3 deploy.py
```

This script is pre-configured with your account IDs and will:
- Verify AWS credentials with the `org-admin` profile
- Deploy the CloudFormation stack `ControlTowerConfigCustomization`
- Wait for completion and show deployment status
- Include EC2 Fleet and Spot Fleet in the exclusion list

### Step 2: Verify the Deployment

**Basic Verification:**
```bash
AWS_PROFILE=org-admin python3 verify.py
```

**Complete Verification (with managed account check):**
If you have a Control Tower managed account to test:
```bash
export TARGET_ACCOUNT="YOUR_MANAGED_ACCOUNT_ID"  # Replace with actual managed account
AWS_PROFILE=org-admin python3 verify.py
```

## Alternative Deployment Methods

### Manual CloudFormation Deployment (Advanced)

If you prefer to use AWS CLI directly:

```bash
aws cloudformation create-stack \
  --stack-name ControlTowerConfigCustomization \
  --template-body file://template.yaml \
  --parameters \
    ParameterKey=ExcludedAccounts,ParameterValue="['891377069955', '058264522153', '211125586359']" \
    ParameterKey=ConfigRecorderExcludedResourceTypes,ParameterValue="AWS::HealthLake::FHIRDatastore,AWS::Pinpoint::Segment,AWS::Pinpoint::ApplicationSettings,AWS::EC2::EC2Fleet,AWS::EC2::SpotFleet" \
    ParameterKey=ConfigRecorderStrategy,ParameterValue="EXCLUSION" \
  --capabilities CAPABILITY_IAM \
  --region us-east-2 \
  --profile org-admin
```

## What Gets Excluded

The solution excludes these AWS Config resource types from recording:

- ✅ **AWS::EC2::EC2Fleet** - EC2 Fleet configurations (NEWLY ADDED)
- ✅ **AWS::EC2::SpotFleet** - EC2 Spot Fleet configurations (NEWLY ADDED)
- **AWS::HealthLake::FHIRDatastore** (existing)
- **AWS::Pinpoint::Segment** (existing)  
- **AWS::Pinpoint::ApplicationSettings** (existing)

**Excluded Accounts (will maintain Control Tower defaults):**
- Management Account: `891377069955`
- Log Archive Account: `058264522153`
- Audit Account: `211125586359`

## How It Works

1. **Producer Lambda** monitors Control Tower events and triggers when:
   - New accounts are created
   - Existing accounts are updated
   - Landing Zone is updated

2. **Consumer Lambda** updates AWS Config recorders in managed accounts to:
   - Exclude specified resource types from recording
   - Maintain other Control Tower baseline settings
   - Apply daily recording frequency for specific resource types

3. **Accounts are automatically excluded**:
   - Management Account (`891377069955`)
   - Log Archive Account (`058264522153`)
   - Audit Account (`211125586359`)

## Troubleshooting

### Check Lambda Logs
```bash
# Get function names from CloudFormation
aws cloudformation describe-stack-resources \
  --stack-name ControlTowerConfigCustomization \
  --region us-east-2 \
  --profile org-admin \
  --query 'StackResources[?starts_with(LogicalResourceId, `Producer`) || starts_with(LogicalResourceId, `Consumer`)][LogicalResourceId, PhysicalResourceId]' \
  --output table

# View logs (replace FUNCTION_NAME)
aws logs tail /aws/lambda/FUNCTION_NAME --follow --region us-east-2 --profile org-admin
```

### Verify Config Recorder Settings
In a managed account (after assuming appropriate role):
```bash
aws configservice describe-configuration-recorders --region us-east-2

# Check for exclusion settings
aws configservice describe-configuration-recorders \
  --region us-east-2 \
  --query 'ConfigurationRecorders[0].recordingGroup.exclusionByResourceTypes.resourceTypes'
```

### Manual Verification in AWS Console
1. Go to AWS Config in a managed account
2. Click 'Settings' in the left menu
3. Check 'Recording' tab
4. Verify `AWS::EC2::EC2Fleet` and `AWS::EC2::SpotFleet` are in exclusion list

## Important Notes

⚠️ **Deploy from Management Account**: This solution must be deployed from your AWS Control Tower management account (`891377069955`).

⚠️ **Region**: Deploy in your Control Tower home region (`us-east-2`).

⚠️ **AWS Profile**: Use the `org-admin` profile for authentication.

⚠️ **Propagation Time**: Changes may take 5-10 minutes to propagate to all managed accounts.

⚠️ **Existing Resources**: This only affects future Config recording. Existing Config data is not deleted.

## Rollback

To restore Control Tower default Config settings:

```bash
# Option 1: Delete the stack (Recommended)
aws cloudformation delete-stack \
  --stack-name ControlTowerConfigCustomization \
  --region us-east-2 \
  --profile org-admin

# Option 2: Update template to remove EC2 Fleet exclusions
# Edit template.yaml and change ConfigRecorderExcludedResourceTypes default to:
# "AWS::HealthLake::FHIRDatastore,AWS::Pinpoint::Segment,AWS::Pinpoint::ApplicationSettings"
# Then redeploy with: AWS_PROFILE=org-admin python3 deploy.py
```

## Support

For issues:
1. Check CloudFormation stack events in the AWS Console
2. Review Lambda function logs using the commands above
3. Verify IAM permissions for Control Tower execution role
4. Ensure you're deploying from the management account (`891377069955`)

## Files in This Solution

- [`template.yaml`](template.yaml) - CloudFormation template (updated with EC2 Fleet exclusions)
- [`deploy.py`](deploy.py) - Python deployment script (pre-configured for your environment)
- [`verify.py`](verify.py) - Comprehensive verification script
- [`ct_configrecorder_override_producer.py`](ct_configrecorder_override_producer.py) - Producer Lambda function
- [`ct_configrecorder_override_consumer.py`](ct_configrecorder_override_consumer.py) - Consumer Lambda function

## References

- [Original AWS Blog Post](https://aws.amazon.com/blogs/mt/customize-aws-config-resource-tracking-in-aws-control-tower-environment/)
- [AWS Config Supported Resource Types](https://docs.aws.amazon.com/config/latest/developerguide/resource-config-reference.html)
- [AWS Control Tower User Guide](https://docs.aws.amazon.com/controltower/latest/userguide/)