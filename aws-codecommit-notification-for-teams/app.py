import json
import pymsteams
import os


def lambda_handler(event, context):
    url = os.environ['HOOK_URL']
    ccard = pymsteams.connectorcard(url)

    print({"url": url})
    print({"event": event})

    event_message = json.loads(event['Records'][0]['Sns']['Message'])

    print({"event_message": event_message})

    detail = event_message["detail"]

    # PR関連イベント
    if event_message["detailType"] == "CodeCommit Pull Request State Change":
        repository_name = detail["repositoryNames"][0]
        notificationBody = detail["notificationBody"]

        # リポジトリ名によって色変える
        if "ansible" in repository_name:
            ccard.color("#ff5750")
        elif "terraform" in repository_name:
            ccard.color("#623CE4")

        # PR作成
        if detail["event"] == "pullRequestCreated":
            ccard.title("PRが作成されました！")
            ccard.summary("dummy")
        # PR更新
        elif detail["event"] == "pullRequestSourceBranchUpdated":
            ccard.title("PRが更新されました！")
            ccard.summary("dummy")
        # PR削除
        elif detail["event"] == "pullRequestStatusChanged" and \
                detail["isMerged"] == "False":
            ccard.title("PRがクローズされました！")
            ccard.text("マージしてないよ")
        # PRマージ
        elif detail["event"] == "pullRequestMergeStatusUpdated" and \
                detail["isMerged"] == "True":
            ccard.title("PRがマージされました！")
            ccard.text("ご対応ありがとうございました！")
        # その他
        else:
            ccard.title("PRに何かしらの変更がありやす")
            ccard.text(json.dumps(detail))

        # 共通情報
        pr_id = detail["pullRequestId"]
        title = detail["title"]
        if "description" in detail.keys():
            description = detail["description"]
        source_branch_name = detail["sourceReference"].split("/")[-1]
        dest_branch_name = detail["destinationReference"].split("/")[-1]
        pr_url = notificationBody[notificationBody.rfind("https://"):-1]
        author_name = detail["author"].split("/")[-1]

        section_info = pymsteams.cardsection()
        section_info.activityTitle(repository_name)
        section_info.activitySubtitle(title)
        if "description" in locals():
            section_info.activityText(description)

        if "ansible" in repository_name:
            section_info.activityImage("https://xxx")
        elif "terraform" in repository_name:
            section_info.activityImage("https://xxx")

        section_info.addFact("作成者", author_name)
        section_info.addFact(
            "ブランチ", f"{source_branch_name} -> {dest_branch_name}")

        # PRマージ
        if detail["event"] == "pullRequestMergeStatusUpdated" and\
                detail["isMerged"] == "True":
            merge_username = detail["callerUserArn"].split("/")[-1]
            commit_id = detail["destinationCommit"]
            section_info.addFact("マージした人", merge_username)
            section_info.addFact("コミットID", commit_id)

        ccard.addSection(section_info)
        ccard.addLinkButton(f"Jump to Pull Request {pr_id}", pr_url)

    # その他のイベント
    else:
        repository_name = detail["repositoryName"]

        # リポジトリ名によって色変える
        if "ansible" in repository_name:
            ccard.color("#ff5750")
        elif "terraform" in repository_name:
            ccard.color("#623CE4")

        # とりあえずjsonまんま出す
        ccard.title(event_message["detailType"])
        ccard.text(json.dumps(detail))

    ccard.send()

    print({
        "message": event_message,
        "status_code": ccard.last_http_status.status_code,
    })

    return ccard.last_http_status.status_code


if __name__ == '__main__':
    # test pr create
    pr_create_event_json = json.load(open("fixture/pr_create.json", "r"))
    lambda_handler(pr_create_event_json, {})

    # test pr update
    pr_update_event_json = json.load(open("fixture/pr_update.json", "r"))
    lambda_handler(pr_update_event_json, {})

    # test pr delete
    pr_delete_event_json = json.load(open("fixture/pr_delete.json", "r"))
    lambda_handler(pr_delete_event_json, {})

    # test pr merged
    pr_merged_event_json = json.load(open("fixture/pr_merged.json", "r"))
    lambda_handler(pr_merged_event_json, {})

    # test branch create
    branch_create_event_json = json.load(
        open("fixture/branch_create.json", "r"))
    lambda_handler(branch_create_event_json, {})

    # test branch delete
    branch_delete_event_json = json.load(
        open("fixture/branch_delete.json", "r"))
    lambda_handler(branch_delete_event_json, {})
