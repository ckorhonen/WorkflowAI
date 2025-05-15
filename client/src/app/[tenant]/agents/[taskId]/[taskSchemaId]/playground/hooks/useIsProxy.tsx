import { useMemo } from 'react';
import { TaskSchemaResponseWithSchema } from '@/types';
import { JsonSchema } from '@/types/json_schema';
import { ProxyMessage, VersionV1 } from '@/types/workflowAI';

function checkSchemaForProxy(schema: TaskSchemaResponseWithSchema) {
  const inputSchema = schema.input_schema.json_schema;
  if (inputSchema.format !== 'messages') {
    return false;
  }
  return inputSchema.type === 'array' || inputSchema.type === 'object';
}

function checkVersionForProxy(version: VersionV1 | undefined) {
  if (!version) {
    return false;
  }

  if (version.input_schema) {
    return (version.input_schema as JsonSchema).format === 'messages';
  }

  return false;
}

function findMessagesInVersion(version: VersionV1 | undefined) {
  if (!version) {
    return undefined;
  }
  return version.properties.messages as ProxyMessage[];
}

function checkIfVersionHasInput(version: VersionV1 | undefined) {
  if (!version) {
    return false;
  }
  return version.properties.messages !== undefined;
}

export function useIsProxy(schema: TaskSchemaResponseWithSchema, version: VersionV1 | undefined) {
  const isProxy: boolean = useMemo(() => {
    return checkSchemaForProxy(schema) || checkVersionForProxy(version);
  }, [schema, version]);

  const hasInput = useMemo(() => {
    return checkIfVersionHasInput(version);
  }, [version]);

  const messages = useMemo(() => {
    return findMessagesInVersion(version);
  }, [version]);

  return { isProxy, hasInput, messages };
}
