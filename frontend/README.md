# Leafleter Frontend

React + TypeScript frontend for Leafleter — the AI-powered market intelligence SaaS platform.

## Tech Stack

- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **UI Components**: Shadcn/UI
- **State**: Zustand
- **Server State**: TanStack Query
- **Routing**: React Router
- **Charts**: Recharts
- **Testing**: Vitest

## Project Structure

```
frontend/
├── src/
│   ├── components/    # Reusable UI components
│   ├── pages/         # Route-level pages
│   ├── services/      # API clients
│   ├── stores/        # Zustand stores
│   ├── hooks/         # Custom React hooks
│   ├── types/         # TypeScript types
│   └── lib/           # Utilities
├── public/            # Static assets
├── index.html
├── package.json
└── vite.config.ts
```

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # if available
```

## Run

```bash
npm run dev
```

Open `http://localhost:5240`.

## Build

```bash
npm run build
```

Production build is output to `dist/`.

## Test

```bash
npm test
```

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8085/api/v1
```

## Scripts

| Command            | Description              |
| ------------------ | ------------------------ |
| `npm run dev`      | Start dev server         |
| `npm run build`    | Production build         |
| `npm run preview`  | Preview production build |
| `npm run lint`     | Run ESLint               |
| `npm test`         | Run tests                |
| `npm run coverage` | Run tests with coverage  |
