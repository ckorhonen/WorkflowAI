import { useCallback, useEffect, useState } from 'react';
import { StreamedChunk } from '@/types/task_run';
import { RunResponseStreamChunk } from '@/types/workflowAI';

export function useProxyStreamedChunks(
  taskRunId1: string | undefined,
  taskRunId2: string | undefined,
  taskRunId3: string | undefined
) {
  const [streamedChunks, setStreamedChunks] = useState<(StreamedChunk | undefined)[]>(() => []);

  const resetStreamedChunk = useCallback((index: number) => {
    setStreamedChunks((prev) => {
      const chunks = [...prev];
      chunks[index] = undefined;
      return chunks;
    });
  }, []);

  useEffect(() => {
    if (taskRunId1) {
      resetStreamedChunk(0);
    }

    if (taskRunId2) {
      resetStreamedChunk(1);
    }

    if (taskRunId3) {
      resetStreamedChunk(2);
    }
  }, [taskRunId1, taskRunId2, taskRunId3, resetStreamedChunk]);

  const handleStreamedChunk = useCallback((index: number, message: RunResponseStreamChunk | undefined) => {
    setStreamedChunks((prev) => {
      const chunks = [...prev];
      if (message) {
        chunks[index] = {
          output: message?.task_output,
          toolCalls: message?.tool_calls ?? undefined,
          reasoningSteps: message?.reasoning_steps ?? undefined,
        };
      } else {
        chunks[index] = undefined;
      }
      return chunks;
    });
  }, []);

  return { streamedChunks, resetStreamedChunk, setStreamedChunks, handleStreamedChunk };
}
