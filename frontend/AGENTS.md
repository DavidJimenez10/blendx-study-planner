# AI Study Planner - Frontend

Frontend application for the AI Study Planner, providing the UI for managing study plans and interacting with backend services.

## Tech Stack
- **Framework:** React 18
- **Build Tool:** Vite
- **Language:** TypeScript
- **Routing:** React Router DOM
- **Data Fetching:** TanStack React Query
- **UI Components:** Mantine (`@mantine/core`, `@mantine/hooks`, `@mantine/form`)
- **Icons:** Tabler Icons (`@tabler/icons-react`)

## Project map
- `src/`: Main source code directory (components, pages, hooks).
- `public/`: Static assets.

<important if="you need to run commands to build, test, lint, or generate code">

**Package Manager:** Use `npm` ONLY (do not use yarn or bun).

| Command | Description |
|---|---|
| `npm install` | Install dependencies |
| `npm run dev` | Run development server (port 5173, proxies `/api` to `http://backend:8000`) |
| `npm run build` | Typecheck & Build (runs `tsc && vite build`) - run this to verify type safety |
</important>
