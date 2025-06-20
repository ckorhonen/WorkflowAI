# WorkflowAI Repo Recon

This repository is a monorepo that contains two major apps:

- **API** – Python FastAPI application.
- **Client** – Next.js application written in Typescript.

Key guidelines come from the existing `AGENTS.md` file and `.cursor/rules`:

## Development checks

- Use `poetry` for dependency management on the API side.
- Run `poetry run ruff check <path>` and `poetry run pyright <path>` on Python files.
- Run `poetry run pytest <test-file>` for tests. Unit tests live next to the code they cover.
- For the client, run `yarn workspace workflowai lint` and `yarn workspace workflowai build`.

## Docs

Documentation lives in `docsv2` and uses FumaDocs (MDX). Build the docs with `yarn workspace docs build`.

See each directory's README for setup and additional commands.
