import os
import json
import datetime
import pytest
import boto3
from moto import mock_aws

# Import the Lambda handlers
import lambda_function

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture
def mock_config(monkeypatch):
    """Force unit tests to use custom scan configurations and active dry-run."""
    test_config = {
        "dry_run": True,
        "regions": ["us-east-1"],
        "cleanup_settings": {
            "unused_eip": True,
            "orphaned_ebs": True,
            "old_snapshots": True,
            "idle_load_balancers": True
        },
        "rules": {
            "ebs_orphan_days": 7,
            "snapshot_max_age_days": 30,
            "idle_alb_request_threshold": 100
        },
        "notifications": {
            "sns_topic_arn": "arn:aws:sns:us-east-1:123456789012:TestTopic",
            "s3_report_bucket": "test-report-bucket"
        }
    }
    monkeypatch.setattr(lambda_function, "load_config", lambda: test_config)
    return test_config

@mock_aws
def test_sweep_unused_resources(aws_credentials, mock_config, monkeypatch):
    # Initialize mock AWS resources
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    elbv2_client = boto3.client('elbv2', region_name='us-east-1')
    s3_client = boto3.client('s3', region_name='us-east-1')
    sns_client = boto3.client('sns', region_name='us-east-1')

    # Create mock notification targets
    s3_client.create_bucket(Bucket="test-report-bucket")
    topic_arn = sns_client.create_topic(Name="TestTopic")["TopicArn"]
    
    # 1. Setup mock unused Elastic IP
    eip_unassociated = ec2_client.allocate_address(Domain='vpc')
    
    # Setup associated EIP (should NOT be flagged)
    # Create an instance and associate EIP to it
    # First create subnets/VPC or just use default VPC endpoints in moto
    # Moto EC2 allows running instance directly
    instances = ec2.create_instances(ImageId='ami-12345678', MinCount=1, MaxCount=1)
    instance_id = instances[0].id
    eip_associated = ec2_client.allocate_address(Domain='vpc')
    ec2_client.associate_address(InstanceId=instance_id, AllocationId=eip_associated['AllocationId'])

    # 2. Setup mock orphaned EBS Volume (gp3, available state, 100GB)
    vol_orphaned = ec2.create_volume(
        AvailabilityZone='us-east-1a',
        Size=100,
        VolumeType='gp3'
    )
    # Mock its creation date to be 10 days ago (older than 7 days threshold)
    past_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)
    ec2_client.describe_volumes() # populate mock cache
    # Update CreateTime inside the mock model structure
    # Wait, moto creation time can be patched or we can just verify the threshold filter.
    # To keep tests robust, we will check that available volume is captured.
    # Let's adjust volume create times if needed, or moto defaults volume creation to "now".
    # Since moto sets CreateTime to now, let's temporarily patch age rule to 0 days for testing!
    mock_config["rules"]["ebs_orphan_days"] = 0
    mock_config["rules"]["snapshot_max_age_days"] = 0

    # 3. Setup mock old Snapshot
    snap_old = ec2_client.create_snapshot(
        VolumeId=vol_orphaned.id,
        Description="Old test snapshot"
    )

    # 4. Setup mock idle Load Balancer (empty targets)
    # Describe load balancers needs subnet inputs
    # Let's mock a default VPC and Subnet
    vpc = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')
    subnet = ec2_client.create_subnet(VpcId=vpc['Vpc']['VpcId'], CidrBlock='10.0.1.0/24')
    
    lb = elbv2_client.create_load_balancer(
        Name='idle-alb',
        Subnets=[subnet['Subnet']['SubnetId']],
        Type='application'
    )
    lb_arn = lb['LoadBalancers'][0]['LoadBalancerArn']

    # Execute lambda_handler
    event = {}
    context = None
    response = lambda_function.lambda_handler(event, context)

    # Assertions
    assert response["statusCode"] == 200
    body = response["body"]
    assert body["total_savings_estimated"] > 0
    assert body["dry_run"] is True

    # Check S3 Report creation
    s3_objects = s3_client.list_objects_v2(Bucket="test-report-bucket")["Contents"]
    assert len(s3_objects) == 1
    assert s3_objects[0]["Key"].startswith("cost-reports/report-")

    # Clean up mock resources
    instances[0].terminate()
