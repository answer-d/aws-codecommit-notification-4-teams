#!/usr/local/bin/fish

set -e AWS_ACCESS_KEY_ID
set -e AWS_SECRET_ACCESS_KEY
set -e AWS_SESSION_TOKEN

set -x AWS_ACCESS_KEY_ID $AWS_DEPLOY_ACCESS_KEY_ID
set -x AWS_SECRET_ACCESS_KEY $AWS_DEPLOY_SECRET_ACCESS_KEY

set aws_sts_credentials (aws sts assume-role \
  --role-arn "$AWS_DEPLOY_IAM_ROLE_ARN" \
  --role-session-name "$AWS_DEPLOY_ROLE_SESSION_NAME" \
  --query "Credentials" \
  --output "json")

set -x AWS_ACCESS_KEY_ID (echo $aws_sts_credentials | jq -r '.AccessKeyId')
set -x AWS_SECRET_ACCESS_KEY (echo $aws_sts_credentials | jq -r '.SecretAccessKey')
set -x AWS_SESSION_TOKEN (echo $aws_sts_credentials | jq -r '.SessionToken')
