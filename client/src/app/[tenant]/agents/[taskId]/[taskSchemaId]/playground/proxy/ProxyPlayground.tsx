'use client';

/* eslint-disable max-lines */
import { Link16Regular } from '@fluentui/react-icons';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';
import useMeasure from 'react-use-measure';
import { useMap } from 'usehooks-ts';
import TaskRunModal from '@/components/TaskRunModal/TaskRunModal';
import { Button } from '@/components/ui/Button';
import { PageContainer } from '@/components/v2/PageContainer';
import { RequestError } from '@/lib/api/client';
import { useCopyCurrentUrl } from '@/lib/hooks/useCopy';
import { useDemoMode } from '@/lib/hooks/useDemoMode';
import { useIsMobile } from '@/lib/hooks/useIsMobile';
import { scrollTo } from '@/lib/scrollUtils';
import {
  useAIModels,
  useOrFetchOrganizationSettings,
  useOrFetchTask,
  useOrFetchVersions,
  useScheduledMetaAgentMessages,
  useTasks,
} from '@/store';
import { useOrExtractTemplete } from '@/store/extract_templete';
import { useOrganizationSettings } from '@/store/organization_settings';
import { ToolCallName, usePlaygroundChatStore } from '@/store/playgroundChatStore';
import { useTaskSchemas } from '@/store/task_schemas';
import { useVersions } from '@/store/versions';
import { GeneralizedTaskInput, TaskSchemaResponseWithSchema } from '@/types';
import { ModelOptional, TaskID, TaskSchemaID, TenantID } from '@/types/aliases';
import { StreamError, captureIfNeeded } from '@/types/errors';
import {
  MajorVersion,
  PlaygroundState,
  RunRequest,
  RunV1,
  SelectedModels,
  TaskGroupProperties_Input,
  TaskInputDict,
  ToolKind,
  Tool_Output,
} from '@/types/workflowAI';
import { ProxyMessage } from '@/types/workflowAI';
import { PlaygroundChat } from '../components/Chat/PlaygroundChat';
import { RunAgentsButton } from '../components/RunAgentsButton';
import { useFetchTaskRunUntilCreated } from '../hooks/useFetchTaskRunUntilCreated';
import { RunTaskOptions } from '../hooks/usePlaygroundPersistedState';
import { useTaskRunners } from '../hooks/useTaskRunners';
import { useVersionsForTaskRunners } from '../hooks/useVersionsForRuns';
import { PlaygroundModels } from '../hooks/utils';
import { PlaygroundOutput } from '../playgroundOutput';
import { ProxySection } from './ProxySection';
import { getFromProxyHistory, useSaveToProxyHistory } from './hooks/useProxyHistory';
import { useProxyMatchVersion } from './hooks/useProxyMatchVersion';
import { useProxyPlaygroundStates } from './hooks/useProxyPlaygroundStates';
import { useProxyStreamedChunks } from './hooks/useProxyStreamedChunks';
import { findMessagesInVersion, repairMessageKeyInInput } from './utils';

export type Props = {
  taskId: TaskID;
  tenant: TenantID | undefined;
  taskSchemaId: TaskSchemaID;
  schema: TaskSchemaResponseWithSchema;
};

