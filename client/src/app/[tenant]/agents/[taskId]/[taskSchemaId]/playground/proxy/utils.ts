import { FileValueType } from '@/components/ObjectViewer/FileViewers/utils';
import { ToolCallRequestWithID } from '@/types/workflowAI/models';

export type ToolCallResult = {
  id?: string;
  result?: unknown;
};

export type ProxyMessageContent = {
  text?: string;
  file?: FileValueType;
  tool_call_request?: ToolCallRequestWithID;
  tool_call_result?: ToolCallResult;
};

export type ProxyMessage = {
  role: 'user' | 'system' | 'assistant';
  content: ProxyMessageContent[];
};

export function createEmptyMessageContent(): ProxyMessageContent {
  return {
    text: undefined,
    file: undefined,
    tool_call_request: undefined,
  };
}

export function createEmptySystemMessage(): ProxyMessage {
  return {
    role: 'system',
    content: [createEmptyMessageContent()],
  };
}

export function createEmptyUserMessage(): ProxyMessage {
  return {
    role: 'user',
    content: [createEmptyMessageContent()],
  };
}
