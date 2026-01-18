# Gorgon Frontend

React + TypeScript dashboard for the Gorgon multi-agent orchestration framework.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast builds and HMR
- **TanStack Query** for data fetching
- **Zustand** for state management
- **Tailwind CSS** + **shadcn/ui** for styling
- **Recharts** for data visualization
- **React Router** for navigation

## Quick Start

```bash
# Install dependencies
npm install

# Start dev server (with API proxy to localhost:8000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── api/           # API client with typed endpoints
│   └── client.ts  # Axios-based API wrapper
├── components/    # Reusable UI components
│   ├── ui/        # shadcn/ui primitives
│   ├── Layout.tsx # Main layout wrapper
│   └── Sidebar.tsx
├── hooks/         # React Query hooks
│   └── useApi.ts  # All data fetching hooks
├── lib/           # Utility functions
│   └── utils.ts   # cn(), formatters, colors
├── pages/         # Route components
│   ├── Dashboard.tsx
│   ├── Workflows.tsx
│   ├── Executions.tsx
│   └── Budget.tsx
├── stores/        # Zustand stores
│   └── index.ts   # UI, preferences, workflow builder state
├── types/         # TypeScript interfaces
│   └── index.ts   # API types matching backend models
├── App.tsx        # Router setup
├── main.tsx       # Entry point
└── index.css      # Global styles + CSS variables
```

## Key Features

### Dashboard
- Real-time stats cards (active executions, tokens, costs)
- Token usage chart over time
- Usage breakdown by agent role
- Recent executions list
- Budget status with alerts

### Workflows
- Grid view of all workflows
- Agent role visualization
- Quick actions (run, edit, delete)
- Search/filter functionality

### Executions
- Live execution monitoring
- Progress tracking with step breakdown
- Pause/resume/cancel controls
- Checkpoint management for recovery
- Real-time logs preview

### Budget
- Monthly spending overview
- Daily cost trend charts
- Per-agent budget limits
- Alert system for threshold warnings
- Cost distribution pie chart

## API Integration

The frontend expects these endpoints from the FastAPI backend:

```
GET  /api/workflows          # List workflows
GET  /api/workflows/:id      # Get workflow details
POST /api/workflows          # Create workflow
POST /api/workflows/:id/execute  # Start execution

GET  /api/executions         # List executions
GET  /api/executions/:id     # Get execution details
POST /api/executions/:id/pause   # Pause execution
POST /api/executions/:id/resume  # Resume from checkpoint

GET  /api/budgets            # List budgets
GET  /api/budgets/summary    # Aggregated budget stats

GET  /api/dashboard/stats    # Dashboard metrics
GET  /api/health             # System health check
```

## Development

### Adding a New Page

1. Create component in `src/pages/NewPage.tsx`
2. Add route in `src/App.tsx`
3. Add nav item in `src/components/Sidebar.tsx`

### Adding API Endpoints

1. Add types in `src/types/index.ts`
2. Add method in `src/api/client.ts`
3. Create hook in `src/hooks/useApi.ts`

### Styling

Uses Tailwind CSS with CSS variables for theming. Key colors:

- Agent colors: `getAgentColor()` in utils
- Status colors: `getStatusColor()` in utils
- Theme via CSS variables in `index.css`

## Docker

```bash
# Build and run with docker-compose (from project root)
docker-compose up

# Frontend only
docker build -t gorgon-frontend .
docker run -p 3000:80 gorgon-frontend
```

## Environment Variables

```env
VITE_API_URL=http://localhost:8000/api  # API base URL
```

## License

MIT
