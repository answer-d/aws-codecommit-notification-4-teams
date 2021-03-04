import os
import uuid
import time
import datetime
from unittest import TestCase

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
                'Purpose': 'CI'
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
        シナリオ(発生イベント数=12)
        1. mainブランチにコミット
        2. コミットにコメント
        3. featureブランチ作成+コミット
        4. PR作成
        5. PRにコメント
        6. featureブランチ更新
           PR更新イベントが同時に発生する
        7. PR承認
        8. PRマージ+ブランチ削除
        9. タグ付け
        """

        dt_before = datetime.datetime.now()

        # 1. mainブランチにコミット
        commit_1 = self.client_codecommit.create_commit(
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
            afterCommitId=commit_1["commitId"],
            location={
                'filePath': commit_1['filesAdded'][0]['absolutePath'],
                'filePosition': 1,
                'relativeFileVersion': 'AFTER',
            },
            content="そうだね、SAMはいいね",
        )

        # todo: シナリオの実装

        # Lambda処理待ち(クソ実装です！！！！！)
        time.sleep(480)

        dt_after = datetime.datetime.now()

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

        # change this value when add/remove steps
        self.assertGreaterEqual(
            sum([x['Sum'] for x in statistics_invocation['Datapoints']]), 2.0,
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
