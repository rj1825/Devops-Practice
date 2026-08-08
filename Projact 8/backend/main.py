import os
import json
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(
    title="Kanban Board API",
    description="A microservice API for managing Kanban tasks using Redis.",
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

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Try connecting to Redis, fallback to in-memory store if unavailable
redis_client = None
in_memory_db: Dict[str, dict] = {}

try:
    logger.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}...")
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=2.0
    )
    # Ping to check connection
    redis_client.ping()
    logger.info("Successfully connected to Redis!")
except Exception as e:
    logger.warning(f"Failed to connect to Redis ({e}). Falling back to in-memory storage.")
    redis_client = None


class TaskSchema(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    status: str = "todo"  # todo, in-progress, done
    priority: str = "medium"  # low, medium, high


def get_next_id() -> str:
    if redis_client:
        return str(redis_client.incr("task_id_counter"))
    else:
        counter = len(in_memory_db) + 1
        while str(counter) in in_memory_db:
            counter += 1
        return str(counter)


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    db_status = "connected" if redis_client else "in-memory-fallback"
    return {
        "status": "healthy",
        "database": db_status,
        "environment": {
            "REDIS_HOST": REDIS_HOST,
            "REDIS_PORT": REDIS_PORT
        }
    }


@app.get("/api/tasks", response_model=List[TaskSchema])
def get_tasks():
    tasks = []
    if redis_client:
        try:
            keys = redis_client.keys("task:*")
            for key in keys:
                task_data = redis_client.get(key)
                if task_data:
                    tasks.append(json.loads(task_data))
        except Exception as e:
            logger.error(f"Redis error in get_tasks: {e}")
            raise HTTPException(status_code=500, detail="Database access error")
    else:
        tasks = list(in_memory_db.values())
    
    # Sort tasks by ID to keep order consistent
    tasks.sort(key=lambda t: int(t["id"]) if t["id"].isdigit() else 0)
    return tasks


@app.post("/api/tasks", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskSchema):
    task_id = get_next_id()
    task.id = task_id
    task_dict = task.model_dump()
    
    if redis_client:
        try:
            redis_client.set(f"task:{task_id}", json.dumps(task_dict))
        except Exception as e:
            logger.error(f"Redis error in create_task: {e}")
            raise HTTPException(status_code=500, detail="Database storage error")
    else:
        in_memory_db[task_id] = task_dict
        
    return task_dict


@app.put("/api/tasks/{task_id}", response_model=TaskSchema)
def update_task(task_id: str, updated_task: TaskSchema):
    if redis_client:
        try:
            key = f"task:{task_id}"
            if not redis_client.exists(key):
                raise HTTPException(status_code=404, detail="Task not found")
            updated_task.id = task_id
            task_dict = updated_task.model_dump()
            redis_client.set(key, json.dumps(task_dict))
            return task_dict
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Redis error in update_task: {e}")
            raise HTTPException(status_code=500, detail="Database update error")
    else:
        if task_id not in in_memory_db:
            raise HTTPException(status_code=404, detail="Task not found")
        updated_task.id = task_id
        task_dict = updated_task.model_dump()
        in_memory_db[task_id] = task_dict
        return task_dict


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str):
    if redis_client:
        try:
            key = f"task:{task_id}"
            if not redis_client.exists(key):
                raise HTTPException(status_code=404, detail="Task not found")
            redis_client.delete(key)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Redis error in delete_task: {e}")
            raise HTTPException(status_code=500, detail="Database deletion error")
    else:
        if task_id not in in_memory_db:
            raise HTTPException(status_code=404, detail="Task not found")
        del in_memory_db[task_id]
    return None
