import os
import json

from aws_codecommit_notification_4_teams import app


def test_branch_create():
    event = json.load(open(
        os.path.dirname(__file__) + "/../../events/branch_create.json", "r"))

    ret = app.lambda_handler(event, "")

    assert ret["status_code"] == 200


def test_branch_delete():
    event = json.load(open(
        os.path.dirname(__file__) + "/../../events/branch_delete.json", "r"))

    ret = app.lambda_handler(event, "")

    assert ret["status_code"] == 200


def test_pr_create():
    event = json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_create.json", "r"))

    ret = app.lambda_handler(event, "")

    assert ret["status_code"] == 200


def test_pr_update():
    event = json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_update.json", "r"))

    ret = app.lambda_handler(event, "")

    assert ret["status_code"] == 200


def test_pr_delete():
    event = json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_delete.json", "r"))

    ret = app.lambda_handler(event, "")

    assert ret["status_code"] == 200


def test_pr_merged():
    event = json.load(open(
        os.path.dirname(__file__) + "/../../events/pr_merged.json", "r"))

    ret = app.lambda_handler(event, "")

    assert ret["status_code"] == 200
