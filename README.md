# Auto Survey Filler 🤖📝

This project automatically fills out **Google Forms** using AI based on contact information in a CSV file. It uses **Selenium** for browser automation, **spaCy** for NER, **HuggingFace Transformers** for semantic understanding, and **Gemini AI (via GenerativeAI)** for intelligent text answers.

---

## 🚀 Features

- Auto-login with Chrome profile
- Fills text, radio, checkbox, dropdown, and linear scale fields
- Smart field detection using:
  - Named Entity Recognition (NER) via spaCy
  - Semantic similarity via Transformers
  - AI-generated answers using Gemini
- Handles multi-page Google Forms
- Supports random selection for multiple choice questions
- Reads contact data from a CSV file

---

## 🛠 Setup Instructions

### 1. Create Virtual Environment (recommended)
# Create virtual environment
```bash
python -m venv venv
```

# Activate (Windows)
```bash
venv\Scripts\activate
```
# Activate (Mac/Linux)
```bash
source venv/bin/activate
```
### 2. Install Requirements

Install all the required Python packages using:

```bash
pip install -r requirements.txt
```
### 3. Set Up Environment Variables

Create a `.env` file inside the `src/` directory (i.e., `src/keys.env`) and add your [Google Gemini API key](https://aistudio.google.com/app/apikey) like this:

```env
GENAI_API_KEY=your_gemini_api_key_here
```
### 4. Prepare Your Data

Create a CSV file inside the `./data/` directory named `data.csv`. This file should contain user information to be used for auto-filling forms. At minimum, include `Name` and `Email` columns.

Example CSV format:

```csv
Name,Email,City,Age,Gender,Education,Profession
Alice Doe,alice@example.com,New York,24,Female,Bachelor's,Software Engineer
Bob Smith,bob@example.com,Los Angeles,30,Male,Master's,Data Scientist
```
### 5. Run main.py

```bash
py .\src\main.py
```
<h3 align="center">to be continued...</h3>
