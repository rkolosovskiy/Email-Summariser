"""
Gmail Client Module
Handles fetching and processing emails from Gmail
"""

import base64
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
import html2text


class GmailClient:
    """Client for fetching and processing Gmail messages"""

    def __init__(self, service):
        """
        Initialize the Gmail client

        Args:
            service: Authenticated Gmail API service object
        """
        self.service = service
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True

    def get_label_id(self, label_name):
        """
        Get the label ID for a given label name

        Args:
            label_name: Name of the Gmail label

        Returns:
            Label ID or None if not found
        """
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])

            for label in labels:
                if label['name'].lower() == label_name.lower():
                    return label['id']

            print(f"Warning: Label '{label_name}' not found. Available labels:")
            for label in labels:
                print(f"  - {label['name']}")
            return None

        except Exception as e:
            print(f"Error fetching labels: {e}")
            return None

    def fetch_emails(self, label_name='INBOX', max_results=50):
        """
        Fetch emails from a specific label

        Args:
            label_name: Name of the Gmail label to fetch from
            max_results: Maximum number of emails to fetch

        Returns:
            List of email dictionaries with metadata and content
        """
        emails = []

        try:
            # Get label ID
            label_id = self.get_label_id(label_name)
            if not label_id:
                # If label not found, try using it as-is (might be a system label)
                label_id = label_name

            print(f"Fetching emails from label: {label_name}...")

            # Fetch message IDs
            results = self.service.users().messages().list(
                userId='me',
                labelIds=[label_id],
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                print(f"No messages found in label '{label_name}'")
                return emails

            print(f"Found {len(messages)} messages. Fetching details...")

            # Fetch full message details
            for i, message in enumerate(messages, 1):
                try:
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()

                    email_data = self._parse_message(msg)
                    emails.append(email_data)

                    if i % 10 == 0:
                        print(f"  Processed {i}/{len(messages)} emails...")

                except Exception as e:
                    print(f"  Error fetching message {message['id']}: {e}")
                    continue

            print(f"Successfully fetched {len(emails)} emails")
            return emails

        except Exception as e:
            print(f"Error fetching emails: {e}")
            return emails

    def _parse_message(self, message):
        """
        Parse a Gmail message into a structured format

        Args:
            message: Gmail API message object

        Returns:
            Dictionary with email metadata and content
        """
        headers = message['payload']['headers']

        # Extract headers
        subject = self._get_header(headers, 'Subject')
        sender = self._get_header(headers, 'From')
        date = self._get_header(headers, 'Date')

        # Parse date
        try:
            parsed_date = parsedate_to_datetime(date)
            date_str = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        except:
            date_str = date

        # Extract body
        body = self._get_message_body(message['payload'])

        return {
            'id': message['id'],
            'subject': subject,
            'from': sender,
            'date': date_str,
            'body': body,
            'snippet': message.get('snippet', '')
        }

    def _get_header(self, headers, name):
        """Get a specific header value from email headers"""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ''

    def _get_message_body(self, payload):
        """
        Extract the message body from the payload
        Handles both plain text and HTML emails
        """
        body = ''

        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
                        break
                elif part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        html = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
                        body = self.html_converter.handle(html)
                elif 'parts' in part:
                    # Nested parts
                    body = self._get_message_body(part)
                    if body:
                        break
        else:
            # Single part message
            if 'data' in payload.get('body', {}):
                if payload['mimeType'] == 'text/html':
                    html = base64.urlsafe_b64decode(
                        payload['body']['data']
                    ).decode('utf-8', errors='ignore')
                    body = self.html_converter.handle(html)
                else:
                    body = base64.urlsafe_b64decode(
                        payload['body']['data']
                    ).decode('utf-8', errors='ignore')

        return body.strip()
