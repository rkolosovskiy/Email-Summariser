import os
import sys
import markdown
import tempfile
from functools import wraps
from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session
from dotenv import load_dotenv

from gmail_auth import GmailAuthenticator
from googleapiclient.discovery import build
from gmail_client import GmailClient
from ai_summarizer import AISummarizer
from financial_analyst import FinancialAnalyst
from pdf_generator import PDFGenerator
from sec_manager import SECManager

import json
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Secret key needed for session/flash
# Secret key needed for session/flash
secret_key = os.getenv('FLASK_SECRET_KEY')
if not secret_key:
    # Fallback for when env var is present but empty, or missing
    secret_key = os.urandom(24)
app.secret_key = secret_key
# Simple password from environment variable
APP_PASSWORD = os.getenv('APP_PASSWORD')

# OAuth 2.0 Configuration
# Allow OAuth over HTTP for local testing
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv('GMAIL_CLIENT_ID'),
        "client_secret": os.getenv('GMAIL_CLIENT_SECRET'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Strictly require user to be logged in with Google credentials
        if not session.get('logged_in') or 'credentials' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_gmail_client():
    if 'credentials' in session:
        creds = GmailAuthenticator.dict_to_credentials(session['credentials'])
        service = build('gmail', 'v1', credentials=creds)
        return GmailClient(service)
    
    # Fallback to local/env credentials (legacy/cli mode or if no session)
    # This might fail in cloud if strictly relying on user session
    credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
    authenticator = GmailAuthenticator(credentials_path=credentials_path)
    # Note: original get_gmail_service might trigger interactive flow which is bad in web server
    # Ideally checking if we have creds before calling.
    
    # For now, let's assume if no session, we return None or try the old way but be careful
    service = authenticator.get_gmail_service() 
    return GmailClient(service)

def get_summarizer():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    return AISummarizer(api_key)

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        # If already logged in, go to index
        if session.get('logged_in') and 'credentials' in session:
            return redirect(url_for('index'))
    
        if request.method == 'POST':
            password = request.form.get('password')
            if password == APP_PASSWORD:
                session['logged_in'] = True
                return redirect(url_for('index'))
            else:
                flash('Invalid password')
        return render_template('login.html')
    except Exception as e:
        import traceback
        return f"<h1>Debug Error (500)</h1><pre>{traceback.format_exc()}</pre>", 500

@app.route('/google/login')
def google_login():
    try:
        # Dynamically determine redirect URI based on request
        # For local: http://localhost:8080/oauth2callback
        # For Cloud Run: https://<service-url>/oauth2callback
        redirect_uri = url_for('oauth2callback', _external=True)
    
        # Fix for local mismatch: Google Console usually has http://127.0.0.1:8080/oauth2callback
        # If browser is on localhost, force 127.0.0.1 to match Console.
        if 'localhost' in redirect_uri:
            redirect_uri = redirect_uri.replace('localhost', '127.0.0.1')

        # Enforce HTTPS on Cloud Run (or any non-local environment)
        if 'localhost' not in request.host and '127.0.0.1' not in request.host:
            if redirect_uri.startswith('http:'):
                redirect_uri = redirect_uri.replace('http:', 'https:', 1)
        
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES
        )
        flow.redirect_uri = redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        session['state'] = state
        return redirect(authorization_url)
    except Exception as e:
        import traceback
        return f"<h1>Error in /google/login</h1><pre>{traceback.format_exc()}</pre>", 500

