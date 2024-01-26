import re
import sys
from datetime import datetime, timedelta
from typing import Any, Type

from flask import Flask, request, jsonify

from database import DatabaseService, Email
from read_emails import authenticate_gmail

app = Flask(__name__)


class GmailService:
    @staticmethod
    def get_body_data(action: dict[str, str]) -> dict[str, Any]:
        action_name = action["type"]
        action_types = {
            "markAsRead": {
                "removeLabelIds": ["UNREAD"]
            },
            "markAsUnread": {
                "addLabelIds": ["UNREAD"]
            },
            "addLabel": {
                "addLabelIds": [action.get("labelId", "")]
            },
            "addStar": {
                "addLabelIds": ["STARRED"]
            },
            "archive": {
                "removeLabelIds": ["INBOX"]
            },
            "moveMessage": {
                "addLabelIds": [action.get("folderId", "")],
                "removeLabelIds": ["INBOX"]
            }
        }
        return action_types.get(action_name)

    @staticmethod
    def apply_actions(email_id: str,
                      body: dict[str, Any]) -> None:
        service = authenticate_gmail()
        try:
            service.users().messages().modify(userId="me", id=email_id, body=body).execute()
        except Exception as e:
            print(f"Unable to perform action on email id - {email_id}")
            print(f"Error - {str(e)}")

    @staticmethod
    def perform_actions(email_id: str,
                        actions: list[dict[str, str]]) -> None:
        gmail_service = GmailService()
        for action in actions:
            body = gmail_service.get_body_data(action)
            if body:
                gmail_service.apply_actions(email_id, body)


class EmailProcessor:
    def __init__(self,
                 db_service: DatabaseService,
                 gmail_service: Type[GmailService]) -> None:
        self.db_service = db_service
        self.gmail_service = gmail_service

    def check_conditions(self,
                         email: Type[Email],
                         condition: dict[str, str]) -> bool:
        field = condition["field"].lower()
        predicate = condition["predicate"].lower()
        value = condition["value"]

        if not hasattr(email, field):
            return False

        email_value = getattr(email, field)

        if field in ["from_address", "subject", "message_body"]:
            if predicate == "contains":
                return value.lower() in email_value.lower()

            elif predicate == "does not contain":
                return value.lower() not in email_value.lower()

            elif predicate == "equals":
                return email_value.lower() == value.lower()

            elif predicate == "does not equal":
                return email_value.lower() != value.lower()

        elif field == "date_received":
            email_date = email_value.replace(tzinfo=None)
            match = re.match(r"(\d+)(\s+)?(days|months)", value, re.I)
            if match:
                num, _, unit = match.groups()
                num = int(num)

                if unit.lower() == "days":
                    compare_date = datetime.utcnow() - timedelta(days=num)
                elif unit.lower() == "months":
                    compare_date = datetime.utcnow() - timedelta(days=30 * num)

                if predicate == "less than":
                    return email_date > compare_date
                elif predicate == "greater than":
                    return email_date < compare_date

        return False

    def apply_rules(self,
                    email: Type[Email],
                    rule: dict[str, Any]) -> bool:
        conditions_met = [self.check_conditions(email, condition) for condition in rule["conditions"]]

        if rule["overallPredicate"].lower() == "all":
            return all(conditions_met)

        elif rule["overallPredicate"].lower() == "any":
            return any(conditions_met)

        else:
            return False

    def process_emails(self,
                       rules: list[dict[str, Any]]) -> None:
        emails = self.db_service.fetch_emails()
        for email in emails:
            for rule in rules:
                if self.apply_rules(email, rule):
                    self.gmail_service.perform_actions(email.id, rule["actions"])


@app.route("/process_emails", methods=["POST"])
def process_emails_endpoint():
    try:
        payload = request.json
        if "rules" not in payload:
            return jsonify({
                "error": "Invalid payload"
            }), 400

        db_service = DatabaseService()
        gmail_service = GmailService
        email_processor = EmailProcessor(db_service, gmail_service)
        email_processor.process_emails(payload["rules"])

        return jsonify({
            "message": "Email processing has been completed"
        })

    except Exception as e:
        print(f"Error - {str(e)}")


def main():
    try:
        app.run(debug=True, port=8000)
    except Exception as e:
        print(f"Error - {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
