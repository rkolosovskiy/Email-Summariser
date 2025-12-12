# Gmail AI Summarizer

An intelligent tool that connects to your Gmail account, fetches emails from specific labels, and generates comprehensive AI-powered summaries focused on topics like AI industry news, trends, and developments.

## Features

- **Gmail Integration**: Secure OAuth2 authentication with Gmail API
- **Label-Based Filtering**: Fetch emails from specific Gmail labels
- **AI-Powered Summarization**: Uses Claude AI (Anthropic) to generate detailed summaries
- **Topic-Focused Analysis**: Configurable focus on specific topics (default: AI industry)
- **Comprehensive Reports**: Includes key developments, trends, companies, technical insights, and action items
- **Multiple Output Modes**: Detailed summaries or quick insights
- **Flexible CLI**: Command-line interface with multiple options
- **Auto-Save**: Automatically saves summaries with timestamps

## Prerequisites

- Python 3.7 or higher
- Gmail account
- Google Cloud Project with Gmail API enabled
- Anthropic API key (for Claude AI)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Gmail
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client anthropic python-dotenv beautifulsoup4 html2text
```

### 3. Set Up Gmail API Credentials

#### a. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

#### b. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External (for personal use)
   - Add your email as a test user
   - Scopes: Just add the basic profile info
4. Choose "Desktop app" as the application type
5. Download the credentials JSON file
6. Save it as `credentials.json` in the project directory

### 4. Get Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (you'll need it in the next step)

### 5. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file and add your credentials:

```env
GMAIL_CREDENTIALS_PATH=credentials.json
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GMAIL_LABEL=AI-News
MAX_EMAILS=50
```

### 6. Create a Gmail Label (Optional)

1. Open Gmail
2. Create a label for AI-related emails (e.g., "AI-News")
3. Set up filters to automatically label incoming AI newsletters and emails
4. Update the `GMAIL_LABEL` in your `.env` file

## Usage

### Basic Usage

Run with default settings from `.env`:

```bash
python main.py
```

### Command-Line Options

```bash
# Fetch from a specific label
python main.py --label "AI-News"

# Focus on a different topic
python main.py --topic "Machine Learning"

# Process more emails
python main.py --max 100

# Generate quick insights instead of detailed summary
python main.py --quick

# Save to a specific file
python main.py --output my_summary.md

# Print only, don't save to file
python main.py --no-save

# List all available Gmail labels
python main.py --list-labels
```

### Combined Options

```bash
python main.py --label "Tech-News" --topic "Artificial Intelligence" --max 75 --output ai_weekly.md
```

## First-Time Authentication

When you run the tool for the first time:

1. A browser window will open automatically
2. Sign in to your Gmail account
3. Grant the requested permissions (read-only access to Gmail)
4. The authentication token will be saved locally as `token.pickle`
5. Future runs will use this saved token (no browser required)

## Output Format

The tool generates comprehensive markdown summaries including:

1. **Executive Summary**: High-level overview of main themes
2. **Key Developments**: Detailed breakdown by category
3. **Notable Companies & Projects**: Significant mentions
4. **Emerging Trends**: Industry patterns and themes
5. **Important Dates & Events**: Upcoming events and deadlines
6. **Action Items**: Calls-to-action and opportunities
7. **Technical Insights**: Technical details and innovations

Summaries are automatically saved to the `summaries/` directory with timestamps.

## Example Output

```
summaries/
├── gmail_summary_20231215_143022.md
├── gmail_summary_20231216_090145.md
└── gmail_summary_20231217_161203.md
```

## Project Structure

```
Gmail/
├── main.py                 # Main application entry point
├── gmail_auth.py          # Gmail OAuth2 authentication
├── gmail_client.py        # Email fetching and processing
├── ai_summarizer.py       # AI-powered summarization
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── credentials.json      # Gmail API credentials (you provide)
├── token.pickle          # Saved authentication token (auto-generated)
└── summaries/            # Generated summaries directory
```

## Security Notes

- **Never commit** `credentials.json`, `token.pickle`, or `.env` to version control
- The tool only requests **read-only** access to Gmail
- API keys and tokens are stored locally
- OAuth tokens can be revoked anytime from your [Google Account](https://myaccount.google.com/permissions)

## Troubleshooting

### "Credentials file not found"

Make sure `credentials.json` is in the project directory. Download it from Google Cloud Console.

### "ANTHROPIC_API_KEY not found"

Check that your `.env` file exists and contains the API key. Try:

```bash
export ANTHROPIC_API_KEY=your_key_here
python main.py
```

### "Label not found"

Use `--list-labels` to see all available labels:

```bash
python main.py --list-labels
```

Then use the exact label name (case-sensitive).

### Authentication Issues

If you encounter auth issues:

1. Delete `token.pickle`
2. Run the script again to re-authenticate
3. Make sure you're using the correct Google account

### API Rate Limits

- Gmail API: 250 quota units per user per second
- If you hit limits, reduce `MAX_EMAILS` or add delays
- Anthropic API: Check your plan's rate limits

## Customization

### Change the AI Model

Edit `ai_summarizer.py` and modify the model parameter:

```python
model="claude-sonnet-4-5-20250929"  # Current default
# or
model="claude-3-5-haiku-20241022"   # Faster, cheaper
```

### Adjust Summary Depth

Modify the `max_tokens` parameter in `ai_summarizer.py`:

```python
max_tokens=4000  # Current (detailed)
max_tokens=2000  # Shorter summaries
max_tokens=8000  # Very detailed
```

### Custom Prompts

Edit the `_create_summary_prompt()` method in `ai_summarizer.py` to customize what information you want in your summaries.

## Advanced Usage

### Automated Daily Summaries

Create a cron job (Linux/Mac):

```bash
# Add to crontab (crontab -e)
0 9 * * * cd /path/to/Gmail && /usr/bin/python3 main.py --label "AI-News" --output summaries/daily_$(date +\%Y\%m\%d).md
```

Or use Windows Task Scheduler for Windows systems.

### Process Multiple Labels

Create a bash script:

```bash
#!/bin/bash
python main.py --label "AI-News" --output summaries/ai_news.md
python main.py --label "Tech-Updates" --output summaries/tech_updates.md
python main.py --label "Research-Papers" --topic "Research" --output summaries/research.md
```

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

MIT License - feel free to use and modify as needed.

## Acknowledgments

- Built with [Google Gmail API](https://developers.google.com/gmail/api)
- AI powered by [Anthropic Claude](https://www.anthropic.com/)
- Uses [html2text](https://github.com/Alir3z4/html2text) for email parsing

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the [Gmail API documentation](https://developers.google.com/gmail/api/guides)
- Check [Anthropic API documentation](https://docs.anthropic.com/)

---

**Happy Summarizing!** 🤖📧
