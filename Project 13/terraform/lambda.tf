# Archive the python Lambda script
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/remediator.py"
  output_path = "${path.module}/../lambda/remediator.zip"
}

# IAM Role for Lambda execution
resource "aws_iam_role" "lambda_exec_role" {
  name = "idp-auto-remediation-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for S3 remediation & CloudWatch Logging
resource "aws_iam_policy" "lambda_policy" {
  name        = "idp-auto-remediation-lambda-policy"
  description = "Allows Lambda to modify S3 public access settings and write CloudWatch logs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutBucketPublicAccessBlock",
          "s3:GetBucketPublicAccessBlock"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Bind IAM Policy to IAM Role
resource "aws_iam_role_policy_attachment" "lambda_policy_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# Provision Lambda Function
resource "aws_lambda_function" "auto_remediator" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "idp-s3-compliance-auto-remediator"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "remediator.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.10"
  timeout          = 15

  tags = {
    Environment = "Dev"
    Purpose     = "Security-Auto-Remediation"
  }
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.auto_remediator.function_name}"
  retention_in_days = 7
}

output "lambda_function_name" {
  value       = aws_lambda_function.auto_remediator.function_name
  description = "The name of the deployed auto-remediator Lambda function"
}
