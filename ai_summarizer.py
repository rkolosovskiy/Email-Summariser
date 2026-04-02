"""
AI Summarizer Module
Uses Google Gemini AI to generate summaries of email content
"""

from google import genai
from google.genai import types
from datetime import datetime


class AISummarizer:
    """AI-powered email summarizer using Google Gemini"""

    def __init__(self, api_key):
        """
        Initialize the AI summarizer

        Args:
            api_key: Google Gemini API key
        """
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.5-pro-exp-03-25'

    def summarize_emails(self, emails, focus_topic="AI"):
        """
        Generate a detailed summary of emails focused on a specific topic

        Args:
            emails: List of email dictionaries
            focus_topic: Topic to focus the summary on (default: AI)

        Returns:
            Detailed summary string
        """
        if not emails:
            return "No emails to summarize."

        print(f"\nGenerating AI summary for {len(emails)} emails...")
        print(f"Focus topic: {focus_topic}")

        # Prepare email content for analysis
        email_content = self._prepare_email_content(emails)

        # Create the prompt
        prompt = self._create_summary_prompt(email_content, focus_topic)

        try:
            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=4000,
                )
            )

            summary = response.text
            print("Summary generated successfully!")
            return summary

        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"

    def _prepare_email_content(self, emails):
        """
        Prepare email content for AI analysis

        Args:
            emails: List of email dictionaries

        Returns:
            Formatted string of email content
        """
        content_parts = []

        for i, email in enumerate(emails, 1):
            # Truncate very long email bodies
            body = email['body']
            if len(body) > 3000:
                body = body[:3000] + "... [truncated]"

            email_text = f"""
Email {i}:
From: {email['from']}
Date: {email['date']}
Subject: {email['subject']}
Content: {body}
---
"""
            content_parts.append(email_text)

        return "\n".join(content_parts)

    def _create_summary_prompt(self, email_content, focus_topic):
        """
        Create the prompt for Claude API

        Args:
            email_content: Formatted email content
            focus_topic: Topic to focus on

        Returns:
            Prompt string
        """
        prompt = f"""You are an expert analyst specializing in {focus_topic} industry news and trends.

I have a collection of emails that I need you to analyze and summarize with a focus on {focus_topic}-related topics and developments.

Please provide a comprehensive summary that includes:

1. **Executive Summary**: A high-level overview of the main {focus_topic} themes and trends discussed across all emails.

2. **Key Developments**: Detailed breakdown of important {focus_topic} news, announcements, or updates, organized by category (e.g., new technologies, company news, research breakthroughs, industry trends, regulations, etc.).

3. **Notable Companies & Projects**: Highlight any significant companies, products, or projects mentioned in relation to {focus_topic}.

4. **Emerging Trends**: Identify any emerging patterns, trends, or themes in the {focus_topic} industry based on these emails.

5. **Important Dates & Events**: Any upcoming events, deadlines, or significant dates mentioned.

6. **Action Items**: If there are any calls-to-action, opportunities, or items that require attention.

7. **Technical Insights**: Any technical details, methodologies, or innovations worth noting.

Please be thorough and specific, citing key details from the emails. Organize the information in a clear, scannable format using markdown.

Here are the emails to analyze:

{email_content}

Please provide your comprehensive {focus_topic} industry summary now:"""

        return prompt

    def generate_quick_insights(self, emails, focus_topic="AI"):
        """
        Generate quick bullet-point insights from emails

        Args:
            emails: List of email dictionaries
            focus_topic: Topic to focus on

        Returns:
            Quick insights string
        """
        if not emails:
            return "No emails to analyze."

        print(f"\nGenerating quick insights for {len(emails)} emails...")

        # Prepare condensed content
        subjects = [f"- {email['subject']}" for email in emails[:20]]
        subjects_text = "\n".join(subjects)

        prompt = f"""Based on these email subjects related to {focus_topic}, provide 5-7 key bullet points highlighting the most important trends, news, or developments:

{subjects_text}

Provide concise, actionable bullet points:"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=500,
                )
            )

            insights = response.text
            print("Quick insights generated!")
            return insights

        except Exception as e:
            print(f"Error generating insights: {e}")
            return f"Error: {str(e)}"
