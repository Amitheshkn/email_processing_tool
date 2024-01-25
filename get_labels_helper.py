from googleapiclient.discovery import Resource

from gmail_utils import authenticate_gmail


def get_all_labels(service: Resource) -> None:
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(f"{label['name']} (ID: {label['id']})")


if __name__ == '__main__':
    gmail_service = authenticate_gmail()
    get_all_labels(gmail_service)
