#!/usr/bin/env python3
"""
Gmail AI Summarizer
Main application for fetching Gmail emails and generating AI summaries
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

from gmail_auth import GmailAuthenticator
from gmail_client import GmailClient
from ai_summarizer import AISummarizer


def load_config():
    """Load configuration from environment variables"""
    load_dotenv()

    config = {
        'credentials_path': os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'gmail_label': os.getenv('GMAIL_LABEL', 'INBOX'),
        'max_emails': int(os.getenv('MAX_EMAILS', '100')),
        'focus_topic': os.getenv('FOCUS_TOPIC', 'AI')
    }

    # Validate required config
    if not config['gemini_api_key']:
        print("Error: GEMINI_API_KEY not found in environment variables")
        print("Please set it in your .env file or export it")
        sys.exit(1)

    return config


def save_summary(summary, output_file=None):
    """
    Save summary to file

    Args:
        summary: Summary text
        output_file: Output file path (optional)
    """
    if not output_file:
        # Create summaries directory if it doesn't exist
        os.makedirs('summaries', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'summaries/gmail_summary_{timestamp}.md'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(f"\n✓ Summary saved to: {output_file}")
    return output_file


def print_separator():
    """Print a visual separator"""
    print("\n" + "=" * 80 + "\n")


def main():
    """Main application entry point"""
    # Load configuration
    config = load_config()

    parser = argparse.ArgumentParser(
        description='Gmail AI Summarizer - Analyze and summarize emails using AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Use default settings from .env
  %(prog)s --label "AI-News"         # Summarize emails from AI-News label
  %(prog)s --topic "Machine Learning" --max 100
  %(prog)s --after-date 2024/01/01 --before-date 2024/12/31  # Date range
  %(prog)s --quick                   # Generate quick insights only
  %(prog)s --output my_summary.md    # Save to specific file
        """
    )

    parser.add_argument(
        '--label',
        help='Gmail label to fetch emails from (default: from .env or INBOX)',
        default=config['gmail_label']
    )

    parser.add_argument(
        '--topic',
        help='Topic to focus the summary on (default: from .env or AI)',
        default=config['focus_topic']
    )

    parser.add_argument(
        '--max',
        type=int,
        help='Maximum number of emails to process (default: from .env or 50)',
        default=config['max_emails']
    )

    parser.add_argument(
        '--after-date',
        help='Start date for email search in YYYY-MM-DD or YYYY/MM/DD format (inclusive)',
        default=None
    )

    parser.add_argument(
        '--before-date',
        help='End date for email search in YYYY-MM-DD or YYYY/MM/DD format (inclusive)',
        default=None
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Generate quick insights instead of detailed summary'
    )

    parser.add_argument(
        '--output',
        help='Output file path for the summary',
        default=None
    )

    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save summary to file, only print to console'
    )

    parser.add_argument(
        '--list-labels',
        action='store_true',
        help='List all available Gmail labels and exit'
    )

    args = parser.parse_args()

    print("Gmail AI Summarizer")
    print_separator()
    print("Loading configuration...")
    # Config already loaded at start


    # Override config with command-line arguments
    if args.label:
        config['gmail_label'] = args.label
    if args.max:
        config['max_emails'] = args.max

    # Authenticate with Gmail
    print("Authenticating with Gmail...")
    try:
        authenticator = GmailAuthenticator(
            credentials_path=config['credentials_path']
        )
        gmail_service = authenticator.get_gmail_service()
        print("✓ Gmail authentication successful")
    except Exception as e:
        print(f"✗ Gmail authentication failed: {e}")
        sys.exit(1)

    # Create Gmail client
    gmail_client = GmailClient(gmail_service)

    # List labels if requested
    if args.list_labels:
        print_separator()
        print("Available Gmail labels:")
        try:
            results = gmail_service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            for label in sorted(labels, key=lambda x: x['name']):
                print(f"  - {label['name']}")
        except Exception as e:
            print(f"Error fetching labels: {e}")
        sys.exit(0)

    # Fetch emails
    print_separator()
    print(f"Fetching emails from label: {config['gmail_label']}")
    print(f"Maximum emails to process: {config['max_emails']}")
    if args.after_date:
        print(f"From date: {args.after_date}")
    if args.before_date:
        print(f"To date: {args.before_date}")

    try:
        emails = gmail_client.fetch_emails(
            label_name=config['gmail_label'],
            max_results=config['max_emails'],
            after_date=args.after_date,
            before_date=args.before_date
        )
    except Exception as e:
        print(f"✗ Error fetching emails: {e}")
        sys.exit(1)

    if not emails:
        print("No emails found. Exiting.")
        sys.exit(0)

    print(f"✓ Successfully fetched {len(emails)} emails")

    # Initialize AI summarizer
    print_separator()
    summarizer = AISummarizer(config['gemini_api_key'])

    # Generate summary
    try:
        if args.quick:
            summary_text = summarizer.generate_quick_insights(
                emails,
                focus_topic=args.topic
            )
            summary_title = f"# Quick Insights: {args.topic} Industry Updates\n\n"
        else:
            summary_text = summarizer.summarize_emails(
                emails,
                focus_topic=args.topic
            )
            summary_title = f"# {args.topic} Industry Email Summary\n\n"
            summary_title += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            summary_title += f"**Emails Analyzed:** {len(emails)}\n\n"
            summary_title += f"**Source Label:** {config['gmail_label']}\n\n"
            summary_title += "---\n\n"

        full_summary = summary_title + summary_text

        # Display summary
        print_separator()
        print("SUMMARY")
        print_separator()
        print(full_summary)

        # Save summary
        if not args.no_save:
            print_separator()
            save_summary(full_summary, args.output)

        print_separator()
        print("✓ Complete!")

    except Exception as e:
        print(f"✗ Error generating summary: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
