# reddit-startup-extractor
A Python-based pipeline that scrapes startup-related comments from Reddit, uses a local LLM (via Ollama) to extract structured information such as startup name, location, website, and description, and stores the results in an SQLite database. Ideal for analyzing early-stage startups, market research, or building datasets for AI applications.

# Reddit Startup Analyzer

Scrapes Reddit comments and extracts startup information using **PRAW** and **Ollama LLaMA**.

## Features
- Extract startup name, location, URL, and description
- Save results to SQLite
- Uses Ollama LLaMA model locally

## Requirements

Python 3.10+

Ollama installed and running

Reddit API credentials

## Setup
```bash
git clone https://github.com/<username>/Reddit-Startup-Analyzer.git
cd Reddit-Startup-Analyzer
pip install -r requirements.txt
python main.py


