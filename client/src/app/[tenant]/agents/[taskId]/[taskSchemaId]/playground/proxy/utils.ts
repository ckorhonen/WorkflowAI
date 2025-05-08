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

export function createEmptyMessageContent(type?: 'text' | 'document' | 'image' | 'audio'): ProxyMessageContent {
  if (!type) {
    return {
      text: undefined,
      file: undefined,
      tool_call_request: undefined,
    };
  }

  switch (type) {
    case 'text':
      return { text: '' };
    case 'document':
      return {
        file: {
          content_type: 'application/pdf',
        },
      };
    case 'image':
      return {
        file: {
          content_type: 'image/jpeg',
        },
      };
    case 'audio':
      return {
        file: {
          content_type: 'audio/mpeg',
        },
      };
  }
}

export function createEmptySystemMessage(): ProxyMessage {
  return {
    role: 'system',
    content: [createEmptyMessageContent()],
  };
}

export function createEmptyUserMessage(type?: 'text' | 'document' | 'image' | 'audio'): ProxyMessage {
  return {
    role: 'user',
    content: [createEmptyMessageContent(type)],
  };
}

export function formatResponseToText(response: unknown) {
  if (!response) return undefined;

  const text = typeof response === 'string' ? response : JSON.stringify(response);

  try {
    const json = JSON.parse(text);
    return JSON.stringify(json, null, 2);
  } catch {
    return text;
  }
}
