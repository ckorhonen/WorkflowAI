import { useRouter } from 'next/navigation';
import { useSearchParams } from 'next/navigation';
import { usePathname } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { QueryParam, useParsedSearchParams, useRedirectWithParams } from '@/lib/queryString';
import { replaceTaskSchemaId } from '@/lib/routeFormatter';
import { TaskID, TaskSchemaID, TenantID } from '@/types/aliases';
import { saveSearchParamsToHistory } from './useProxyHistory';

export function useProxyPlaygroundSearchParams(
  tenant: TenantID | undefined,
  taskId: TaskID,
  taskSchemaId: TaskSchemaID
) {
  const {
    versionId: versionIdFromParams,
    taskRunId: runIdForModal,
    taskRunId1: taskRunId1FromParams,
    taskRunId2: taskRunId2FromParams,
    taskRunId3: taskRunId3FromParams,
    baseRunId: baseRunIdFromParams,
    showDiffMode: showDiffModeFromParams,
    hiddenModelColumns: hiddenModelColumnsFromParams,
    historyId: historyIdFromParams,
    temperature: temperatureFromParams,
    model1: model1FromParams,
    model2: model2FromParams,
    model3: model3FromParams,
  } = useParsedSearchParams(
    'versionId',
    'taskRunId',
    'taskRunId1',
    'taskRunId2',
    'taskRunId3',
    'baseRunId',
    'showDiffMode',
    'hiddenModelColumns',
    'historyId',
    'temperature',
    'model1',
    'model2',
    'model3'
  );

  const redirectWithParams = useRedirectWithParams();

  const [versionId, setVersionId] = useState(versionIdFromParams);
  const [taskRunId1, setTaskRunId1] = useState(taskRunId1FromParams);
  const [taskRunId2, setTaskRunId2] = useState(taskRunId2FromParams);
  const [taskRunId3, setTaskRunId3] = useState(taskRunId3FromParams);
  const [baseRunId, setBaseRunId] = useState(baseRunIdFromParams);
  const [showDiffMode, setShowDiffMode] = useState(showDiffModeFromParams);
  const [hiddenModelColumns, setHiddenModelColumns] = useState(hiddenModelColumnsFromParams);
  const [historyId, setHistoryId] = useState(historyIdFromParams);
  const [temperature, setTemperature] = useState<number | undefined>(
    temperatureFromParams ? Number(temperatureFromParams) : undefined
  );
  const [model1, setModel1] = useState<string | undefined>(model1FromParams);
  const [model2, setModel2] = useState<string | undefined>(model2FromParams);
  const [model3, setModel3] = useState<string | undefined>(model3FromParams);

  useEffect(() => {
    const params: Record<string, QueryParam> = {
      versionId: versionId,
      taskRunId1: taskRunId1,
      taskRunId2: taskRunId2,
      taskRunId3: taskRunId3,
      baseRunId: baseRunId,
      showDiffMode: showDiffMode,
      hiddenModelColumns: hiddenModelColumns,
      historyId: historyId,
      temperature: temperature ? temperature.toString() : undefined,
      model1: model1,
      model2: model2,
      model3: model3,
    };

    saveSearchParamsToHistory(tenant, taskId, taskSchemaId, params);

    redirectWithParams({
      params,
      scroll: false,
    });
  }, [
    versionId,
    taskRunId1,
    taskRunId2,
    taskRunId3,
    baseRunId,
    showDiffMode,
    hiddenModelColumns,
    historyId,
    temperature,
    model1,
    model2,
    model3,
    redirectWithParams,
    tenant,
    taskId,
    taskSchemaId,
  ]);

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

  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const changeSchemaId = useCallback(
    (taskSchemaId: TaskSchemaID) => {
      const newUrl = replaceTaskSchemaId(pathname, taskSchemaId);
      const search = searchParams.toString();
      const finalUrl = search ? `${newUrl}?${search}` : newUrl;
      router.replace(finalUrl, { scroll: false });
    },
    [pathname, searchParams, router]
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
    historyId,
    temperature,
    model1,
    model2,
    model3,
    setVersionId,
    setTaskRunId1,
    setTaskRunId2,
    setTaskRunId3,
    setBaseRunId,
    setShowDiffMode,
    setHiddenModelColumns,
    setRunIdForModal,
    changeSchemaId,
    setHistoryId,
    setTemperature,
    setModel1,
    setModel2,
    setModel3,
  };
}
