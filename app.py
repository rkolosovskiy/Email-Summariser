import os
import sys
import markdown
import tempfile
from functools import wraps
from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session
from dotenv import load_dotenv

from gmail_auth import GmailAuthenticator
from gmail_client import GmailClient
from ai_summarizer import AISummarizer
from pdf_generator import PDFGenerator

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Secret key needed for session/flash
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
# Simple password from environment variable
APP_PASSWORD = os.getenv('APP_PASSWORD')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If no password is set in env, skip auth (optional, but good for local dev if wanted)
        if not APP_PASSWORD:
            return f(*args, **kwargs)
        
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_gmail_client():
    credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
    authenticator = GmailAuthenticator(credentials_path=credentials_path)
    service = authenticator.get_gmail_service()
    return GmailClient(service)

def get_summarizer():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    return AISummarizer(api_key)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == APP_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
@login_required
def index():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
@login_required
def summarize():
    topic = request.form.get('topic', 'AI')
    label = request.form.get('label', 'INBOX')
    try:
        max_emails = int(request.form.get('max_emails', 50))
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
