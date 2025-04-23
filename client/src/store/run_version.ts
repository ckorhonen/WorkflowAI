import { enableMapSet, produce } from 'immer';
import { useEffect } from 'react';
import { useRef } from 'react';
import { create } from 'zustand';
import { Method, SSEClient } from '@/lib/api/client';
import { TaskID, TaskSchemaID, TenantID } from '@/types/aliases';
import { GeneralizedTaskInput } from '@/types/task_run';
import { RunRequest, RunResponseStreamChunk } from '@/types/workflowAI';
import { buildRunVersionScopeKey, runTaskPathNoProxy } from './utils';

enableMapSet();

interface RunVersionState {
  isRunningVersion: Map<string, boolean>;
  runMessages: Map<string, RunResponseStreamChunk>;
  runErrors: Map<string, Error>;

  runVersion(
    tenant: TenantID | undefined,
    taskId: TaskID,
    taskSchemaId: TaskSchemaID,
    versionId: string,
    input: GeneralizedTaskInput
  ): Promise<void>;
}

export const useRunVersion = create<RunVersionState>((set, get) => ({
  isRunningVersion: new Map(),
  runMessages: new Map(),
  runErrors: new Map(),

  runVersion: async (
    tenant: TenantID | undefined,
    taskId: TaskID,
    taskSchemaId: TaskSchemaID,
    versionId: string,
    input: GeneralizedTaskInput
  ): Promise<void> => {
    const scopeKey = buildRunVersionScopeKey({
      tenant,
      taskId,
      taskSchemaId,
      versionId,
      input,
    });

    if (!scopeKey) return;

    if (get().isRunningVersion.get(scopeKey) ?? false) return;

    set(
      produce((state: RunVersionState) => {
        state.isRunningVersion.set(scopeKey, true);
      })
    );

    try {
      const lastMessage = await SSEClient<RunRequest, RunResponseStreamChunk>(
        `${runTaskPathNoProxy(tenant)}/${taskId}/schemas/${taskSchemaId}/run`,
        Method.POST,
        {
          task_input: input as Record<string, unknown>,
          version: versionId,
        },
        (message) => {
          set(
            produce((state: RunVersionState) => {
              state.runMessages.set(scopeKey, message);
            })
          );
        }
      );

      set(
        produce((state: RunVersionState) => {
          state.runMessages.set(scopeKey, lastMessage);
        })
      );
    } catch (error) {
      set(
        produce((state: RunVersionState) => {
          state.runErrors.set(scopeKey, error as Error);
        })
      );
    }
    set(
      produce((state: RunVersionState) => {
        state.isRunningVersion.set(scopeKey, false);
      })
    );
  },
}));

export const useOrRunVersion = (
  tenant: TenantID | undefined,
  taskId: TaskID,
  taskSchemaId: TaskSchemaID,
  versionId: string | undefined,
  input: GeneralizedTaskInput
) => {
  const scopeKey = buildRunVersionScopeKey({
    tenant,
    taskId,
    taskSchemaId,
    versionId,
    input,
  });

  const runVersion = useRunVersion((state) => state.runVersion);
  const isRunningVersion = useRunVersion((state) => (scopeKey ? state.isRunningVersion.get(scopeKey) : false));
  const runMessage = useRunVersion((state) => (scopeKey ? state.runMessages.get(scopeKey) : undefined));
  const error = useRunVersion((state) => (scopeKey ? state.runErrors.get(scopeKey) : undefined));

  const isRunningVersionRef = useRef(isRunningVersion);
  isRunningVersionRef.current = isRunningVersion;

  const wasRunRef = useRef(false);
  wasRunRef.current = !!runMessage;

  useEffect(() => {
    if (!wasRunRef.current && !isRunningVersionRef.current && !!versionId) {
      runVersion(tenant, taskId, taskSchemaId, versionId, input);
    }
  }, [runVersion, isRunningVersionRef, tenant, taskId, taskSchemaId, versionId, input]);

  return {
    isRunningVersion,
    runMessage,
    error,
  };
};
