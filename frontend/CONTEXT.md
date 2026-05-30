# Frontend

React/TypeScript single-page application built with Vite and Mantine. Provides user-facing pages for authentication, dashboard, and study plan management.

## Language

### Pages

**Login Page**:
The unauthenticated entry point. Supports both "Sign in" and "Create account" modes via tabs. On success, stores the JWT token and redirects to the dashboard.
_Avoid_: Auth page, sign-in page

**Dashboard**:
The main authenticated landing page. Displays all study plans owned by the current user in a card grid, with per-plan progress stats. Includes a call-to-action to create the first plan when empty.
_Avoid_: Home page, landing page, plans overview

**Plan Detail**:
The detail page for a single study plan. Shows plan metadata (goal, description, hours, target date), a progress bar, and the list of tasks. Supports creating and toggling tasks.
_Avoid_: Plan view, plan page

### Components

**Plan Card**:
A card component displayed on the dashboard summarizing a study plan. Shows goal, description excerpt, hours per week, progress bar, and a date badge (overdue / due today / N days left / complete).
_Avoid_: Plan tile, plan summary

**Task Item**:
A single row in the task list. Contains a checkbox to toggle completion and a badge showing estimated hours.
_Avoid_: Task row, task entry

**Private Route**:
A routing guard component. Checks for a valid JWT token; redirects to `/login` if missing or expired.
_Avoid_: Auth guard, protected route

### API Client

**API Client**:
A TypeScript module that wraps `fetch` with JWT Bearer token attachment, typed methods (login, register, CRUD for plans and tasks), and automatic token expiry handling.
_Avoid_: HTTP client, API service, network layer

**Token Storage**:
JWT tokens are stored in `localStorage` under a known key. The API client reads, writes, and clears this token automatically.
_Avoid_: Session storage, cookie auth

### Modals

**Create Plan Modal**:
A Mantine modal form for creating a new study plan. Fields: goal (required), description (optional), hours per week (required), target date (optional).
_Avoid_: New plan dialog, plan form

**Add Task Modal**:
A Mantine modal form for adding a task to a study plan. Fields: title (required), estimated hours (required).
_Avoid_: New task dialog, task form
