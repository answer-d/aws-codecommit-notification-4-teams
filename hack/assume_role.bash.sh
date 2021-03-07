#!/bin/bash

unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN

export AWS_ACCESS_KEY_ID=${AWS_DEPLOY_ACCESS_KEY_ID}
export AWS_SECRET_ACCESS_KEY=${AWS_DEPLOY_SECRET_ACCESS_KEY}

aws_sts_credentials="$(aws sts assume-role \
  --role-arn "$AWS_DEPLOY_IAM_ROLE_ARN" \
  --role-session-name "$AWS_DEPLOY_ROLE_SESSION_NAME" \
  --query "Credentials" \
  --output "json")"

export AWS_ACCESS_KEY_ID="$(echo $aws_sts_credentials | jq -r '.AccessKeyId')"
export AWS_SECRET_ACCESS_KEY="$(echo $aws_sts_credentials | jq -r '.SecretAccessKey')"
export AWS_SESSION_TOKEN="$(echo $aws_sts_credentials | jq -r '.SessionToken')"
