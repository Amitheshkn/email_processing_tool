import base64
import sys
from datetime import datetime
from typing import Any

from googleapiclient.discovery import Resource

from database import DatabaseService
from gmail_utils import authenticate_gmail


class EmailFetcher:
    def __init__(self,
                 gmail_service: Resource) -> None:
        self.service = gmail_service

    def extract_message_body(self,
                             msg: dict[str, Any]) -> str:
        if "parts" in msg["payload"]:
            for part in msg["payload"]["parts"]:
                if part.get("mimeType", "") == "text/plain":
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

        return ""

    def convert_internal_date(self,
                              internal_date: float) -> datetime:
        epoch_time_in_seconds = internal_date / 1000.0
        date_time_in_utc = datetime.utcfromtimestamp(epoch_time_in_seconds)
        return date_time_in_utc

    def extract_native_details(self,
                               msg: dict[str, Any],
                               field_name: str) -> str:
        headers = msg["payload"]["headers"]
        return next((header["value"] for header in headers if header["name"] == field_name), "")

    def fetch_emails(self) -> list[dict[str, Any]]:
        results = self.service.users().messages().list(userId="me", maxResults=300).execute()
        messages = results.get("messages", [])

        if not messages:
            print("No messages found in Email Service")
            return []

        else:
            print("Fetch Emails Started....")

        emails = []
        for message in messages:
            msg = self.service.users().messages().get(userId="me", id=message["id"]).execute()

            emails.append({
                "id": message["id"],
                "subject": self.extract_native_details(msg, "Subject"),
                "from_address": self.extract_native_details(msg, "From"),
                "message_body": self.extract_message_body(msg),
                "date_received": self.convert_internal_date(int(msg["internalDate"]))
            })
        print(f"Fetched - {len(emails)} email-s")
        return emails


def main():
    try:
        gmail_service = authenticate_gmail()
        email_fetcher = EmailFetcher(gmail_service)
        emails = email_fetcher.fetch_emails()
        if emails:
            db_service = DatabaseService()
            db_service.add_emails(emails)

    except Exception as e:
        print(f"Error - {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
