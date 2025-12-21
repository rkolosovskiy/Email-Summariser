import os
import google.generativeai as genai

class FinancialAnalyst:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Gemini API Key is required for Financial Analyst")
        genai.configure(api_key=api_key)
        # using the same model as ai_summarizer.py which is confirmed working
        self.model = genai.GenerativeModel('gemini-2.5-pro')

    def analyze_filing(self, text, ticker, filing_type):
        """Analyzes a single filing text."""
        prompt = f"""
        You are an expert financial analyst. Analyze the following {filing_type} filing for {ticker}.
        
        Focus on:
        1. Key Financial Results (Revenue, Net Income, Growth).
        2. Management's Commentary & Guidance.
        3. Major Risks or Headwinds mentioned.
        4. Any surprising or notable details.

        Keep the summary concise (under 400 words) but data-rich. Use bullet points.
        
        Filing Text (truncated if necessary):
        {text[:50000]} 
        """ 
        # Note: 50k chars is a safe starting chunk for Flash without hitting limits too hard, 
        # though Flash has a huge context window, we want speed.
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error analyzing {ticker}: {str(e)}"

    def synthesize_reports(self, analyses, custom_prompt=None):
        """Synthesizes multiple individual reports into one market overview."""
        if not analyses:
            return "No analyses to synthesize."

        combined_text = "\n\n".join([f"--- {ticker} ({r_type}) ---\n{content}" for ticker, r_type, content in analyses])
        
        if custom_prompt:
            prompt = f"""
            You are an expert financial analyst.
            Based on the following financial summaries for multiple companies:
            
            {combined_text}
            
            Answer the user's specific request:
            {custom_prompt}
            
            Output in Markdown format.
            """
        else:
            prompt = f"""
            You are a Chief Investment Officer. 
            Read the following financial summaries for multiple companies:

            {combined_text}

            Task:
            1. Identify common trends across these companies (e.g., "All tech companies mentioned slower ad spend").
            2. Highlight the standout performer and the laggard.
            3. Provide a brief 1-sentence verdict for each company.
            4. Output in Markdown format.
            """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error synthesizing reports: {str(e)}"
