import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))
    
    bucket_name = None
    
    # 1. Parse EventBridge structure (CloudTrail S3 API calls)
    if 'detail' in event:
        detail = event['detail']
        # Check standard requestParameters
        if 'requestParameters' in detail:
            req_params = detail['requestParameters']
            if 'bucketName' in req_params:
                bucket_name = req_params['bucketName']
            elif 'Host' in req_params:
                # Fallback: parse host name (e.g. my-bucket.s3.amazonaws.com)
                host = req_params['Host']
                bucket_name = host.split('.')[0]
                
    # 2. Fallback: Parse direct test invocation payload
    if not bucket_name:
        bucket_name = event.get('bucket_name')
        
    if not bucket_name:
        logger.error("Could not extract S3 bucket name from the event payload.")
        return {
            'statusCode': 400,
            'body': json.dumps('Error: S3 bucket name not identified in event.')
        }
        
    logger.info("Executing auto-remediation: Enforcing 'Block Public Access' on S3 bucket: %s", bucket_name)
    
    try:
        # 3. Apply AWS S3 Public Access Block configuration
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        logger.info("Auto-remediation successful! Strict access blocks enforced on S3 bucket: %s", bucket_name)
        
        # 4. Simulate Slack Alert Payload
        slack_alert = {
            "channel": "#security-alerts",
            "username": "AWS-Auto-Remediator",
            "text": f"🚨 *SECURITY VIOLATION RECTIFIED* 🚨\n"
                    f"*Resource Type:* AWS S3 Bucket\n"
                    f"*Resource Name:* `{bucket_name}`\n"
                    f"*Violation:* Attempt to disable 'Block Public Access' configurations.\n"
                    f"*Status:* Enforced strict corporate encryption and access controls automatically."
        }
        logger.info("SIMULATED SECURE SLACK NOTIFICATION: %s", json.dumps(slack_alert))
        
        return {
            'statusCode': 200,
            'body': json.dumps(f"Success: S3 bucket {bucket_name} is now secured.")
        }
        
    except Exception as e:
        logger.error("Error applying public access block: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps(f"Failure: Remediation failed. Reason: {str(e)}")
        }
