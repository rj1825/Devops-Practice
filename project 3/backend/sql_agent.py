import os
import json
import logging
from sqlalchemy import text
from database import SessionLocal, engine

# Set up logging
logger = logging.getLogger("sql_agent")
logger.setLevel(logging.INFO)

# Mock translation dictionary for offline/no-API-key execution
MOCK_QUERIES = {
    "total revenue": "SELECT SUM(total_amount) AS total_revenue FROM orders;",
    "how much money": "SELECT SUM(total_amount) AS total_revenue FROM orders;",
    "who bought shoes": "SELECT DISTINCT customers.name FROM customers JOIN orders ON customers.id = orders.customer_id JOIN products ON products.id = orders.product_id WHERE products.name LIKE '%Shoes%';",
    "shoe customers": "SELECT DISTINCT customers.name FROM customers JOIN orders ON customers.id = orders.customer_id JOIN products ON products.id = orders.product_id WHERE products.name LIKE '%Shoes%';",
    "list products": "SELECT name, category, price, stock FROM products;",
    "what products": "SELECT name, category, price, stock FROM products;",
    "how many customers": "SELECT COUNT(*) AS customer_count FROM customers;",
    "count customers": "SELECT COUNT(*) AS customer_count FROM customers;",
    "top customer": "SELECT customers.name, SUM(orders.total_amount) AS spent FROM customers JOIN orders ON customers.id = orders.customer_id GROUP BY customers.name ORDER BY spent DESC LIMIT 1;",
    "highest spender": "SELECT customers.name, SUM(orders.total_amount) AS spent FROM customers JOIN orders ON customers.id = orders.customer_id GROUP BY customers.name ORDER BY spent DESC LIMIT 1;"
}

def get_schema_info() -> str:
    """Returns database schema information as a readable string for the LLM prompt."""
    schema_desc = """
    We have a database with three tables:
    1. Table: customers
       - id: INTEGER (Primary Key)
       - name: VARCHAR
       - email: VARCHAR
       - joined_date: DATETIME
    2. Table: products
       - id: INTEGER (Primary Key)
       - name: VARCHAR
       - category: VARCHAR
       - price: FLOAT
       - stock: INTEGER
    3. Table: orders
       - id: INTEGER (Primary Key)
       - customer_id: INTEGER (Foreign Key to customers.id)
       - product_id: INTEGER (Foreign Key to products.id)
       - quantity: INTEGER
       - total_amount: FLOAT
       - order_date: DATETIME
    """
    return schema_desc

class SQLAgent:
    def __init__(self):
        # Check for Google API key or Gemini API key
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.use_llm = False
        
        if self.api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=self.api_key,
                    temperature=0.0
                )
                self.use_llm = True
                logger.info("Successfully loaded Google Gemini LLM for SQLAgent.")
            except Exception as e:
                logger.warning(f"Failed to initialize ChatGoogleGenerativeAI ({e}). Falling back to rules-based Mock mode.")
        else:
            logger.info("No GOOGLE_API_KEY or GEMINI_API_KEY found. Using rules-based Mock mode for offline execution.")

    def generate_sql(self, question: str) -> str:
        """Translates user's natural language question into SQL."""
        question_lower = question.lower().strip()
        
        # 1. LLM translation route
        if self.use_llm:
            try:
                schema_context = get_schema_info()
                prompt = (
                    f"You are a SQL expert. Given the database schema:\n{schema_context}\n"
                    f"Translate this question into a SQLite-compatible SQL query: \"{question}\"\n"
                    f"Output ONLY the SQL query code inside a single line. Do not use backticks, markdown, or any explanations."
                )
                response = self.llm.invoke(prompt)
                sql = response.content.replace("```sql", "").replace("```", "").strip()
                logger.info(f"LLM Generated SQL: {sql}")
                return sql
            except Exception as e:
                logger.error(f"LLM SQL Generation failed: {e}. Falling back to rules-based matching.")
        
        # 2. Rule-based offline mock fallback route
        for key, mock_sql in MOCK_QUERIES.items():
            if key in question_lower:
                return mock_sql
                
        # Generic fallback if no match found offline
        return "SELECT * FROM products;"

    def execute_query(self, sql_query: str):
        """Executes SQL query and returns raw results and column descriptions."""
        db = SessionLocal()
        try:
            result = db.execute(text(sql_query))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            db.close()
            return rows, columns
        except Exception as e:
            db.close()
            logger.error(f"SQL Execution failed for query '{sql_query}': {e}")
            raise e

    def generate_explanation(self, question: str, sql_query: str, results: list) -> str:
        """Converts raw data results into a conversational explanation using the LLM."""
        # 1. LLM route
        if self.use_llm:
            try:
                results_json = json.dumps(results[:10], default=str)
                prompt = (
                    f"You are a helpful business assistant. A user asked: \"{question}\"\n"
                    f"We ran this SQL query: `{sql_query}`\n"
                    f"And got these database results:\n{results_json}\n\n"
                    f"Generate a friendly, concise summary answering the user's question directly based on these results."
                )
                response = self.llm.invoke(prompt)
                return response.content.strip()
            except Exception as e:
                logger.error(f"LLM Explanation failed: {e}. Using offline generic renderer.")

        # 2. Offline summary builder
        if not results:
            return "No matching records were found in the database."
            
        # Format a simple text list
        summary = "Based on the records:\n"
        for row in results[:5]:
            summary += " - " + ", ".join(f"{k}: {v}" for k, v in row.items()) + "\n"
        if len(results) > 5:
            summary += f" ...and {len(results) - 5} more records."
        return summary
