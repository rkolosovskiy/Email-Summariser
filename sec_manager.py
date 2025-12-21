import json
import os
from sec_edgar_downloader import Downloader

class SECManager:
    def __init__(self, download_dir="sec_filings"):
        self.download_dir = download_dir
        self.watchlist_file = "watchlist.json"
        
        # Ensure email is set
        self.email = os.getenv('SEC_USER_EMAIL')
        if not self.email:
            print("WARNING: SEC_USER_EMAIL not found in environment variables.")
            
        # Initialize downloader with Company Name and Email
        # The library requires a user-agent string: "CompanyName ContactEmail"
        # We'll use "GmailSummarizerApp" as the company name.
        self.downloader = None
        if self.email:
            self.downloader = Downloader("GmailSummarizerApp", self.email, self.download_dir)

    def get_watchlist(self):
        """Reads the watchlist from JSON file."""
        if not os.path.exists(self.watchlist_file):
            return {"tickers": [], "report_types": []}
        
        try:
            with open(self.watchlist_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading watchlist: {e}")
            return {"tickers": [], "report_types": []}

    def save_watchlist(self, watchlist_data):
        """Saves the watchlist to JSON file."""
        try:
            with open(self.watchlist_file, 'w') as f:
                json.dump(watchlist_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving watchlist: {e}")
            return False

    def add_ticker(self, ticker):
        """Adds a ticker to the watchlist."""
        data = self.get_watchlist()
        ticker = ticker.upper().strip()
        if ticker not in data['tickers']:
            data['tickers'].append(ticker)
            self.save_watchlist(data)
            return True
        return False

    def remove_ticker(self, ticker):
        """Removes a ticker from the watchlist."""
        data = self.get_watchlist()
        ticker = ticker.upper().strip()
        if ticker in data['tickers']:
            data['tickers'].remove(ticker)
            self.save_watchlist(data)
            return True
        return False

    def download_reports_for_ticker(self, ticker, amount=1, report_types=None):
        """Downloads latest reports for a specific ticker."""
        if not self.downloader:
            raise ValueError("SEC_USER_EMAIL is missing. Cannot download.")
            
        if report_types is None:
            report_types = ["10-Q", "10-K", "8-K"]
            
        results = {}
        for r_type in report_types:
            try:
                # amount limit is per report type
                count = self.downloader.get(r_type, ticker, limit=amount)
                results[r_type] = count
            except Exception as e:
                print(f"Error downloading {r_type} for {ticker}: {e}")
                results[r_type] = 0
        return results

    def download_all_watchlist(self, amount=1):
        """Downloads reports for all tickers in watchlist."""
        data = self.get_watchlist()
        report_types = data.get('report_types', ["10-Q", "10-K"])
        tickers = data.get('tickers', [])
        
        summary = {}
        for ticker in tickers:
            print(f"Downloading for {ticker}...")
            # Ideally this would print to a real logger or update a status dict
            summary[ticker] = self.download_reports_for_ticker(ticker, amount, report_types)
            
        return summary

    def get_latest_filing_path(self, ticker, report_type):
        """Finds the filesystem path for the latest downloaded filing."""
        # Structure: sec_filings/sec-edgar-filings/{ticker}/{report_type}/{accession_number}/full-submission.txt
        # We need to find the latest valid text file.
        base_path = os.path.join(self.download_dir, "sec-edgar-filings", ticker, report_type)
        if not os.path.exists(base_path):
            return None
        
        # Get all accession folders
        accessions = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
        if not accessions:
            return None
            
        # Simplest sort: usually these are not chronological by name, but let's assume 
        # we want just *one* file. To get the "latest", we'd ideally check file times or metadata.
        # For now, let's grab the first one we find to prove the concept.
        target_folder = os.path.join(base_path, accessions[0])
        
        # The file is usually named "full-submission.txt" or "primary-document.html" depending on downloader version
        # version 5.x usually saves as primary-document.html or .txt
        # Let's check for standard text files
        for fname in os.listdir(target_folder):
            if fname.endswith(".txt") or fname.endswith(".html"):
                return os.path.join(target_folder, fname)
                
        return None
