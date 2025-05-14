import { nanoid } from 'nanoid';
import { ProxyMessage, ProxyMessageContent, ToolCallRequestWithID, ToolCallResult } from '@/types/workflowAI';

export function createEmptyMessageContent(
  type?: 'text' | 'document' | 'image' | 'audio' | 'toolCallResult' | 'toolCallRequest'
): ProxyMessageContent {
  if (!type) {
    return {
      text: undefined,
      file: undefined,
      tool_call_request: undefined,
      tool_call_result: undefined,
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
    case 'toolCallResult':
      return {
        tool_call_result: {
          id: nanoid(),
          result: 'Result of the tool call',
          tool_name: '',
          tool_input_dict: {},
        } as ToolCallResult,
      };
    case 'toolCallRequest':
      return {
        tool_call_request: {
          tool_input_dict: {
            parameter: 'value',
          },
          tool_name: 'tool_name',
          id: nanoid(),
        } as ToolCallRequestWithID,
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

export function createEmptyAgentMessage(type?: 'text' | 'document' | 'image' | 'audio'): ProxyMessage {
  return {
    role: 'assistant',
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

export function formatTextToResponse(text: string | undefined): unknown {
  if (!text) return undefined;

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}
