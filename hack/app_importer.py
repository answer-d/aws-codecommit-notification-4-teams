from aws_codecommit_notification_4_teams import app
import json

event_file = "events/pr_create.json"
event = json.load(open(event_file, "r"))

app.lambda_handler(event, "")
