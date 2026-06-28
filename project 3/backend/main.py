import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import init_db
from sql_agent import SQLAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend_server")

app = FastAPI(
    title="AI SQL RAG API Server",
    description="Backend microservice translating natural language questions to database queries using LangChain.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database schema and insert seed data on startup
@app.on_event("startup")
def startup_event():
    logger.info("Initializing Database...")
    init_db()
    logger.info("Database initialized successfully!")

# Initialize LangChain SQL Agent instance
sql_agent = SQLAgent()

class QuestionRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    question: str
    sql_query: str
    columns: list
    results: list
    answer: str

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "agent_mode": "LLM" if sql_agent.use_llm else "Mock/Fallback"
    }

@app.post("/api/chat", response_model=ChatResponse)
def query_database(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty.")
    
    try:
        # 1. Generate SQL query from question
        sql_query = sql_agent.generate_sql(question)
        logger.info(f"Generated SQL: {sql_query}")
        
        # 2. Execute SQL query on database
        results, columns = sql_agent.execute_query(sql_query)
        
        # 3. Generate natural language response
        answer = sql_agent.generate_explanation(question, sql_query, results)
        
        return ChatResponse(
            question=question,
            sql_query=sql_query,
            columns=columns,
            results=results,
            answer=answer
        )
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while querying the database: {str(e)}"
        )
