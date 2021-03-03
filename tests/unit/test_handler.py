import os
import json

import pytest

from aws_codecommit_notification_4_teams import app


@pytest.fixture(scope='module')
def pr_create_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_create.json", "r"))


@pytest.fixture(scope='module')
def pr_delete_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_delete.json", "r"))


@pytest.fixture(scope='module')
def pr_merged_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_merged.json", "r"))


@pytest.fixture(scope='module')
def pr_update_event():
    return json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_update.json", "r"))


def test_generate_ccard_info_pr_create(pr_create_event):
    ret = app.generate_ccard_info_pr(
        json.loads(pr_create_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'PRが作成されました！'
    assert ret['repository_name'] == 'sample-repo-ansible'
    assert ret['section_info_title'] == "\u3060\u3044\u305f\u3044\u5b9f\u88c5"
    assert ret['description'] == 'hogehoge'
    assert ret['facts']['作成者'] == 'someone'
    assert ret['facts']['ブランチ'] == 'feature-implement-almost -> master'
    assert ret['link_button_text'] == 'Jump to Pull Request 78'
    assert ret['link_button_url'] == 'https://ap-northeast-1.console.'\
        'aws.amazon.com/codesuite/codecommit/repositories/'\
        'sample-repo-ansible/pull-requests/78?region=ap-northeast-1'


def test_generate_ccard_info_pr_delete(pr_delete_event):
    ret = app.generate_ccard_info_pr(
        json.loads(pr_delete_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'PRがクローズされました！'
    assert ret['repository_name'] == 'sample-repo-ansible'
    assert ret['section_info_title'] == "\u3060\u3044\u305f\u3044\u5b9f\u88c5"
    assert ret['description'] == 'hogehoge'
    assert ret['facts']['作成者'] == 'someone'
    assert ret['facts']['ブランチ'] == 'feature-implement-almost -> master'
    assert ret['link_button_text'] == 'Jump to Pull Request 78'
    assert ret['link_button_url'] == 'https://ap-northeast-1.console.'\
        'aws.amazon.com/codesuite/codecommit/repositories/'\
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
    assert ret['facts']['作成者'] == 'someone'
    assert ret['facts']['ブランチ'] == 'testtest -> master'
    assert ret['facts']['マージした人'] == 'someone'
    assert ret['facts']['コミットID'] == '01fb3163f4bcc8faa4f05c4'\
        '1852db52c21146a96'
    assert ret['link_button_text'] == 'Jump to Pull Request 80'
    assert ret['link_button_url'] == 'https://ap-northeast-1.console.'\
        'aws.amazon.com/codesuite/codecommit/repositories/'\
        'sample-repo-terraform/pull-requests/80?region=ap-northeast-1'


def test_generate_ccard_info_pr_update(pr_update_event):
    ret = app.generate_ccard_info_pr(
        json.loads(pr_update_event['Records'][0]['Sns']['Message'])
    )

    assert ret['title'] == 'PRが更新されました！'
    assert ret['repository_name'] == 'reponame'
    assert ret['section_info_title'] == "onakaita-i"
    assert 'description' not in ret.keys()
    assert ret['facts']['作成者'] == 'someone'
    assert ret['facts']['ブランチ'] == 'ponponpain -> master'
    assert ret['link_button_text'] == 'Jump to Pull Request 68'
    assert ret['link_button_url'] == 'https://ap-northeast-1.console'\
        '.aws.amazon.com/codesuite/codecommit/repositories/'\
        'reponame/pull-requests/68?region=ap-northeast-1'
