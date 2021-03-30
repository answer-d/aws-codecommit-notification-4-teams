import json
import pymsteams
import os
import boto3


def lambda_handler(event, context):
    print(json.dumps(event))
    event_message = json.loads(event['Records'][0]['Sns']['Message'])
    ccard_info = {
        'url': os.environ['HOOK_URL']
    }
    print(json.dumps(event_message))

    detail_type = event_message["detailType"]
    # pr event
    if detail_type == "CodeCommit Pull Request State Change":
        ccard_info.update(generate_ccard_info_pr(event_message))
    # branch/tag event
    elif detail_type == "CodeCommit Repository State Change":
        ccard_info.update(generate_ccard_info_branch_and_tag(event_message))
    # comment event
    elif detail_type == "CodeCommit Comment on Commit" or \
            detail_type == "CodeCommit Comment on Pull Request":
        ccard_info.update(generate_ccard_info_comment(event_message))

    codecommit_arn = event_message["resources"][0]

    color = get_codecommit_tag(
        codecommit_arn, "Notification4TeamsColorCode")
    if color:
        ccard_info['color'] = color

    image_url = get_codecommit_tag(
        codecommit_arn, "Notification4TeamsImageUrl")
    if image_url:
        ccard_info['activity_image'] = image_url

    print(ccard_info)
    ccard = create_ccard(**ccard_info)
    ccard.send()

    ret = {
        "status_code": ccard.last_http_status.status_code,
        "payload": ccard.payload,
    }
    print(ret)

    return ret


def create_ccard(url, title, repository_name, **kwargs):
    ccard = pymsteams.connectorcard(url)

    # 発生したイベントを入れる(PR作成、ブランチ更新など)
    ccard.title(title)

    # イベントに対する補足情報があれば入れる
    # (PRクローズ時「マージしてないよ」などの注意喚起)
    if "text" in kwargs:
        ccard.text(kwargs.get("text"))

    # サマリは通知に出る
    if "summary" in kwargs:
        ccard.summary(kwargs.get("summary"))

    # カードの色指定
    if "color" in kwargs:
        ccard.color(kwargs.get("color"))

    section_info = pymsteams.cardsection()

    # リポジトリ名
    section_info.activityTitle(repository_name)

    # カード内に表示する画像
    # png/jpeg/gif(非アニメーション)、上限1024*1024
    if "activity_image" in kwargs:
        section_info.activityImage(kwargs.get("activity_image"))

    # PRタイトルなど
    if "section_info_title" in kwargs:
        section_info.activitySubtitle(kwargs.get("section_info_title"))

    # PRの備考などの補足情報(強調しなくて良いやつ)
    if "description" in kwargs:
        section_info.activityText(kwargs.get("description"))

    # PR作成者、PRリクエスト詳細などの補足情報(割と強調したいやつ)
    if "facts" in kwargs:
        for key, value in kwargs.get("facts").items():
            section_info.addFact(key, value)

    ccard.addSection(section_info)

    # PRやコミットへのリンク
    if "link_button_url" in kwargs:
        ccard.addLinkButton(
            kwargs.get("link_button_text"),
            kwargs.get("link_button_url")
        )

    return ccard


def generate_ccard_info_pr(event_message) -> dict:
    ret = {}
    detail = event_message["detail"]

    pr_id = detail["pullRequestId"]
    source_branch_name = detail["sourceReference"].split("/")[-1]
    dest_branch_name = detail["destinationReference"].split("/")[-1]
    notification_body = detail["notificationBody"]
    pr_url = notification_body[notification_body.rfind("https://"):-1]
    author_name = detail["author"].split(":")[-1]

    # common
    ret['repository_name'] = detail["repositoryNames"][0]
    ret['section_info_title'] = detail["title"]
    if "description" in detail.keys():
        ret['description'] = detail["description"]
    ret['facts'] = {
        "作成者": author_name,
        "ブランチ": f"{source_branch_name} -> {dest_branch_name}",
    }
    ret['link_button_text'] = f"Jump to Pull Request {pr_id}"
    ret['link_button_url'] = pr_url

    caller_username = detail["callerUserArn"].split(":")[-1]
    if detail["event"] == "pullRequestCreated":
        ret['title'] = "PRが作成されました！"
        ret['summary'] = \
            f"{ret['repository_name']}: PR作成 \"{ret['section_info_title']}\""
    elif detail["event"] == "pullRequestSourceBranchUpdated":
        ret['title'] = "PRが更新されました！"
        ret['summary'] = \
            f"{ret['repository_name']}: PR更新 \"{ret['section_info_title']}\""
        ret['facts'].update({
            "更新した人": caller_username
        })
    elif detail["event"] == "pullRequestStatusChanged" and \
            detail["isMerged"] == "False":
        ret['title'] = "PRがクローズされました！"
        ret['summary'] = \
            f"{ret['repository_name']}: PRクローズ " \
            f"\"{ret['section_info_title']}\" by {caller_username}"
        ret['text'] = "マージしてないよ"
        ret['facts'].update({
            "クローズした人": caller_username
        })
    elif detail["event"] == "pullRequestMergeStatusUpdated" and \
            detail["isMerged"] == "True":
        ret['title'] = "PRがマージされました！"
        ret['summary'] = \
            f"{ret['repository_name']}: PRマージ " \
            f"\"{ret['section_info_title']}\" by {caller_username}"
        ret['text'] = "ご対応ありがとうございました！"

        commit_id = detail["destinationCommit"]
        ret['facts'].update({
            "マージした人": caller_username,
            "コミットID": commit_id,
        })
    elif detail["event"] == "pullRequestApprovalStateChanged" and \
            detail["approvalStatus"] == "APPROVE":
        ret['title'] = "PRが承認されました！"
        ret['summary'] = \
            f"{ret['repository_name']}: PR承認 " \
            f"\"{ret['section_info_title']}\" by {caller_username}"
        ret['text'] = "LGTM！"

        ret['facts'].update({
            "承認した人": caller_username,
        })
    elif detail["event"] == "pullRequestApprovalRuleOverridden":
        ret['title'] = "PRが強制的に承認されました！"
        ret['summary'] = \
            f"{ret['repository_name']}: PR承認(強制) " \
            f"\"{ret['section_info_title']}\" by {caller_username}"

        ret['facts'].update({
            "強制承認した人": caller_username,
        })
    else:
        raise Exception(
            f"Cannot detect event type({detail['event']})\n"
            f"event_message: {event_message}"
        )

    return ret


