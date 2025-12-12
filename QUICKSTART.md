# Quick Start Guide

Get up and running with Gmail AI Summarizer in 5 minutes!

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Your API Keys

**Gmail API:**
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download as `credentials.json` in this directory

**Anthropic API:**
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Get your API key

### 3. Configure

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 4. Run!

```bash
python main.py
```

On first run, your browser will open for Gmail authentication. Grant access and you're done!

## 📋 Common Commands

```bash
# Basic usage (uses .env settings)
python main.py

# Use a specific Gmail label
python main.py --label "AI-News"

# Quick insights instead of full summary
python main.py --quick

# See all your Gmail labels
python main.py --list-labels

# Process more emails
python main.py --max 100

# Different topic focus
python main.py --topic "Machine Learning"
```

## 💡 Tips

- **Create a Gmail label** for AI-related emails and set up auto-filtering
- **First run** requires browser authentication - subsequent runs are automatic
- **Summaries auto-save** to `summaries/` directory with timestamps
- **Read-only access** - the tool never modifies or deletes your emails

## 🎯 Typical Workflow

1. Set up Gmail filters to label incoming AI newsletters
2. Run the tool daily/weekly to get summaries
3. Review the markdown summaries in the `summaries/` folder

## ⚠️ Troubleshooting

**"Credentials file not found"**
→ Make sure `credentials.json` is in the project directory

**"ANTHROPIC_API_KEY not found"**
→ Check your `.env` file has the API key

**"Label not found"**
→ Run `python main.py --list-labels` to see available labels

## 📚 Need More Help?

See the full [README.md](README.md) for detailed documentation, advanced usage, and customization options.

---

**That's it!** You're ready to start summarizing your AI emails. 🎉
