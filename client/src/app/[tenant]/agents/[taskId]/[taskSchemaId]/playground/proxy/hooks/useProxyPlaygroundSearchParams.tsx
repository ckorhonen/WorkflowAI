import { useCallback, useEffect, useState } from 'react';
import { useParsedSearchParams, useRedirectWithParams } from '@/lib/queryString';

export function useProxyPlaygroundSearchParams() {
  const {
    versionId: versionIdFromParams,
    taskRunId: runIdForModal,
    taskRunId1: taskRunId1FromParams,
    taskRunId2: taskRunId2FromParams,
    taskRunId3: taskRunId3FromParams,
    baseRunId: baseRunIdFromParams,
    showDiffMode: showDiffModeFromParams,
    hiddenModelColumns: hiddenModelColumnsFromParams,
  } = useParsedSearchParams(
    'versionId',
    'taskRunId',
    'taskRunId1',
    'taskRunId2',
    'taskRunId3',
    'baseRunId',
    'showDiffMode',
    'hiddenModelColumns'
  );

  const redirectWithParams = useRedirectWithParams();

  const [versionId, setVersionId] = useState(versionIdFromParams);
  const [taskRunId1, setTaskRunId1] = useState(taskRunId1FromParams);
  const [taskRunId2, setTaskRunId2] = useState(taskRunId2FromParams);
  const [taskRunId3, setTaskRunId3] = useState(taskRunId3FromParams);
  const [baseRunId, setBaseRunId] = useState(baseRunIdFromParams);
  const [showDiffMode, setShowDiffMode] = useState(showDiffModeFromParams);
  const [hiddenModelColumns, setHiddenModelColumns] = useState(hiddenModelColumnsFromParams);

  useEffect(() => {
    redirectWithParams({
      params: {
        versionId: versionId,
        taskRunId1: taskRunId1,
        taskRunId2: taskRunId2,
        taskRunId3: taskRunId3,
        baseRunId: baseRunId,
        showDiffMode: showDiffMode,
        hiddenModelColumns: hiddenModelColumns,
      },
      scroll: false,
    });
  }, [versionId, taskRunId1, taskRunId2, taskRunId3, baseRunId, showDiffMode, hiddenModelColumns, redirectWithParams]);

  const setRunIdForModal = useCallback(
    (taskRunId: string | undefined) => {
      redirectWithParams({
        params: {
          taskRunId: taskRunId,
        },
        scroll: false,
      });
    },
    [redirectWithParams]
  );

  return {
    versionId,
    taskRunId1,
    taskRunId2,
    taskRunId3,
    baseRunId,
    showDiffMode,
    hiddenModelColumns,
    runIdForModal,
    setVersionId,
    setTaskRunId1,
    setTaskRunId2,
    setTaskRunId3,
    setBaseRunId,
    setShowDiffMode,
    setHiddenModelColumns,
    setRunIdForModal,
  };
}
