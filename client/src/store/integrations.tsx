import { produce } from 'immer';
import { useEffect } from 'react';
import { create } from 'zustand';
import { client } from '@/lib/api';
import { Integration } from '@/types/workflowAI';

interface IntegrationsState {
  isLoading: boolean;
  isInitialized: boolean;
  integrations: Integration[] | undefined;

  getIntegrations: () => Promise<void>;
}

export const useIntegrations = create<IntegrationsState>((set) => ({
  isLoading: false,
  isInitialized: false,
  integrations: undefined,

  getIntegrations: async () => {
    set(
      produce((state: IntegrationsState) => {
        state.isLoading = true;
      })
    );

    const path = `/api/data/v1/integrations`;

    try {
      const { integrations } = await client.get<{ integrations: Integration[] }>(path);
      set(
        produce((state: IntegrationsState) => {
          state.integrations = integrations;
          state.isInitialized = true;
        })
      );
    } catch (error) {
      console.error('Failed to fetch integrations', error);
    } finally {
      set(
        produce((state: IntegrationsState) => {
          state.isLoading = false;
        })
      );
    }
  },
}));

export const useOrFetchIntegrations = () => {
  const integrations = useIntegrations((state) => state.integrations);
  const isLoading = useIntegrations((state) => state.isLoading);
  const isInitialized = useIntegrations((state) => state.isInitialized);
  const getIntegrations = useIntegrations((state) => state.getIntegrations);

  useEffect(() => {
    getIntegrations();
  }, [getIntegrations]);

  return {
    integrations,
    isLoading,
    isInitialized,
  };
};
