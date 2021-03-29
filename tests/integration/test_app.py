import os
import uuid
import time
from unittest import TestCase
from datetime import datetime, timezone

import boto3

"""
Make sure env variable AWS_SAM_STACK_NAME exists with the
name of the stack we are going to test.
"""


class TestApp(TestCase):
    @classmethod
    def get_stack_name(cls) -> str:
        stack_name = os.environ.get("AWS_SAM_STACK_NAME")
        if not stack_name:
            raise Exception(
                "Cannot find env var AWS_SAM_STACK_NAME. \n"
                "Please setup this environment variable with"
                " the stack name where we are running integration tests."
            )

        return stack_name

    def setUp(self) -> None:
        """
        Based on the provided env variable AWS_SAM_STACK_NAME,
        CodeCommitリポジトリを作成し、
        cloudformationで作成されているSNSトピックを通知先とする通知ルールを作成する
        """
        stack_name = TestApp.get_stack_name()

        client_cfn = boto3.client("cloudformation")

        try:
            response = client_cfn.describe_stacks(StackName=stack_name)
        except Exception as e:
            raise Exception(
                f"Cannot find stack {stack_name}. \n"
                f'Please make sure stack with the name "{stack_name}" exists.'
            ) from e

        stacks = response["Stacks"]

        stack_outputs = stacks[0]["Outputs"]
        sns_topic_outputs = [
            output for output in stack_outputs if
            output["OutputKey"] == "SnsTopic"
        ]
        self.assertTrue(
            sns_topic_outputs,
            f"Cannot find output SnsTopic in stack {stack_name}"
        )

        sns_topic_arn = sns_topic_outputs[0]["OutputValue"]

        function_name_outputs = [
            output for output in stack_outputs if
            output["OutputKey"] == "FunctionName"
        ]
        self.assertTrue(
            function_name_outputs,
            f"Cannot find output FunctionName in stack {stack_name}"
        )

        self.function_name = function_name_outputs[0]["OutputValue"]

        self.client_codecommit = boto3.client("codecommit")

        self.repository_name = f"{stack_name}-ci-{str(uuid.uuid4())}"
        self.codecommit_repo = self.client_codecommit.create_repository(
            repositoryName=self.repository_name,
            tags={
                'Service': 'aws-codecommit-notification-4-teams',
                'Purpose': 'CI',
                'Notification4TeamsColorCode': "007627",
                "Notification4TeamsImageUrl":
                    "https://raw.githubusercontent.com/answer-d/"
                    "aws-codecommit-notification-4-teams/answer-d/"
                    "issue3/tests/integration/girigiri_neko.jpg",
            },
        )

        client_codestar_notifications = boto3.client("codestar-notifications")

        client_codestar_notifications.create_notification_rule(
            Name=self.repository_name[:64],
            EventTypeIds=[
                "codecommit-repository-comments-on-commits",
                "codecommit-repository-comments-on-pull-requests",
                "codecommit-repository-approvals-status-changed",
                "codecommit-repository-approvals-rule-override",
                "codecommit-repository-pull-request-created",
                "codecommit-repository-pull-request-source-updated",
                "codecommit-repository-pull-request-status-changed",
                "codecommit-repository-pull-request-merged",
                "codecommit-repository-branches-and-tags-created",
                "codecommit-repository-branches-and-tags-deleted",
                "codecommit-repository-branches-and-tags-updated",
            ],
            Resource=self.codecommit_repo['repositoryMetadata']['Arn'],
            Targets=[{
                'TargetType': 'SNS',
                'TargetAddress': sns_topic_arn,
            }],
            DetailType='FULL',
            Tags={
                'Service': 'aws-codecommit-notification-4-teams',
                'Purpose': 'CI',
            },
        )

    def tearDown(self):
        """
        CodeCommitリポジトリを削除する
        """
        self.client_codecommit.delete_repository(
            repositoryName=self.repository_name
        )

    def test_pr_accept_flow(self):
        """
        実際にCodeCommitに対して変更を行い、Lambdaが発火していることを確認する
        1.  mainブランチにコミット
        2.  コミットにコメント
        3.  featureブランチ作成
        5.  PR作成
        6.  PRにコメント
        7.  featureブランチ更新
            -> PR更新イベントが同時に発生する
        8.  PR承認
        9.  PR承認のオーバーライド
        10. PRマージ
            -> ブランチ更新イベントが同時に発生する
        11. ブランチ削除
        """

        dt_before = datetime.now(timezone.utc)

        # 1. mainブランチにコミット
        commit_main = self.client_codecommit.create_commit(
            repositoryName=self.repository_name,
            branchName='main',
            putFiles=[
                {
                    'filePath': 'README.md',
                    'fileContent': 'SAMはいいぞ',
                }
            ],
        )
        # 2. コミットにコメント
        self.client_codecommit.post_comment_for_compared_commit(
            repositoryName=self.repository_name,
            afterCommitId=commit_main["commitId"],
            location={
                'filePath': commit_main['filesAdded'][0]['absolutePath'],
                'filePosition': 1,
                'relativeFileVersion': 'AFTER',
            },
            content="そうだね、SAMはいいね",
        )
        # 3. featureブランチ作成
        feature_branch_name = 'feature/hogehoge'
        self.client_codecommit.create_branch(
            repositoryName=self.repository_name,
            branchName=feature_branch_name,
            commitId=commit_main["commitId"],
        )
        commit_feature = self.client_codecommit.create_commit(
            repositoryName=self.repository_name,
            branchName=feature_branch_name,
            parentCommitId=commit_main["commitId"],
            putFiles=[
                {
                    'filePath': 'test.txt',
                    'fileContent': '手作業はいいぞ',
                }
            ],
        )
        # 5. PR作成
        pr = self.client_codecommit.create_pull_request(
            title='add test.txt',
            targets=[
                {
                    'repositoryName': self.repository_name,
                    'sourceReference': feature_branch_name,
                    'destinationReference': 'main',
                }
            ]
        )
        # 6. PRにコメント
        self.client_codecommit.post_comment_for_pull_request(
            pullRequestId=pr["pullRequest"]["pullRequestId"],
            repositoryName=self.repository_name,
            beforeCommitId=pr["pullRequest"]["pullRequestTargets"][0]
            ["destinationCommit"],
            afterCommitId=pr["pullRequest"]["pullRequestTargets"][0]
            ["sourceCommit"],
            location={
                'filePath': commit_feature['filesAdded'][0]['absolutePath'],
                'filePosition': 1,
                'relativeFileVersion': 'AFTER',
            },
            content="いや、手作業は良くないね",
        )
        # 7. featureブランチ更新
        #    -> PR更新イベントが同時に発生する
        self.client_codecommit.create_commit(
            repositoryName=self.repository_name,
            branchName=feature_branch_name,
            parentCommitId=commit_feature["commitId"],
            putFiles=[
                {
                    'filePath': 'test.txt',
                    'fileContent': 'IaCはいいぞ',
                }
            ],
        )
        # 8. PR承認
        # 自身が作成したPRは承認できないためAssumeRoleして実施する
        client_sts = boto3.client('sts')
        role_arn = os.environ.get('ANOTHER_ROLE_ARN')
        region_name = os.environ.get('AWS_DEFAULT_REGION')
        sts_resp = client_sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"awscredswrap@it-{TestApp.get_stack_name()}"
        )
        session_pr_approve = boto3.Session(
            aws_access_key_id=sts_resp['Credentials']['AccessKeyId'],
            aws_secret_access_key=sts_resp['Credentials']['SecretAccessKey'],
            aws_session_token=sts_resp['Credentials']['SessionToken'],
            region_name=region_name,
        )

        # PRの最新リビジョンIDを拾うため情報取得
        pr_recent = self.client_codecommit.get_pull_request(
            pullRequestId=pr["pullRequest"]["pullRequestId"]
        )

        client_codecommit_assumed = session_pr_approve.client('codecommit')
        client_codecommit_assumed.update_pull_request_approval_state(
            pullRequestId=pr_recent["pullRequest"]["pullRequestId"],
            revisionId=pr_recent["pullRequest"]["revisionId"],
            approvalState="APPROVE",
        )
        # 9. PR承認のオーバーライド
        self.client_codecommit.override_pull_request_approval_rules(
            pullRequestId=pr_recent["pullRequest"]["pullRequestId"],
            revisionId=pr_recent["pullRequest"]["revisionId"],
            overrideStatus='OVERRIDE'
        )
        # 10. PRマージ
        #     -> ブランチ更新イベントが同時に発生する
        self.client_codecommit.merge_pull_request_by_three_way(
            pullRequestId=pr["pullRequest"]["pullRequestId"],
            repositoryName=self.repository_name,
        )
        # 11. ブランチ削除
        self.client_codecommit.delete_branch(
            repositoryName=self.repository_name,
            branchName=feature_branch_name,
        )

        # Lambda処理+CloudWatchメトリクス取得待ち (クソ実装 of the year受賞中)
        if not os.environ.get("AWS_SAM_SKIP_IT_WAIT"):
            print(f"{chr(int(0x2615))} coffee break...")
            time.sleep(10 * 60)
        else:
            time.sleep(30)

        dt_after = datetime.now(timezone.utc)

        print({
            "dt_before": dt_before,
            "dt_after": dt_after,
        })

        client_cloudwatch = boto3.client("cloudwatch")

        # Check Lambda Invocation
        statistics_invocation = client_cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[{
                'Name': 'FunctionName',
                'Value': self.function_name
            }],
            StartTime=dt_before,
            EndTime=dt_after,
            Period=60,
            Statistics=['Sum'],
        )

        print({"statistics_invocation": statistics_invocation})

        # ステップを追加したらここの数値を変更
        self.assertEqual(
            sum([x['Sum'] for x in statistics_invocation['Datapoints']]), 13.0,
            "Lambda function has not been invoked properly"
        )

        # Chack Lambda Error
        statistics_error = client_cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Errors',
            Dimensions=[{
                'Name': 'FunctionName',
                'Value': self.function_name
            }],
            StartTime=dt_before,
            EndTime=dt_after,
            Period=1,
            Statistics=['Sum'],
        )

        print({"statistics_error": statistics_error})

        self.assertEqual(
            sum([x['Sum'] for x in statistics_error['Datapoints']]), 0.0,
            "Error on invocated Lambda Function"
        )

    def test_pr_reject_flow(self):
        pass
