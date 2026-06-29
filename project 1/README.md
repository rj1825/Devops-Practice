# Project 1: Collaborative Kanban Dashboard & CI/CD Pipeline

This project contains a containerized microservices application representing a **Collaborative Kanban Dashboard** integrated with a local **Jenkins CI/CD Automation Pipeline**.

---

## How to Start the Application (Docker Compose)

The application stack consists of a Frontend (Nginx), Backend (FastAPI), and Database (Redis).

1. Open your terminal and navigate to the project directory:
   ```bash
   cd "project 1"
   ```
2. Build and launch all three containers in the background:
   ```bash
   docker compose up --build -d
   ```
3. Access the dashboard UI:
   * Open your browser and go to: **`http://localhost:8080`**
4. Shut down the application:
   ```bash
   docker compose down
   ```

---

## How to Manage the Jenkins Server

The automation server runs inside a Docker container, mounted to your host's Docker socket to allow running pipeline stages.

* **To Start Jenkins**:
  ```bash
  docker start jenkins-server
  ```
* **To Access the Jenkins UI**:
  * Open your browser and go to: **`http://localhost:8082`**
* **To Stop Jenkins** (to save system RAM):
  ```bash
  docker stop jenkins-server
  ```

---

## URLs Reference Table

| Component | URL | Purpose |
| :--- | :--- | :--- |
| **Kanban Dashboard** | `http://localhost:8080` | Client UI to manage, add, and progress tasks. |
| **Backend API Docs** | `http://localhost:8000/docs` | Swagger interactive OpenAPI endpoints documentation. |
| **API Health Status** | `http://localhost:8000/health` | Checks API status and connection to Redis database. |
| **Jenkins Console** | `http://localhost:8082` | Automates code linting, unit testing, and builds. |