@app.route('/oauth2callback')
def oauth2callback():
    if 'state' not in session:
        flash('Authentication canceled or session expired. Please try again.')
        return redirect(url_for('login'))
        
    state = session['state']
    
    redirect_uri = url_for('oauth2callback', _external=True)

    # Fix for local mismatch: Ensure we use the exact same URI as we sent in the login request
    if 'localhost' in redirect_uri:
        redirect_uri = redirect_uri.replace('localhost', '127.0.0.1')
    
    # Enforce HTTPS on Cloud Run
    if 'localhost' not in request.host and '127.0.0.1' not in request.host:
        if redirect_uri.startswith('http:'):
            redirect_uri = redirect_uri.replace('http:', 'https:', 1)
    
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        state=state
    )
    flow.redirect_uri = redirect_uri
    
    # Use the authorization server's response to fetch the OAuth 2.0 token.
    authorization_response = request.url
    
    # Enforce HTTPS on Cloud Run for the authorization response too
    if 'localhost' not in request.host and '127.0.0.1' not in request.host:
        if authorization_response.startswith('http:'):
            authorization_response = authorization_response.replace('http:', 'https:', 1)
            
    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as e:
        flash(f'Authentication failed: {str(e)}')
        return redirect(url_for('login'))
    
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    session['logged_in'] = True # Mark as logged in
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('credentials', None)
    return redirect(url_for('login'))

@app.route('/health')
def health():
    return "OK", 200

@app.route('/', methods=['GET'])
@login_required
def index():
    labels = []
    try:
        if 'credentials' in session:
            # Using the existing client architecture which is cleaner
            client = get_gmail_client()
            # We need to access the service directly or add a list_labels method to GmailClient
            # Let's inspect GmailClient first, but for now assuming we can add/use raw service
            # Actually, let's verify if GmailClient has list_labels or similar.
            # If not, let's use the service directly here for speed
            service = client.service 
            results = service.users().labels().list(userId='me').execute()
            labels_raw = results.get('labels', [])
            # Filter system labels if desired, or just pass all
            # Sorting alphabetically
            labels = sorted([l['name'] for l in labels_raw])
    except Exception as e:
        print(f"Error fetching labels: {e}")
        # flash(f"Error fetching labels: {e}") # Optional

    return render_template('index.html', labels=labels)

@app.route('/summarize', methods=['POST'])
@login_required
def summarize():
    topic = request.form.get('topic') or os.getenv('FOCUS_TOPIC', 'AI')
    label = request.form.get('label') or os.getenv('GMAIL_LABEL', 'INBOX')
    try:
        max_emails = int(request.form.get('max_emails') or os.getenv('MAX_EMAILS', '50'))
    except ValueError:
        max_emails = 50

    # Get date range parameters (optional)
    after_date = request.form.get('after_date') or None
    before_date = request.form.get('before_date') or None

    # 1. Authenticate & Fetch
    try:
        client = get_gmail_client()
        emails = client.fetch_emails(
            label_name=label, 
            max_results=max_emails,
            after_date=after_date,
            before_date=before_date
        )
    except Exception as e:
        import traceback
        return f"<h3>Error</h3><pre>{str(e)}\n\n{traceback.format_exc()}</pre>", 500

    if not emails:
        return render_template('summary.html', content_html="<p>No emails found for the specified label.</p>", markdown_content="")

    # 2. Summarize
    summarizer = get_summarizer()
    if not summarizer:
        return "Gemini API Key missing. Please check configuration.", 500
    
    summary_markdown = summarizer.summarize_emails(emails, focus_topic=topic)
    
    # 3. Convert to HTML for display
    # Using extensions for better rendering (tables, fenced_code)
    html_content = markdown.markdown(summary_markdown, extensions=['fenced_code', 'tables'])

    return render_template('summary.html', content_html=html_content, markdown_content=summary_markdown)

# --- Q_Reports Routes ---
@app.route('/q_reports', methods=['GET'])
@login_required
def q_reports():
    sec_manager = SECManager()
    watchlist = sec_manager.get_watchlist()
    last_action = session.pop('q_reports_action', None)
    return render_template('q_reports.html', watchlist=watchlist, last_action=last_action)

@app.route('/q_reports/add_ticker', methods=['POST'])
@login_required
def add_ticker():
    ticker = request.form.get('ticker')
    if ticker:
        sec_manager = SECManager()
        if sec_manager.add_ticker(ticker):
             session['q_reports_action'] = f"Added {ticker} to watchlist."
        else:
             session['q_reports_action'] = f"{ticker} already in watchlist."
    return redirect(url_for('q_reports'))

