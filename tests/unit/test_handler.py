import os
import json

import pytest

from aws_codecommit_notification_4_teams import app


@pytest.fixture(scope='module')
def pr_create_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_create.json", "r")
    )


@pytest.fixture(scope='module')
def pr_delete_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_delete.json", "r")
    )


@pytest.fixture(scope='module')
def pr_merged_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_merged.json", "r")
    )


@pytest.fixture(scope='module')
def pr_update_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_update.json", "r")
    )


@pytest.fixture(scope='module')
def pr_approval_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_approval.json", "r")
    )


@pytest.fixture(scope='module')
def pr_approval_override_event():
    return json.load(open(
        os.path.dirname(__file__) +
        "/../../events/pr_approval_override.json", "r")
    )


@pytest.fixture(scope='module')
def branch_create_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/branch_create.json", "r")
    )


@pytest.fixture(scope='module')
def branch_delete_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/branch_delete.json", "r")
    )


@pytest.fixture(scope='module')
def branch_update_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/branch_update.json", "r")
    )


@pytest.fixture(scope='module')
def tag_create_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/tag_create.json", "r")
    )


@pytest.fixture(scope='module')
def tag_delete_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/tag_delete.json", "r")
    )


def test_generate_ccard_info_pr_create(pr_create_event):
    ret = app.generate_ccard_info_pr(
        json.loads(pr_create_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'PRが作成されました！'
    assert ret['repository_name'] == 'sample-repo-ansible'
    assert ret['section_info_title'] == "\u3060\u3044\u305f\u3044\u5b9f\u88c5"
    assert ret['description'] == 'hogehoge'
    assert ret['facts']['作成者'] == 'user/someone'
    assert ret['facts']['ブランチ'] == 'feature-implement-almost -> master'
    assert ret['link_button_text'] == 'Jump to Pull Request 78'
    assert ret['link_button_url'] == 'https://ap-northeast-1.console.' \
        'aws.amazon.com/codesuite/codecommit/repositories/' \
        'sample-repo-ansible/pull-requests/78?region=ap-northeast-1'


def test_generate_ccard_info_pr_delete(pr_delete_event):
    ret = app.generate_ccard_info_pr(
        json.loads(pr_delete_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'PRがクローズされました！'
    assert ret['repository_name'] == 'sample-repo-ansible'
    assert ret['section_info_title'] == "\u3060\u3044\u305f\u3044\u5b9f\u88c5"
    assert ret['description'] == 'hogehoge'
    assert ret['facts']['作成者'] == 'user/someone'
    assert ret['facts']['ブランチ'] == 'feature-implement-almost -> master'
    assert ret['link_button_text'] == 'Jump to Pull Request 78'
    assert ret['link_button_url'] == 'https://ap-northeast-1.console.' \
        'aws.amazon.com/codesuite/codecommit/repositories/' \
        'sample-repo-ansible/pull-requests/78?region=ap-northeast-1'


def test_generate_ccard_info_pr_merged(pr_merged_event):
    ret = app.generate_ccard_info_pr(
        json.loads(pr_merged_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'PRがマージされました！'
    assert ret['text'] == 'ご対応ありがとうございました！'
    assert ret['repository_name'] == 'sample-repo-terraform'
    assert ret['section_info_title'] == "\u30c6\u30b9\u30c8\uff5e\uff5e\uff5e"
    assert 'description' not in ret.keys()
    assert ret['facts']['作成者'] == 'user/someone'
    assert ret['facts']['ブランチ'] == 'testtest -> master'
    assert ret['facts']['マージした人'] == 'user/someone'
    assert ret['facts']['コミットID'] == '01fb3163f4bcc8faa4f05c4'\
        '1852db52c21146a96'
    assert ret['link_button_text'] == 'Jump to Pull Request 80'
    assert ret['link_button_url'] == 'https://ap-northeast-1.console.' \
        'aws.amazon.com/codesuite/codecommit/repositories/' \
        'sample-repo-terraform/pull-requests/80?region=ap-northeast-1'


def test_generate_ccard_info_pr_update(pr_update_event):
    ret = app.generate_ccard_info_pr(
        json.loads(pr_update_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'PRが更新されました！'
    assert ret['repository_name'] == 'reponame'
    assert ret['section_info_title'] == "onakaita-i"
    assert 'description' not in ret.keys()
    assert ret['facts']['作成者'] == 'user/someone'
    assert ret['facts']['ブランチ'] == 'ponponpain -> master'
    assert ret['link_button_text'] == 'Jump to Pull Request 68'
    assert ret['link_button_url'] == 'https://ap-northeast-1.console' \
        '.aws.amazon.com/codesuite/codecommit/repositories/' \
        'reponame/pull-requests/68?region=ap-northeast-1'


def test_generate_ccard_info_pr_approve(pr_approval_event):
    ret = app.generate_ccard_info_pr(
        json.loads(pr_approval_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'PRが承認されました！'
    assert ret['repository_name'] == 'aws-codecommit-notification-4-teams-test'
    assert ret['section_info_title'] == 'prtest2'
    assert 'description' not in ret.keys()
    assert ret['facts']['承認した人'] == 'someone'
    assert ret['link_button_text'] == 'Jump to Pull Request 10'
    assert ret['link_button_url'] == 'https://ap-northeast-1.console' \
        '.aws.amazon.com/codesuite/codecommit/repositories/' \
        'aws-codecommit-notification-4-teams-test/' \
        'pull-requests/10?region=ap-northeast-1'


def test_generate_ccard_info_pr_approval_override(pr_approval_override_event):
    ret = app.generate_ccard_info_pr(
        json.loads(pr_approval_override_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'PRが強制的に承認されました！'
    assert ret['repository_name'] == 'aws-codecommit-notification-4-teams-test'
    assert ret['section_info_title'] == 'pr_test'
    assert ret['description'] == 'update'
    assert ret['facts']['強制承認した人'] == 'someone'
    assert ret['link_button_text'] == 'Jump to Pull Request 9'
    assert ret['link_button_url'] == 'https://ap-northeast-1.console' \
        '.aws.amazon.com/codesuite/codecommit/repositories/' \
        'aws-codecommit-notification-4-teams-test/' \
        'pull-requests/9?region=ap-northeast-1'


def test_generate_ccard_info_branch_create(branch_create_event):
    ret = app.generate_ccard_info_branch_and_tag(
        json.loads(branch_create_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'ブランチが作成されました！'
    assert ret['repository_name'] == 'sample-repo-ansible'
    assert ret['section_info_title'] == 'feature-implement-almost'
    assert 'description' not in ret.keys()
    assert ret['facts']['作成者'] == 'assumed-role/C9Role/i-01256440b4d783e3a'
    assert 'link_button_text' not in ret.keys()
    assert 'link_button_url' not in ret.keys()


def test_generate_ccard_info_branch_delete(branch_delete_event):
    ret = app.generate_ccard_info_branch_and_tag(
        json.loads(branch_delete_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'ブランチが削除されました！'
    assert ret['repository_name'] == 'sample-repo-ansible'
    assert ret['section_info_title'] == 'feature-implement-almost'
    assert 'description' not in ret.keys()
    assert ret['facts']['削除した人'] == 'user/someone'
    assert 'link_button_text' not in ret.keys()
    assert 'link_button_url' not in ret.keys()


def test_generate_ccard_info_branch_update(branch_update_event):
    ret = app.generate_ccard_info_branch_and_tag(
        json.loads(branch_update_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'ブランチが更新されました！'
    assert ret['repository_name'] == 'aws-codecommit-notification-4-teams-test'
    assert ret['section_info_title'] == 'main'
    assert 'description' not in ret.keys()
    assert ret['facts']['更新した人'] == 'user/someone'
    assert 'link_button_text' not in ret.keys()
    assert 'link_button_url' not in ret.keys()


def test_generate_ccard_info_tag_create(tag_create_event):
    ret = app.generate_ccard_info_branch_and_tag(
        json.loads(tag_create_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'タグが作成されました！'
    assert ret['repository_name'] == 'aws-codecommit-notification-4-teams-test'
    assert ret['section_info_title'] == 'tag-test'
    assert 'description' not in ret.keys()
    assert ret['facts']['作成者'] == 'user/someone'
    assert 'link_button_text' not in ret.keys()
    assert 'link_button_url' not in ret.keys()


def test_generate_ccard_info_tag_delete(tag_delete_event):
    ret = app.generate_ccard_info_branch_and_tag(
        json.loads(tag_delete_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'タグが削除されました！'
    assert ret['repository_name'] == 'aws-codecommit-notification-4-teams-test'
    assert ret['section_info_title'] == 'tag-test'
    assert 'description' not in ret.keys()
    assert ret['facts']['削除した人'] == 'user/someone'
    assert 'link_button_text' not in ret.keys()
    assert 'link_button_url' not in ret.keys()
