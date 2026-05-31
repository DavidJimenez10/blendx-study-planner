# Backend

Python/FastAPI API that handles authentication, study plan management, and task tracking. Exposes a REST API consumed by the frontend.

## Language

### Users & Authentication

**User**:
A person who registers and logs into the application. Identified by a unique `name`.
_Avoid_: Account, member, profile

**JWT (JSON Web Token)**:
A signed token returned after login/register, used to authenticate subsequent API requests via Bearer header. Contains user `sub` (id), `name`, and `exp` (expiration).
_Avoid_: Session token, API key

**Password Hash**:
A bcrypt hash of the user's password. The raw password is never stored.
_Avoid_: Encrypted password

### Study Plans

**Study Plan**:
A learning goal created by a user with a target weekly commitment in hours. May include an optional description and target completion date.
_Avoid_: Course, curriculum, learning path

**Goal**:
A short string describing what the user wants to learn or achieve (e.g. "AWS Solutions Architect").
_Avoid_: Title, name, subject

**Hours Per Week**:
The number of hours the user commits to studying this plan each week. Stored as a float.
_Avoid_: Weekly commitment, study load

### Study Tasks

**Study Task**:
A concrete action item within a study plan. Has a title, estimated hours, and a completion flag.
_Avoid_: Todo, assignment, item, step, subtask

**Estimated Hours**:
The expected time (in hours) to complete a single task. Used for planning, not tracking.
_Avoid_: Duration, effort, time required

**Completed**:
A boolean flag indicating whether the task is done. Toggling completion is a PATCH operation.
_Avoid_: Done, finished, checked

### Task Generation

**Task Generation**:
The process of using an LLM (Large Language Model) to automatically create Study Tasks from a Study Plan's goal, hours_per_week, and target_date. Invoked via `POST /plans/{id}/generate-tasks`.
_Avoid_: Auto-planning, AI scheduling, smart tasks

**LLM**:
A Large Language Model (via OpenAI API) that produces structured Study Tasks given a prompt containing the plan context. Uses the `instructor` library for Pydantic-validated output.
_Avoid_: AI model, GPT, chatbot

**max_tasks**:
An optional integer parameter on the generate-tasks request that caps the number of tasks the LLM may produce. When omitted, the LLM autonomously decides the task count.
_Avoid_: task_limit, count, num_tasks

### Plan Documents

**Plan Document**:
A file (PDF, TXT, MD) uploaded by a user and associated with a Study Plan. The original file is not persisted — only its extracted text, split into chunks, is stored as Document Chunks.
_Avoid_: Attachment, resource, file upload, material

**Document Chunk**:
A semantic fragment of text extracted from a Plan Document, stored with its embedding vector and metadata (document source, plan_id, position). Used as context for Document Chat queries.
_Avoid_: Segment, block, fragment, passage

### Document Chat

**Document Chat**:
A stateless question-answering endpoint (`POST /plans/{id}/chat`) that searches a plan's Document Chunks for relevant context, passes it to the LLM, and returns an answer grounded in the uploaded documents. Each request is independent — no conversation history is maintained. If no relevant information is found in the documents, it returns a polite fallback message instead of fabricating an answer.
_Avoid_: RAG chat, document Q&A, AI chat
