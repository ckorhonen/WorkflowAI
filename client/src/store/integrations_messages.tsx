import { produce } from 'immer';
import { useEffect, useRef, useState } from 'react';
import { useCallback } from 'react';
import { create } from 'zustand';
import { Method, SSEClient } from '@/lib/api/client';
import { API_URL } from '@/lib/constants';
import { IntegrationChatMessage } from '../types/workflowAI/models';

export type RedirectToAgentPlayground = {
  agent_id?: string;
  agent_schema_id?: number;
};

export type IntegrationChatResponse = {
  messages: IntegrationChatMessage[];
  redirect_to_agent_playground?: RedirectToAgentPlayground;
};

export type IntegrationChatRequest = {
  integration_slug: string;
  messages: IntegrationChatMessage[];
};

interface IntegrationChatState {
  isLoading: boolean;
  isInitialized: boolean;
  slug: string | undefined;
  messages: IntegrationChatMessage[] | undefined;
  redirectToAgentPlayground: RedirectToAgentPlayground | undefined;

  clean: () => void;
  reset: (slug: string) => void;
  sendMessage: (text: string | undefined, signal?: AbortSignal) => Promise<void>;
}

export const useIntegrationChat = create<IntegrationChatState>((set, get) => ({
  isLoading: false,
  isInitialized: false,
  slug: undefined,
  messages: undefined,
  redirectToAgentPlayground: undefined,

  clean: () => {
    set(
      produce((state: IntegrationChatState) => {
        state.isInitialized = false;
        state.isLoading = false;
        state.messages = undefined;
        state.slug = undefined;
        state.redirectToAgentPlayground = undefined;
      })
    );
  },

  reset: (slug: string) => {
    set(
      produce((state: IntegrationChatState) => {
        state.isInitialized = false;
        state.isLoading = false;
        state.messages = undefined;
        state.slug = slug;
        state.redirectToAgentPlayground = undefined;
      })
    );

    get().sendMessage(undefined);
  },

  sendMessage: async (text: string | undefined, signal?: AbortSignal) => {
    const oldMessages = get().messages;
    const slug = get().slug;

    if (!slug) {
      return;
    }

    let messages: IntegrationChatMessage[] | undefined;

    const isLoading = get().isLoading;

    if (!!isLoading) {
      return;
    }

    if (!!oldMessages && oldMessages.length > 0) {
      messages = oldMessages;
    }

    if (!!text) {
      const previousMessages = messages || [];
      messages = [
        ...previousMessages,
        { role: 'USER', content: text, sent_at: new Date().toISOString(), message_kind: 'non_specific' },
      ];
    }

    set(
      produce((state: IntegrationChatState) => {
        state.isLoading = true;
        state.messages = messages;
      })
    );

    const request: IntegrationChatRequest = {
      integration_slug: slug,
      messages: messages ?? [],
    };

    const updateMessages = (response: IntegrationChatResponse) => {
      const previouseMessages = messages ?? [];
      const updatedMessages = !!response.messages ? [...previouseMessages, ...response.messages] : previouseMessages;

      if (signal?.aborted) {
        return;
      }

      set(
        produce((state: IntegrationChatState) => {
          state.messages = updatedMessages;
        })
      );
    };

    try {
      const path = `${API_URL}/v1/integrations/messages`;

      const response = await SSEClient<IntegrationChatRequest, IntegrationChatResponse>(
        path,
        Method.POST,
        request,
        updateMessages,
        signal
      );

      set(
        produce((state: IntegrationChatState) => {
          const previouseMessages = messages ?? [];

          const updatedMessages = !!response.messages
            ? [...previouseMessages, ...response.messages]
            : previouseMessages;

          state.messages = updatedMessages;
          state.isLoading = false;
          state.isInitialized = true;

          if (!state.redirectToAgentPlayground && !!response.redirect_to_agent_playground) {
            state.redirectToAgentPlayground = response.redirect_to_agent_playground;
          }
        })
      );
    } finally {
      set(
        produce((state: IntegrationChatState) => {
          state.isLoading = false;
          state.isInitialized = true;
        })
      );
    }
  },
}));

export const useOrFetchIntegrationChat = (integrationId: string | undefined) => {
  const messages = useIntegrationChat((state) => state.messages);
  const redirectToAgentPlayground = useIntegrationChat((state) => state.redirectToAgentPlayground);
  const isLoading = useIntegrationChat((state) => state.isLoading);
  const isInitialized = useIntegrationChat((state) => state.isInitialized);

  const sendMessageIntegrationChat = useIntegrationChat((state) => state.sendMessage);
  const resetIntegrationChat = useIntegrationChat((state) => state.reset);

  const sendMessageAbortController = useRef<AbortController | null>(null);
  const sendMessageInProgressRef = useRef(false);

  const updateAbortController = useRef<AbortController | null>(null);
  const updateInProgressRef = useRef(false);

  const update = useCallback(async () => {
    if (updateInProgressRef.current || sendMessageInProgressRef.current) {
      return;
    }

    updateInProgressRef.current = true;

    updateAbortController.current?.abort();
    const newAbortController = new AbortController();
    updateAbortController.current = newAbortController;

    try {
      await sendMessageIntegrationChat(undefined, newAbortController.signal);
    } finally {
      updateInProgressRef.current = false;
    }
  }, [sendMessageIntegrationChat]);

  const sendMessage = useCallback(
    async (text: string) => {
      sendMessageInProgressRef.current = true;

      updateAbortController.current?.abort();

      sendMessageAbortController.current?.abort();
      const newAbortController = new AbortController();
      sendMessageAbortController.current = newAbortController;

      try {
        await sendMessageIntegrationChat(text, newAbortController.signal);
      } catch (error) {
        console.error('Error sending message:', error);
      } finally {
        sendMessageInProgressRef.current = false;
      }
    },
    [sendMessageIntegrationChat]
  );

  const [startUpdating, setStartUpdating] = useState(false);

  useEffect(() => {
    if (integrationId) {
      resetIntegrationChat(integrationId);
      setStartUpdating(true);
    }
  }, [integrationId, resetIntegrationChat]);

  useEffect(() => {
    if (startUpdating) {
      update();
      const intervalId = setInterval(update, 2000);
      return () => clearInterval(intervalId);
    }
  }, [startUpdating, update]);

  const onStop = useCallback(() => {
    sendMessageAbortController.current?.abort();
    updateAbortController.current?.abort();
  }, []);

  return {
    messages,
    redirectToAgentPlayground,
    isLoading,
    isInitialized,
    sendMessage,
    onStop,
  };
};
