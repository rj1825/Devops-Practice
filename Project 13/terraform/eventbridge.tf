# EventBridge Event Rule capturing S3 public access modification events
resource "aws_cloudwatch_event_rule" "s3_access_change_rule" {
  name        = "s3-public-access-change-rule"
  description = "Triggered when S3 bucket public access blocks are modified or deleted"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail_type = ["AWS API Call via CloudTrail"]
    detail = {
      eventSource = ["s3.amazonaws.com"]
      eventName = [
        "PutBucketPublicAccessBlock",
        "DeleteBucketPublicAccessBlock"
      ]
    }
  })
}

# EventBridge Event Target pointing to the Auto-Remediator Lambda
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.s3_access_change_rule.name
  target_id = "TriggerAutoRemediatorLambda"
  arn       = aws_lambda_function.auto_remediator.arn
}

# Grant EventBridge permission to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auto_remediator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.s3_access_change_rule.arn
}
