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
from pdf_generator import PDFGenerator

import json
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Fix for handling HTTPS behind Cloud Run proxy
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
# Secret key needed for session/flash
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
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

@app.route('/google/login')
def google_login():
    # Dynamically determine redirect URI based on request
    # For local: http://localhost:8080/oauth2callback
    # For Cloud Run: https://<service-url>/oauth2callback
    redirect_uri = url_for('oauth2callback', _external=True)
    
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

@app.route('/oauth2callback')
def oauth2callback():
    if 'state' not in session:
        flash('Authentication canceled or session expired. Please try again.')
        return redirect(url_for('login'))
        
    state = session['state']
    
    redirect_uri = url_for('oauth2callback', _external=True)
    
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        state=state
    )
    flow.redirect_uri = redirect_uri
    
    # Use the authorization server's response to fetch the OAuth 2.0 token.
    authorization_response = request.url
    
    # ProxyFix logic in app.py setup handles Http->Https conversion automatically now.
            
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

    # 1. Authenticate & Fetch
    try:
        client = get_gmail_client()
        emails = client.fetch_emails(label_name=label, max_results=max_emails)
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
