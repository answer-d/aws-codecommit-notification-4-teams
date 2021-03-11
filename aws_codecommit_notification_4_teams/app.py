import json
import pymsteams
import os


def lambda_handler(event, context):
    print(json.dumps(event))
    event_message = json.loads(event['Records'][0]['Sns']['Message'])
    ccard_info = {
        'url': os.environ['HOOK_URL']
    }
    print(json.dumps(event_message))

    # pr event
    if event_message["detailType"] == "CodeCommit Pull Request State Change":
        ccard_info.update(generate_ccard_info_pr(event_message))
    # branch/tag event
    elif event_message["detailType"] == "CodeCommit Repository State Change":
        ccard_info.update(generate_ccard_info_branch_and_tag(event_message))
    # comment on commit event
    elif event_message["detailType"] == "CodeCommit Comment on Commit":
        ccard_info.update(generate_ccard_info_comment_on_commit(event_message))
    # comment on pr event
    elif event_message["detailType"] == "CodeCommit Comment on Pull Request":
        ccard_info.update(generate_ccard_info_comment_on_pr(event_message))

    # todo: def set_color_by_reponame()
    if "ansible" in ccard_info['repository_name']:
        ccard_info['color'] = "#ff5750"
    elif "terraform" in ccard_info['repository_name']:
        ccard_info['color'] = "#623CE4"

    # todo: def set_image_by_reponame()
    if "ansible" in ccard_info['repository_name']:
        ccard_info['activity_image'] = "https://xxx"
    elif "terraform" in ccard_info['repository_name']:
        ccard_info['activity_image'] = "https://xxx"

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
    # textが無い場合はsummaryに何か文字を入れないとエラーになるので適当に入れとく
    if "text" in kwargs:
        ccard.text(kwargs.get("text"))
    else:
        ccard.summary("dummy")

    # TODO: 色付けの仕方(環境変数とか？)
    if "color" in kwargs:
        ccard.color(kwargs.get("color"))

    section_info = pymsteams.cardsection()

    # リポジトリ名
    section_info.activityTitle(repository_name)

    # カード内に表示する画像、サイズ制限あり(上限忘れた)
    # TODO: 画像の選び方(S3？)
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
    notificationBody = detail["notificationBody"]
    pr_url = notificationBody[notificationBody.rfind("https://"):-1]
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

    if detail["event"] == "pullRequestCreated":
        ret['title'] = "PRが作成されました！"
    elif detail["event"] == "pullRequestSourceBranchUpdated":
        ret['title'] = "PRが更新されました！"
    elif detail["event"] == "pullRequestStatusChanged" and \
            detail["isMerged"] == "False":
        ret['title'] = "PRがクローズされました！"
        ret['text'] = "マージしてないよ"
    elif detail["event"] == "pullRequestMergeStatusUpdated" and \
            detail["isMerged"] == "True":
        ret['title'] = "PRがマージされました！"
        ret['text'] = "ご対応ありがとうございました！"

        merge_username = detail["callerUserArn"].split(":")[-1]
        commit_id = detail["destinationCommit"]
        ret['facts'].update({
            "マージした人": merge_username,
            "コミットID": commit_id,
        })
    elif detail["event"] == "pullRequestApprovalStateChanged" and \
            detail["approvalStatus"] == "APPROVE":
        ret['title'] = "PRが承認されました！"
        ret['text'] = "LGTM！"

        approve_username = detail["callerUserArn"].split("/")[-1]
        ret['facts'].update({
            "承認した人": approve_username,
        })
    elif detail["event"] == "pullRequestApprovalRuleOverridden":
        ret['title'] = "PRが強制的に承認されました！"

        override_username = detail["callerUserArn"].split("/")[-1]
        ret['facts'].update({
            "強制承認した人": override_username,
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
        ret['facts'] = {'作成者': caller_username}
    elif detail['referenceType'] == 'branch' and \
            detail['event'] == 'referenceDeleted':
        ret['title'] = "ブランチが削除されました！"
        ret['facts'] = {'削除した人': caller_username}
    elif detail['referenceType'] == 'branch' and \
            detail['event'] == 'referenceUpdated':
        ret['title'] = "ブランチが更新されました！"
        ret['facts'] = {'更新した人': caller_username}
    elif detail['referenceType'] == 'tag' and \
            detail['event'] == 'referenceCreated':
        ret['title'] = "タグが作成されました！"
        ret['facts'] = {'作成者': caller_username}
    elif detail['referenceType'] == 'tag' and \
            detail['event'] == 'referenceDeleted':
        ret['title'] = "タグが削除されました！"
        ret['facts'] = {'削除した人': caller_username}
    else:
        raise Exception(
            f"Cannot detect event type({detail['event']})\n"
            f"event_message: {event_message}"
        )

    return ret


def generate_ccard_info_comment_on_commit(event_message) -> dict:
    ret = {}
    detail = event_message["detail"]

    # とりあえずjsonまんま出す
    ret['repository_name'] = detail["repositoryName"]
    ret['title'] = event_message["detailType"]
    ret['text'] = json.dumps(detail)

    # todo: comment_on_commit

    return ret


def generate_ccard_info_comment_on_pr(event_message) -> dict:
    ret = {}
    detail = event_message["detail"]

    # とりあえずjsonまんま出す
    ret['repository_name'] = detail["repositoryName"]
    ret['title'] = event_message["detailType"]
    ret['text'] = json.dumps(detail)

    # todo: comment_on_pr

    return ret
