import { useCallback } from 'react';
import { GeneralizedTaskInput } from '@/types/task_run';
import { ProxyMessage } from '@/types/workflowAI';

export function useProxyHistory(historyId: string | undefined) {
  const inputKey = 'proxy-input' + historyId;
  const proxyMessagesKey = 'proxy-messages' + historyId;

  const saveInput = useCallback(
    (input: GeneralizedTaskInput | undefined) => {
      if (!historyId) {
        return undefined;
      }

      if (input === undefined) {
        sessionStorage.removeItem(inputKey);
      } else {
        sessionStorage.setItem(inputKey, JSON.stringify(input));
      }
    },
    [inputKey, historyId]
  );

  const getInput = useCallback(() => {
    if (!historyId) {
      return undefined;
    }

    const input = sessionStorage.getItem(inputKey);

    if (input === null) {
      return undefined;
    }
    try {
      return JSON.parse(input) as GeneralizedTaskInput;
    } catch (error) {
      console.error('Failed to parse stored input:', error);
      sessionStorage.removeItem(inputKey);
      return undefined;
    }
  }, [inputKey, historyId]);

  const saveProxyMessages = useCallback(
    (proxyMessages: ProxyMessage[] | undefined) => {
      if (!historyId) {
        return;
      }

      if (proxyMessages === undefined) {
        sessionStorage.removeItem(proxyMessagesKey);
      } else {
        sessionStorage.setItem(proxyMessagesKey, JSON.stringify(proxyMessages));
      }
    },
    [proxyMessagesKey, historyId]
  );

  const getProxyMessages = useCallback(() => {
    if (!historyId) {
      return undefined;
    }

    const proxyMessages = sessionStorage.getItem(proxyMessagesKey);

    if (proxyMessages === null) {
      return undefined;
    }
    try {
      return JSON.parse(proxyMessages) as ProxyMessage[];
    } catch (error) {
      console.error('Failed to parse stored proxy messages:', error);
      sessionStorage.removeItem(proxyMessagesKey);
      return undefined;
    }
  }, [proxyMessagesKey, historyId]);

  return {
    getInputFromHistory: getInput,
    getProxyMessagesFromHistory: getProxyMessages,
    saveInputToHistory: saveInput,
    saveProxyMessagesToHistory: saveProxyMessages,
  };
}
