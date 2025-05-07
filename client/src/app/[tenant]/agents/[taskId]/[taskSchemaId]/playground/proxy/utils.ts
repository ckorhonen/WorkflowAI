import { FileValueType } from '@/components/ObjectViewer/FileViewers/utils';

export type ProxyMessageContent = {
  text?: string;
  file?: FileValueType;
};

export type ProxyMessage = {
  role: 'user' | 'system' | 'assistant';
  content: ProxyMessageContent[];
};

export function createEmptyMessageContent(): ProxyMessageContent {
  return {
    text: undefined,
    file: undefined,
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