export function ProxyPlayground(props: Props) {
  const { tenant, taskId, taskSchemaId, schema } = props;

  const { task, isInitialized: isTaskInitialized } = useOrFetchTask(tenant, taskId);

  const {
    historyId,
    version,
    setShowDiffMode,
    setHiddenModelColumns,
    showDiffMode,
    hiddenModelColumns,
    run1,
    run2,
    run3,
    taskRunId1,
    taskRunId2,
    taskRunId3,
    baseRun,
    setTaskRunId,
    resetTaskRunIds,
    setRunIdForModal,
    runIdForModal,
    temperature,
    setTemperature,
    outputModels,
    setOutputModels,
    allModels,
    changeSchemaIdAndRequestRunning,
  } = useProxyPlaygroundStates(tenant, taskId, taskSchemaId);

  const inputSchema = useMemo(() => schema?.input_schema.json_schema, [schema]);
  const outputSchema = useMemo(() => schema?.output_schema.json_schema, [schema]);

  const [input, setInput] = useState<GeneralizedTaskInput | undefined>(getFromProxyHistory(historyId, 'input'));

  const [proxyMessages, setProxyMessages] = useState<ProxyMessage[] | undefined>(
    getFromProxyHistory(historyId, 'proxy-messages')
  );

  const [proxyToolCalls, setProxyToolCalls] = useState<(ToolKind | Tool_Output)[] | undefined>(
    getFromProxyHistory(historyId, 'proxy-tool-calls')
  );

  useSaveToProxyHistory(historyId, 'input', input);
  useSaveToProxyHistory(historyId, 'proxy-messages', proxyMessages);
  useSaveToProxyHistory(historyId, 'proxy-tool-calls', proxyToolCalls);

  useEffect(() => {
    setProxyMessages(getFromProxyHistory(historyId, 'proxy-messages') ?? findMessagesInVersion(version));
    setProxyToolCalls(
      getFromProxyHistory(historyId, 'proxy-tool-calls') ?? version?.properties.enabled_tools ?? undefined
    );
  }, [version, historyId]);

  useEffect(() => {
    const input = repairMessageKeyInInput(baseRun?.task_input);
    setInput(getFromProxyHistory(historyId, 'input') ?? input);
  }, [baseRun, historyId]);

  const {
    schema: extractedInputSchema,
    inputVariblesKeys,
    error: extractedInputSchemaError,
    areThereChangesInInputSchema,
  } = useOrExtractTemplete(tenant, taskId, proxyMessages, inputSchema, historyId);

  const playgroundOutputRef = useRef<HTMLDivElement>(null);
  const [scheduledPlaygroundStateMessage, setScheduledPlaygroundStateMessage] = useState<string | undefined>(undefined);
  const fetchTaskRunUntilCreated = useFetchTaskRunUntilCreated();

  const { streamedChunks, handleStreamedChunk } = useProxyStreamedChunks(taskRunId1, taskRunId2, taskRunId3);

  const outputModelsRef = useRef<PlaygroundModels>(outputModels);
  outputModelsRef.current = outputModels;

  const [taskIndexesLoading, setTaskIndexLoading] = useState<boolean[]>([false, false, false]);

  const { majorVersions } = useOrFetchVersions(tenant, taskId, taskSchemaId);

  const runTask = useTasks((state) => state.runTask);

  const handleTaskIndexLoadingChange = useCallback(
    (index: number, loading: boolean) =>
      setTaskIndexLoading((prev) => {
        const newTaskIndexesLoading = [...prev];
        newTaskIndexesLoading[index] = loading;
        return newTaskIndexesLoading;
      }),
    []
  );

  const [userSelectedMajor, setUserSelectedMajor] = useState<number | undefined>(undefined);

  const { matchedVersion: matchedMajorVersion } = useProxyMatchVersion({
    majorVersions,
    userSelectedMajor,
    temperature,
    proxyMessages,
  });

  const fetchModels = useAIModels((state) => state.fetchModels);

  const [errorForModels, { set: setModelError, remove: removeModelError }] = useMap<string, Error>(
    new Map<string, Error>()
  );

  const createVersion = useVersions((state) => state.createVersion);

  const { noCreditsLeft } = useOrFetchOrganizationSettings();

  const fetchOrganizationSettings = useOrganizationSettings((state) => state.fetchOrganizationSettings);

  const abortControllerRun0 = useRef<AbortController | null>(null);
  const abortControllerRun1 = useRef<AbortController | null>(null);
  const abortControllerRun2 = useRef<AbortController | null>(null);

  const findAbortController = useCallback((index: number) => {
    switch (index) {
      case 0:
        return abortControllerRun0;
      case 1:
        return abortControllerRun1;
      case 2:
        return abortControllerRun2;
      default:
        return null;
    }
  }, []);

  const setAbortController = useCallback((index: number, abortController: AbortController) => {
    switch (index) {
      case 0:
        abortControllerRun0.current = abortController;
        break;
      case 1:
        abortControllerRun1.current = abortController;
        break;
      case 2:
        abortControllerRun2.current = abortController;
        break;
    }
  }, []);

  const updateTaskSchema = useTasks((state) => state.updateTaskSchema);
  const fetchTaskSchema = useTaskSchemas((state) => state.fetchTaskSchema);

  const checkAndUpdateSchemaIfNeeded = useCallback(
    async (index?: number) => {
      if (!areThereChangesInInputSchema) {
        return false;
      }

      const updatedTask = await updateTaskSchema(tenant, taskId, {
        input_schema: extractedInputSchema as Record<string, unknown>,
        output_schema: outputSchema as Record<string, unknown>,
      });

      const newSchema = `${updatedTask.schema_id}` as TaskSchemaID;

      if (newSchema === taskSchemaId) {
        return false;
      }

      await fetchTaskSchema(tenant, taskId, newSchema);
      await fetchModels(tenant, taskId, newSchema);

      changeSchemaIdAndRequestRunning(newSchema, index);

      return true;
    },
    [
      areThereChangesInInputSchema,
      extractedInputSchema,
      outputSchema,
      updateTaskSchema,
      tenant,
      taskId,
      changeSchemaIdAndRequestRunning,
      fetchTaskSchema,
      taskSchemaId,
      fetchModels,
    ]
  );

  const handleRunTask = useCallback(
    async (index: number, runOptions: RunTaskOptions = {}) =>
      new Promise<void>(async (resolve, reject) => {
        const cleanTaskRun = (model?: string, loading?: boolean) => {
          if (model) {
            removeModelError(model);
          }
          handleTaskIndexLoadingChange(index, loading ?? false);
          handleStreamedChunk(index, undefined);
          setTaskRunId(index, undefined);
        };

        const model = runOptions.externalModel || outputModels?.[index];

        if (!model) {
          cleanTaskRun();
          resolve(undefined);
          return;
        }

        cleanTaskRun(model, true);

        const oldAbortController = findAbortController(index);
        oldAbortController?.current?.abort();

        const abortController = new AbortController();
        setAbortController(index, abortController);

        try {
          const properties: TaskGroupProperties_Input = {
            model,
            temperature,
            enabled_tools: proxyToolCalls,
            messages: proxyMessages,
          };

          // We need to find or create the version that corresponds to these properties
          let id: string | undefined;
          try {
            const response = await createVersion(tenant, taskId, taskSchemaId, {
              properties,
            });
            id = response.id;
          } catch (exception: unknown) {
            cleanTaskRun(model);
            if (exception instanceof RequestError) {
              const msg = exception.humanReadableMessage();
              reject(msg);
              return;
            } else {
              reject(exception);
            }
          }

          if (abortController.signal.aborted) {
            cleanTaskRun(model);
            reject(undefined);
            return;
          }

          if (!id) {
            cleanTaskRun(model);
            reject('Failed to create version');
            return;
          }

          const body: RunRequest = {
            task_input: input as Record<string, unknown>,
            version: id,
          };

          if (temperature !== 0) {
            // the whole point of a higher temperature is to get more "creativity" and our cache removes that opportunity.
            body.use_cache = 'never';
          }

          const { id: run_id } = await runTask({
            tenant,
            taskId,
            taskSchemaId: taskSchemaId,
            body,
            onMessage: (message) => {
              if (abortController.signal.aborted) {
                return;
              }
              handleStreamedChunk(index, message);
            },
            signal: abortController.signal,
          });

          if (abortController.signal.aborted) {
            cleanTaskRun(model);
            reject(undefined);
            return;
          }

          await fetchTaskRunUntilCreated(tenant, taskId, run_id);
          // Running the task may have changed the models prices, so we need to refetch them
          await fetchModels(tenant, taskId, taskSchemaId);
          setTaskRunId(index, run_id);
          resolve();
        } catch (error) {
          cleanTaskRun(model);

          if (abortController.signal.aborted) {
            reject(undefined);
            return;
          }

          if (error instanceof Error) {
            setModelError(model, error);
          }

          if (
            error instanceof StreamError &&
            !!error.extra &&
            'runId' in error.extra &&
            typeof error.extra.runId === 'string'
          ) {
            setTaskRunId(index, error.extra.runId);
          }

          captureIfNeeded(error);
          // We don't reject here to avoid rejecting the Promise.all in handleRunTasks
          // That way if one task fails, the other ones still finish
          resolve(undefined);
        } finally {
          handleTaskIndexLoadingChange(index, false);
          fetchOrganizationSettings();
        }
      }),
    [
      removeModelError,
      handleTaskIndexLoadingChange,
      handleStreamedChunk,
      runTask,
      tenant,
      taskId,
      taskSchemaId,
      fetchTaskRunUntilCreated,
      fetchModels,
      createVersion,
      setModelError,
      fetchOrganizationSettings,
      setAbortController,
      findAbortController,
      setTaskRunId,
      input,
      proxyMessages,
      proxyToolCalls,
      temperature,
      outputModels,
    ]
  );

  const handleTaskRunAndCheckSchema = useCallback(
    async (index: number, runOptions: RunTaskOptions = {}) => {
      const schemaWasUpdated = await checkAndUpdateSchemaIfNeeded(index);
      if (schemaWasUpdated) {
        return;
      }
      await handleRunTask(index, runOptions);
    },
    [checkAndUpdateSchemaIfNeeded, handleRunTask]
  );

  const cancelRunTask = useCallback(
    (index: number) => {
      const abortController = findAbortController(index);
      abortController?.current?.abort();
    },
    [findAbortController]
  );

  const stopAllRuns = useCallback(() => {
    abortControllerRun0.current?.abort();
    abortControllerRun1.current?.abort();
    abortControllerRun2.current?.abort();
  }, []);

  const handleRunTasks = useCallback(
    async (options?: RunTaskOptions, individualOptions?: Record<number, RunTaskOptions>) => {
      resetTaskRunIds();

      const schemaWasUpdated = await checkAndUpdateSchemaIfNeeded();
      if (schemaWasUpdated) {
        return;
      }

      await Promise.all([
        handleRunTask(0, individualOptions?.[0] ?? options),
        handleRunTask(1, individualOptions?.[1] ?? options),
        handleRunTask(2, individualOptions?.[2] ?? options),
      ]);
    },
    [handleRunTask, resetTaskRunIds, checkAndUpdateSchemaIfNeeded]
  );

  const setModelsAndRunTask = useCallback(
    async (index: number, model: ModelOptional) => {
      setOutputModels(index, model ?? null);

      const options = model
        ? {
            externalModel: model,
          }
        : undefined;

      handleTaskRunAndCheckSchema(index, options);
    },
    [handleTaskRunAndCheckSchema, setOutputModels]
  );

  const areTasksRunning = useMemo(() => {
    if (!hiddenModelColumns) {
      return taskIndexesLoading.some((l) => l);
    }
    return taskIndexesLoading.filter((_, index) => !hiddenModelColumns.includes(index)).some((l) => l);
  }, [taskIndexesLoading, hiddenModelColumns]);

  const taskRuns = useMemo(() => [run1, run2, run3], [run1, run2, run3]);

  const filteredTaskRunIds = useMemo(() => {
    const runs = taskRuns.filter((taskRun) => !!taskRun) as RunV1[];
    return runs.map((taskRun) => taskRun?.id ?? '');
  }, [taskRuns]);

  const playgroundOutputsLoading: [boolean, boolean, boolean] = useMemo(
    () => [
      taskIndexesLoading[0] || !!streamedChunks[0],
      taskIndexesLoading[1] || !!streamedChunks[1],
      taskIndexesLoading[2] || !!streamedChunks[2],
    ],
    [taskIndexesLoading, streamedChunks]
  );

  const taskRunners = useTaskRunners({
    playgroundOutputsLoading,
    streamedChunks,
    taskRuns,
    handleRunTask: handleTaskRunAndCheckSchema,
    cancelRunTask,
    generatedInput: input,
  });

  const { versionsForRuns, showSaveAllVersions, onSaveAllVersions } = useVersionsForTaskRunners({
    tenant,
    taskId,
    taskRunners,
    hiddenModelColumns,
  });

  const copyUrl = useCopyCurrentUrl();

  const [containerRef, { height: containerHeight }] = useMeasure();
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const scrollToPlaygroundOutput = useCallback(() => {
    if (!playgroundOutputRef) return;
    scrollTo(scrollRef, playgroundOutputRef);
  }, [playgroundOutputRef, scrollRef]);

  const scrollToTop = useCallback(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTo({ top: 0, behavior: 'smooth' });
  }, [scrollRef]);

  const onTryPromptClick = useCallback(async () => {
    scrollToPlaygroundOutput();
    await handleTaskRunAndCheckSchema(0);
    scrollToPlaygroundOutput();
  }, [handleTaskRunAndCheckSchema, scrollToPlaygroundOutput]);

  useHotkeys('meta+enter', onTryPromptClick);

  const useParametersFromMajorVersion = useCallback(
    (version: MajorVersion) => {
      resetTaskRunIds();
      setTemperature(version.properties.temperature);

      const messages = (version.properties.messages as ProxyMessage[]) ?? undefined;
      setProxyMessages(messages);

      setUserSelectedMajor(version.major);
    },
    [setTemperature, setUserSelectedMajor, resetTaskRunIds, setProxyMessages]
  );

  const { isInDemoMode, onDifferentTenant } = useDemoMode();

  const playgroundState: PlaygroundState = useMemo(() => {
    const models: SelectedModels = {
      column_1: outputModels[0] ?? null,
      column_2: outputModels[1] ?? null,
      column_3: outputModels[2] ?? null,
    };

    const result = {
      is_proxy: true,
      version_id: version?.id,
      version_messages: proxyMessages,
      agent_input: input as Record<string, unknown>,
      agent_instructions: '',
      agent_temperature: temperature,
      agent_run_ids: filteredTaskRunIds,
      selected_models: models,
    };
    return result;
  }, [input, temperature, filteredTaskRunIds, outputModels, version, proxyMessages]);

  const markToolCallAsDone = usePlaygroundChatStore((state) => state.markToolCallAsDone);

  useScheduledMetaAgentMessages(
    tenant,
    taskId,
    taskSchemaId,
    playgroundState,
    scheduledPlaygroundStateMessage,
    setScheduledPlaygroundStateMessage,
    1000
  );

  const onToolCallChangeModels = useCallback(
    (
      columnsAndModels: {
        column: number;
        model: ModelOptional | undefined;
      }[]
    ) => {
      const individualOptions: Record<number, RunTaskOptions> = {};
      columnsAndModels.forEach((columnAndModel) => {
        setOutputModels(columnAndModel.column, columnAndModel.model);
        if (columnAndModel.model) {
          individualOptions[columnAndModel.column] = {
            externalModel: columnAndModel.model,
          };
        }
      });

      scrollToPlaygroundOutput();
      markToolCallAsDone(taskId, ToolCallName.RUN_CURRENT_AGENT_ON_MODELS);
      handleRunTasks(undefined, individualOptions);
    },
    [handleRunTasks, setOutputModels, markToolCallAsDone, scrollToPlaygroundOutput, taskId]
  );

  const onCancelChatToolCallOnPlayground = useCallback(() => {
    stopAllRuns();
    setTimeout(() => {
      stopAllRuns();
    }, 1000);
  }, [stopAllRuns]);

  const isMobile = useIsMobile();

  const shouldShowChat = useMemo(() => {
    if (isMobile) {
      return false;
    }
    if (onDifferentTenant) {
      return false;
    }
    return true;
  }, [isMobile, onDifferentTenant]);

  const addModelColumn = useCallback(() => {
    const newHiddenModelColumns = hiddenModelColumns ?? [];
    newHiddenModelColumns.pop();
    setHiddenModelColumns(newHiddenModelColumns);
  }, [hiddenModelColumns, setHiddenModelColumns]);

  const hideModelColumn = useCallback(
    (column: number) => {
      const newHiddenModelColumns = hiddenModelColumns ?? [];
      if (newHiddenModelColumns.includes(column)) {
        return;
      }
      newHiddenModelColumns.push(column);
      setHiddenModelColumns(newHiddenModelColumns);
    },
    [hiddenModelColumns, setHiddenModelColumns]
  );

  const onSetProxyMessages = useCallback(
    (messages: ProxyMessage[] | undefined) => {
      resetTaskRunIds();
      setProxyMessages(messages);
    },
    [setProxyMessages, resetTaskRunIds]
  );

  const onSetInputAndResetRuns = useCallback(
    (input: GeneralizedTaskInput | undefined) => {
      resetTaskRunIds();
      setInput(input);
    },
    [setInput, resetTaskRunIds]
  );

  const scrollToBottomOfProxyMessages = useCallback(() => {
    const proxyMessagesView = document.getElementById('proxy-messages-view');
    if (proxyMessagesView) {
      proxyMessagesView.scrollTo({
        top: proxyMessagesView.scrollHeight,
        behavior: 'auto',
      });
    }
  }, []);

  const updateInputAndRun = useCallback(
    async (input: TaskInputDict) => {
      setInput(input);
      await new Promise((resolve) => setTimeout(resolve, 200));
      scrollToBottomOfProxyMessages();
      await handleRunTasks();
    },
    [setInput, scrollToBottomOfProxyMessages, handleRunTasks]
  );

  return (
    <div className='flex flex-row h-full w-full'>
      <div className='flex h-full flex-1 overflow-hidden'>
        <PageContainer
          task={task}
          isInitialized={isTaskInitialized}
          name='Playground'
          showCopyLink={false}
          showBottomBorder={true}
          documentationLink='https://docs.workflowai.com/features/playground'
          rightBarText='Your data is not used for LLM training.'
          rightBarChildren={
            <div className='flex flex-row items-center gap-2 font-lato'>
              <Button variant='newDesign' icon={<Link16Regular />} onClick={copyUrl} className='w-9 h-9 px-0 py-0' />
              {!isMobile && (
                <RunAgentsButton
                  showSaveAllVersions={false}
                  areTasksRunning={areTasksRunning}
                  inputLoading={false}
                  areInstructionsLoading={false}
                  onSaveAllVersions={onSaveAllVersions}
                  onTryPromptClick={onTryPromptClick}
                  onStopAllRuns={stopAllRuns}
                />
              )}
            </div>
          }
          showBorders={!isMobile}
        >
          <div
            className='flex flex-col w-full h-full overflow-y-auto relative'
            ref={(element) => {
              containerRef(element);
              scrollRef.current = element;
            }}
            id='playground-scroll'
          >
            <div className='flex flex-col w-full sm:pb-0 pb-20'>
              <ProxySection
                inputSchema={inputSchema}
                extractedInputSchema={extractedInputSchema}
                inputVariblesKeys={inputVariblesKeys}
                error={extractedInputSchemaError}
                input={input}
                setInput={onSetInputAndResetRuns}
                temperature={temperature ?? 0}
                setTemperature={setTemperature}
                toolCalls={proxyToolCalls}
                setToolCalls={setProxyToolCalls}
                maxHeight={isMobile ? undefined : containerHeight - 50}
                proxyMessages={proxyMessages}
                setProxyMessages={onSetProxyMessages}
                tenant={tenant}
                taskId={taskId}
                matchedMajorVersion={matchedMajorVersion}
                majorVersions={majorVersions}
                useParametersFromMajorVersion={useParametersFromMajorVersion}
                showSaveAllVersions={showSaveAllVersions && !noCreditsLeft && !isInDemoMode}
                onSaveAllVersions={onSaveAllVersions}
                versionsForRuns={versionsForRuns}
              />

              <div ref={playgroundOutputRef} className='flex w-full'>
                <PlaygroundOutput
                  // We pass allAIModels here because we want to display all models
                  // and disable the ones that are not supported by the task schema mode.
                  aiModels={allModels}
                  areInstructionsLoading={false}
                  errorForModels={errorForModels}
                  generatedInput={input}
                  improveInstructions={() => Promise.resolve()}
                  models={outputModels}
                  onModelsChange={setModelsAndRunTask}
                  outputSchema={outputSchema}
                  showDiffMode={showDiffMode}
                  setShowDiffMode={setShowDiffMode}
                  taskId={taskId}
                  taskSchemaId={taskSchemaId}
                  taskRunners={taskRunners}
                  tenant={tenant}
                  onShowEditDescriptionModal={() => {}}
                  onShowEditSchemaModal={() => {}}
                  versionsForRuns={versionsForRuns}
                  maxHeight={isMobile ? undefined : containerHeight}
                  isInDemoMode={isInDemoMode}
                  addModelColumn={addModelColumn}
                  hideModelColumn={hideModelColumn}
                  hiddenModelColumns={hiddenModelColumns}
                  isProxy={true}
                  updateInputAndRun={updateInputAndRun}
                />
              </div>
            </div>
            <div className='fixed bottom-0 left-0 right-0 z-10 bg-white border-t border-gray-200 p-4 sm:hidden flex w-full'>
              <RunAgentsButton
                showSaveAllVersions={false}
                areTasksRunning={areTasksRunning}
                inputLoading={false}
                areInstructionsLoading={false}
                onSaveAllVersions={onSaveAllVersions}
                onTryPromptClick={onTryPromptClick}
                onStopAllRuns={stopAllRuns}
                className='flex w-full'
              />
            </div>
            {runIdForModal && (
              <TaskRunModal
                tenant={tenant}
                onClose={() => setRunIdForModal(undefined)}
                open={!!runIdForModal}
                taskId={taskId}
                taskRunId={runIdForModal}
                taskRunIds={filteredTaskRunIds}
                taskSchemaIdFromParams={taskSchemaId}
              />
            )}
          </div>
        </PageContainer>
      </div>
      {shouldShowChat && (
        <PlaygroundChat
          tenant={tenant}
          taskId={taskId}
          schemaId={taskSchemaId}
          playgroundState={playgroundState}
          onShowEditSchemaModal={() => {}}
          improveInstructions={() => Promise.resolve()}
          changeModels={onToolCallChangeModels}
          generateNewInput={() => Promise.resolve()}
          onCancelChatToolCallOnPlayground={onCancelChatToolCallOnPlayground}
          scrollToInput={scrollToTop}
          scrollToOutput={scrollToPlaygroundOutput}
        />
      )}
    </div>
  );
}
