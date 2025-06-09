# Node E2E Tests

## Requirements

> The package.json of this directory is referenced in the root `package.json` file. Meaning that all dependencies will be installed when running `yarn install` in the root directory.

- Node > 20
- Yarn v4

## OpenAI Examples

Examples pulled from the [OpenAI Node Examples](https://github.com/openai/openai-node/tree/master/examples) repository.

The scripts in this repo should be identical to the ones in the OpenAI Node Examples repository.
In order to run the examples while connecting to the WorkflowAI API, it is necessary to
set the `OPENAI_BASE_URL` and `OPENAI_API_KEY` environment variables to point to the WorkflowAI API.

The `run-example` script will set the `OPENAI_BASE_URL` and `OPENAI_API_KEY` environment variables to point to the WorkflowAI API.

```bash
yarn run-example openai_examples/demo.ts
```
