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
