# WorkflowAI Repository Guide for AI Agents

This monorepo hosts the **API** (Python FastAPI) and the **Client** (Next.js with TypeScript). A documentation site powered by FumaDocs lives under `docsv2`. Always read the `README.md` inside each directory before making changes.

## Development Workflow

1. **Install Dependencies**
   - For the API run `poetry install`.
   - For the client run `yarn install` from the repository root.
2. **Follow the Coding Rules**
   - Python rules are defined in `.cursor/rules/python.mdc`.
   - The main guidelines from `AGENTS.md` apply to all code.
3. **Run Checks**
   - **Python**: `poetry run ruff check <path>` and `poetry run pyright <path>`.
   - **Client**: `yarn workspace workflowai lint` then `yarn workspace workflowai build`.
   - **Docs**: `yarn workspace docs lint` and `yarn workspace docs build` when editing files in `docsv2`.
4. **Testing**
   - Execute unit tests with `poetry run pytest <test-file.py>::<test_name>`.
   - Component and integration tests are located under `api/tests`. Use the `api_server` fixture for integration tests.

## Python Guidelines

- Keep comments and docstrings concise. Only explain non‑obvious code.
- Use modern typing syntax (`list` instead of `List`, `| None` instead of `Optional`).
- Place unit tests next to the code they test (`my_file_test.py` for `my_file.py`).
- Prefer `pytest.mark.parametrize` over duplicating test cases.
- Avoid subclassing `unittest.TestCase` and do not add `@pytest.mark.asyncio`.
- For logging, do not use f‑strings; pass variables via the `extra` parameter.

## Repository Structure

- `api/` – FastAPI backend.
- `client/` – Next.js frontend.
- `integrations/` – Example scripts demonstrating the OpenAI-compatible endpoint.
- `docsv2/` – Documentation site.

## Client Guidelines

- Run `yarn prettier-check` and `yarn format` to maintain formatting.
- Avoid unnecessary `useMemo` when the computation is simple and returns a scalar.

## Integrations

The `integrations` directory contains scripts in several languages to validate compatibility with our API. When adding a script, add a pytest that runs it using the `api_server` fixture.

## Further References

- [CONTRIBUTING.md](./CONTRIBUTING.md) explains the branching and release process.
- [AGENTS.md](./AGENTS.md) provides the detailed workflow for both API and Client.

