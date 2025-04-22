import { produce } from 'immer';
import { create } from 'zustand';
import { TaskID, TaskSchemaID, TenantID } from '@/types/aliases';
import { buildScopeKey } from './utils';

export type SideBySideEntry = {
  versionId: string | undefined;
  modelId: string | undefined;
  inputHash: string;
  runId: string;
};

function entryExists(set: Set<SideBySideEntry>, newEntry: SideBySideEntry): boolean {
  for (const entry of set) {
    if (
      entry.runId === newEntry.runId &&
      entry.inputHash === newEntry.inputHash &&
      entry.versionId === newEntry.versionId &&
      entry.modelId === newEntry.modelId
    ) {
      return true;
    }
  }
  return false;
}

interface SideBySideState {
  runs: Map<string, Set<SideBySideEntry>>;
  addRunId: (
    tenant: TenantID | undefined,
    taskId: TaskID,
    taskSchemaId: TaskSchemaID,
    inputHash: string,
    versionId: string | undefined,
    modelId: string | undefined,
    runId: string
  ) => void;
}

export const useSideBySideStore = create<SideBySideState>((set) => ({
  runs: new Map<string, Set<SideBySideEntry>>(),

  addRunId: (
    tenant: TenantID | undefined,
    taskId: TaskID,
    taskSchemaId: TaskSchemaID,
    inputHash: string,
    versionId: string | undefined,
    modelId: string | undefined,
    runId: string
  ) => {
    const scopeKey = buildScopeKey({
      tenant,
      taskId,
      taskSchemaId,
    });

    const modelIdToUse = versionId ? undefined : modelId;
    const entry: SideBySideEntry = { versionId, modelId: modelIdToUse, inputHash, runId };

    set(
      produce((state: SideBySideState) => {
        if (!state.runs.has(scopeKey)) {
          state.runs.set(scopeKey, new Set<SideBySideEntry>());
        }

        const entries = state.runs.get(scopeKey)!;
        if (!entryExists(entries, entry)) {
          entries.add(entry);
        }
      })
    );
  },
}));
