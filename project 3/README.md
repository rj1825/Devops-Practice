# Project 3: AI SQL RAG Chatbot System

An AI-powered Text-to-SQL dashboard allowing natural language business queries (e.g., *"What is the total revenue?"*, *"Who bought shoes?"*) to be translated to SQL, executed, and converted back into conversational statements.

---

## How to Start the Application

The application consists of a FastAPI backend (translating and executing SQL queries) and a static HTML/CSS/JS frontend dashboard.

### 1. Start the Backend API
1. Open your terminal and navigate to the backend directory:
   ```bash
   cd "project 3/backend"
   ```
2. (Optional) Configure your Google Gemini API key if you want real AI processing:
   ```powershell
   # PowerShell
   $env:GEMINI_API_KEY="your-gemini-api-key"
   ```
   *(If no API key is set, the application automatically falls back to a rules-based mock translator so you can still test the suggested prompts offline).*
3. Launch the API server:
   ```bash
   .\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
   ```

### 2. Launch the Frontend UI
* Navigate to the [project 3/frontend/](frontend/) directory and double-click [index.html](frontend/index.html) to open the interactive data console in your web browser.

---

## Suggested Prompts to Try
You can click these buttons in the frontend sidebar or type them in:
* *How much is the total revenue?*
* *Who bought shoes?*
* *List all products*
* *How many customers are there?*
* *Who is the highest spender?*

---

## How to Run the Tests
To run the automated endpoint validation tests:
```bash
cd "project 3/backend"
.\venv\Scripts\python.exe -m pytest
```
