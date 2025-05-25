import { GeneralizedTaskInput, TaskSchemaResponseWithSchema } from '@/types';
import { JsonSchema } from '@/types/json_schema';
import { ProxyMessage, VersionV1 } from '@/types/workflowAI';

export function checkInputSchemaForInputVaribles(inputSchema: JsonSchema | undefined) {
  if (!inputSchema) {
    return false;
  }
  return 'properties' in inputSchema && inputSchema.properties;
}

export function checkInputSchemaForProxy(inputSchema: JsonSchema) {
  return inputSchema.format === 'messages';
}

export function checkSchemaForProxy(schema: TaskSchemaResponseWithSchema) {
  const inputSchema = schema.input_schema.json_schema;
  return checkInputSchemaForProxy(inputSchema);
}

export function checkVersionForProxy(version: VersionV1 | undefined) {
  if (!version) {
    return false;
  }

  if (version.input_schema) {
    return checkInputSchemaForProxy(version.input_schema as JsonSchema);
  }

  return false;
}

export function findMessagesInVersion(version: VersionV1 | undefined) {
  if (!version) {
    return undefined;
  }
  return version.properties.messages as ProxyMessage[];
}

export function numberOfInputVariblesInInputSchema(inputSchema: JsonSchema | undefined): number {
  if (!!inputSchema && 'properties' in inputSchema && inputSchema.properties) {
    return Object.keys(inputSchema.properties).length;
  }
  return 0;
}

export function repairMessageKeyInInput(input: GeneralizedTaskInput | undefined) {
  if (!input) {
    return undefined;
  }

  const keys = Object.keys(input);
  if (keys.length === 1 && keys[0] === 'messages') {
    // change the key from 'messages' to 'workflowai.replies'
    const newInput = { 'workflowai.replies': (input as Record<string, unknown>)['messages'] };
    return newInput as GeneralizedTaskInput;
  }

  return input;
}
