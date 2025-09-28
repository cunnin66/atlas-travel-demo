# Infrastructure

This directory contains all Docker and service-related configuration files for the Atlas Travel Advisor project.

## Files

### Docker Configuration
- `backend.Dockerfile` - Docker configuration for the FastAPI backend service
- `frontend.Dockerfile` - Docker configuration for the Streamlit frontend service

### CLI Tools
- `Makefile` - Make-based CLI shortcuts for project management
- `atlas.sh` - Shell script-based CLI shortcuts (cross-platform alternative)

## Usage

All CLI tools are symlinked to the project root for easy access:

```bash
# From project root
make start          # Uses infrastructure/Makefile
./atlas.sh start    # Uses infrastructure/atlas.sh
```

## Docker Build Context

The Dockerfiles are designed to work with their respective service directories as build context:

- **Backend**: Context is `./backend/`, Dockerfile is `../infrastructure/backend.Dockerfile`
- **Frontend**: Context is `./frontend/`, Dockerfile is `../infrastructure/frontend.Dockerfile`

This allows the Dockerfiles to access the source code while being organized in the infrastructure directory.

## Service Architecture

```
├── infrastructure/
│   ├── backend.Dockerfile     # Backend service container
│   ├── frontend.Dockerfile    # Frontend service container
│   ├── Makefile              # CLI automation
│   └── atlas.sh              # CLI automation (alternative)
├── docker-compose.yml         # Service orchestration (kept at root)
└── .env.example              # Environment configuration
```

The `docker-compose.yml` remains at the project root as it's the main entry point for the entire application stack.