def generate_ccard_info_branch_and_tag(event_message) -> dict:
    ret = {}
    detail = event_message["detail"]

    # common
    ret['repository_name'] = detail["repositoryName"]
    ret['section_info_title'] = detail["referenceName"]

    caller_username = detail["callerUserArn"].split(":")[-1]
    if detail['referenceType'] == 'branch' and \
            detail['event'] == 'referenceCreated':
        ret['title'] = "ブランチが作成されました！"
        ret['summary'] = \
            f"{ret['repository_name']}: ブランチ作成 \"{ret['section_info_title']}\""
        ret['facts'] = {'作成者': caller_username}
    elif detail['referenceType'] == 'branch' and \
            detail['event'] == 'referenceDeleted':
        ret['title'] = "ブランチが削除されました！"
        ret['summary'] = \
            f"{ret['repository_name']}: ブランチ削除 \"{ret['section_info_title']}\""
        ret['facts'] = {'削除した人': caller_username}
    elif detail['referenceType'] == 'branch' and \
            detail['event'] == 'referenceUpdated':
        ret['title'] = "ブランチが更新されました！"
        ret['summary'] = \
            f"{ret['repository_name']}: ブランチ更新 \"{ret['section_info_title']}\""
        ret['facts'] = {'更新した人': caller_username}
    elif detail['referenceType'] == 'tag' and \
            detail['event'] == 'referenceCreated':
        ret['title'] = "タグが作成されました！"
        ret['summary'] = \
            f"{ret['repository_name']}: タグ作成 \"{ret['section_info_title']}\""
        ret['facts'] = {'作成者': caller_username}
    elif detail['referenceType'] == 'tag' and \
            detail['event'] == 'referenceDeleted':
        ret['title'] = "タグが削除されました！"
        ret['summary'] = \
            f"{ret['repository_name']}: タグ削除 \"{ret['section_info_title']}\""
        ret['facts'] = {'削除した人': caller_username}
    else:
        raise Exception(
            f"Cannot detect event type({detail['event']})\n"
            f"event_message: {event_message}"
        )

    return ret


def generate_ccard_info_comment(event_message) -> dict:
    ret = {}
    detail = event_message["detail"]

    # common
    ret['repository_name'] = detail["repositoryName"]

    commenter_username = detail["callerUserArn"].split(":")[-1]
    ret['facts'] = {
        'コメントした人': commenter_username,
    }

    notification_body = detail["notificationBody"]
    comment_url = notification_body[notification_body.rfind("https://"):]
    ret['link_button_text'] = 'View Comment'
    ret['link_button_url'] = comment_url
    ret['summary'] = \
        f"{ret['repository_name']}: コメント by {commenter_username}"

    if detail['event'] == "commentOnPullRequestCreated":
        ret['title'] = 'PRにコメントが付きました！'
    elif detail['event'] == "commentOnCommitCreated":
        ret['title'] = 'コメントが付きました！'

    return ret


def get_codecommit_tag(repository_arn, key) -> str:
    client = boto3.client("codecommit")

    tags = client.list_tags_for_resource(resourceArn=repository_arn)["tags"]

    if key in tags:
        return tags[key]
    else:
        return None
