import configparser
import json
import re
import sys
from datetime import datetime, timedelta
from typing import Any, Type, Union

from database import DatabaseService, Email
from gmail_utils import authenticate_gmail

config = configparser.ConfigParser()
config.read("config.ini")
default_config = config["DEFAULT"]


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
                "addLabelIds": [action.get("labelId", "")],
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
                 gmail_service: GmailService) -> None:
        self.db_service = db_service
        self.gmail_service = gmail_service

    @staticmethod
    def validate_payload(payload: dict[str, Any]) -> Union[str, None]:
        if "rules" not in payload:
            return "Invalid payload: Missing 'rules' key"

        for rule in payload["rules"]:
            if "overallPredicate" not in rule or not isinstance(rule["overallPredicate"], str):
                return "Invalid rule: Missing or invalid 'overallPredicate'"

            if rule["overallPredicate"].lower() not in ["all", "any"]:
                return "Invalid rule: 'overallPredicate' must be 'All' or 'Any'"

            if "conditions" not in rule or not isinstance(rule["conditions"], list):
                return "Invalid rule: Missing or invalid 'conditions'"

            for condition in rule["conditions"]:
                if "field" not in condition or "predicate" not in condition or "value" not in condition:
                    return "Invalid condition: Missing 'field', 'predicate', or 'value'"

            if "actions" not in rule or not isinstance(rule["actions"], list):
                return "Invalid rule: Missing or invalid 'actions'"

            for action in rule["actions"]:
                if "type" not in action:
                    return "Invalid action: Missing 'type'"

                if action["type"] in ["moveMessage", "addLabel"] and "labelId" not in action:
                    return f"Invalid action: Missing 'labelId' for {action['type']} action"

        return None

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


def fetch_json_content() -> dict:
    with open("rules.json", "r") as file:
        content = json.load(file)
        return content


def main():
    try:
        db_service = DatabaseService()
        gmail_service = GmailService()
        email_processor = EmailProcessor(db_service, gmail_service)

        json_content = fetch_json_content()
        if not json_content:
            raise Exception("JSON content not found")

        validation_error = EmailProcessor.validate_payload(json_content)
        if validation_error:
            raise Exception(f"JSON validation failed - {validation_error}")

        email_processor.process_emails(json_content["rules"])
        print("Email processing has been completed")

    except Exception as e:
        print(f"Error - {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