@app.route('/q_reports/remove_ticker', methods=['POST'])
@login_required
def remove_ticker():
    ticker = request.form.get('ticker')
    if ticker:
        sec_manager = SECManager()
        if sec_manager.remove_ticker(ticker):
            session['q_reports_action'] = f"Removed {ticker} from watchlist."
    return redirect(url_for('q_reports'))

@app.route('/q_reports/download', methods=['POST'])
@login_required
def fetch_reports():
    # This might take a while, ideally should be async/background task
    # For now, we'll run it synchronously (beware of timeouts on Cloud Run!)
    try:
        sec_manager = SECManager()
        summary = sec_manager.download_all_watchlist(amount=1)
        session['q_reports_action'] = f"Download Complete!\n{json.dumps(summary, indent=2)}"
    except Exception as e:
        session['q_reports_action'] = f"Error downloading: {str(e)}"
    return redirect(url_for('q_reports'))

@app.route('/q_reports/analyze', methods=['POST'])
@login_required
def analyze_reports():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        session['q_reports_action'] = "Error: GEMINI_API_KEY missing."
        return redirect(url_for('q_reports'))

    sec_manager = SECManager()
    watchlist = sec_manager.get_watchlist()
    tickers = watchlist.get('tickers', [])
    
    analyst = FinancialAnalyst(api_key)
    
    # Check what we have downloaded
    individual_analyses = [] # List of (ticker, type, summary)
    
    # For this MVP, let's just look for 10-Qs first, then 10-Ks if no 10-Q
    for ticker in tickers:
        f_path = sec_manager.get_latest_filing_path(ticker, "10-Q")
        r_type = "10-Q"
        if not f_path:
            f_path = sec_manager.get_latest_filing_path(ticker, "10-K")
            r_type = "10-K"
            
        if f_path:
            try:
                # Read the file
                with open(f_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Analyze it
                # Using a crude HTML->Text if needed, or just raw text depending on file format
                # For MVP, raw text is usually okay for Gemini if not too messy
                summary = analyst.analyze_filing(content, ticker, r_type)
                individual_analyses.append((ticker, r_type, summary))
            except Exception as e:
                print(f"Failed to analyze {ticker}: {e}")
    
    if not individual_analyses:
        session['q_reports_action'] = "No downloaded reports found. Please click 'Fetch Latest Reports' first."
        return redirect(url_for('q_reports'))

    # Synthesize
    custom_prompt = request.form.get('custom_prompt')
    final_report = analyst.synthesize_reports(individual_analyses, custom_prompt=custom_prompt)
    
    # Store result to be shown in template
    # We'll pass it to render_template via a temporary session store or re-render
    # Ideally, we should redirect and show it.
    # Hack for MVP: Store in a global variable or user session if small enough.
    # Better: Write to a file or database. 
    # Let's render it directly by calling the view function with context? 
    # No, redirection is safer. Let's put it in session if it fits, or assume we just show the preview.
    # Markdown to HTML
    html_report = markdown.markdown(final_report)
    
    return render_template('q_reports.html', watchlist=watchlist, analysis_result=html_report, last_action="Analysis Complete!")

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    markdown_content = request.form.get('markdown_content')
    if not markdown_content:
        return redirect(url_for('index'))

    # Generate PDF
    generator = PDFGenerator()
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        output_path = tmp.name
    
    try:
        generator.generate_pdf(markdown_content, output_path)
        return send_file(
            output_path,
            as_attachment=True,
            download_name='gmail_summary.pdf',
            mimetype='application/pdf'
        )
    finally:
        # Clean up is tricky with send_file as it needs the file open/existing
        # Flask's send_file can execute a callback after sending, 
        # but for simple temp files, we rely on OS cleanup or simple delete-on-close strategies if handled manually.
        # But here valid pattern is usually just letting it stay in tmp or scheduling cleanup. 
        # For this logic, we will rely on standard temp dir cleaning or let it persist briefly.
        pass

if __name__ == '__main__':
    # Local development
    app.run(debug=True, port=8080)
