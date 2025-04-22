import { Loader2 } from 'lucide-react';
import { useCallback, useEffect, useMemo } from 'react';
import { useRedirectWithParams } from '@/lib/queryString';
import { useParsedSearchParams } from '@/lib/queryString';
import { useOrFetchCurrentTaskSchema } from '@/store/fetchers';
import { TaskID, TenantID } from '@/types/aliases';
import { TaskSchemaID } from '@/types/aliases';
import { ModelResponse, VersionV1 } from '@/types/workflowAI';
import { TaskInputDict } from '@/types/workflowAI';
import { SideBySideTableHeader } from './SideBySideTableHeader';
import { SideBySideTableRow } from './SideBySideTableRow';
import { SideBySideTableStatsRow } from './Stats/SideBySideTableStatsRow';

type SideBySideTableProps = {
  inputs: TaskInputDict[] | undefined;
  versions: VersionV1[];
  models: ModelResponse[] | undefined;
  tenant: TenantID | undefined;
  taskId: TaskID;
  taskSchemaId: TaskSchemaID;
  page: number;
};

export function SideBySideTable(props: SideBySideTableProps) {
  const { inputs, versions, models, tenant, taskId, taskSchemaId, page } = props;

  const { selectedLeftVersionId, selectedRightVersionId, selectedRightModelId } = useParsedSearchParams(
    'selectedLeftVersionId',
    'selectedRightVersionId',
    'selectedRightModelId'
  );

  const redirectWithParams = useRedirectWithParams();

  const setSelectedLeftVersionId = useCallback(
    (newLeftVersionId: string | undefined) => {
      redirectWithParams({
        params: {
          selectedLeftVersionId: newLeftVersionId,
          selectedRightVersionId: undefined,
          selectedRightModelId: undefined,
        },
        scroll: false,
      });
    },
    [redirectWithParams]
  );

  const setSelectedRightVersionId = useCallback(
    (newRightVersionId: string | undefined) => {
      redirectWithParams({
        params: {
          selectedRightVersionId: newRightVersionId,
          selectedRightModelId: undefined,
        },
        scroll: false,
      });
    },
    [redirectWithParams]
  );

  const setSelectedRightModelId = useCallback(
    (newRightModelId: string | undefined) => {
      redirectWithParams({
        params: {
          selectedRightVersionId: undefined,
          selectedRightModelId: newRightModelId,
        },
        scroll: false,
      });
    },
    [redirectWithParams]
  );

  const selectedLeftVersion = versions.find((version) => version.id === selectedLeftVersionId);
  const selectedRightVersion = versions.find((version) => version.id === selectedRightVersionId);
  const selectedRightModel = models?.find((model) => model.id === selectedRightModelId);

  const { taskSchema } = useOrFetchCurrentTaskSchema(undefined, taskId, taskSchemaId);

  const deployedVersion = useMemo(() => {
    if (versions.length === 0) {
      return undefined;
    }

    const prodVersion = versions.find((version) =>
      version.deployments?.some((deployment) => deployment.environment === 'production')
    );
    if (prodVersion) return prodVersion;

    const stagingVersion = versions.find((version) =>
      version.deployments?.some((deployment) => deployment.environment === 'staging')
    );
    if (stagingVersion) return stagingVersion;

    const devVersion = versions.find((version) =>
      version.deployments?.some((deployment) => deployment.environment === 'dev')
    );
    if (devVersion) return devVersion;

    return undefined;
  }, [versions]);

  useEffect(() => {
    if (versions.length === 0 || !!selectedLeftVersionId) {
      return;
    }

    const leftVersion = deployedVersion ?? versions[0];
    const rightVersion: VersionV1 | undefined = deployedVersion
      ? leftVersion.id === versions[0].id
        ? versions[1]
        : versions[0]
      : versions[1];

    redirectWithParams({
      params: {
        selectedLeftVersionId: leftVersion.id,
        selectedRightVersionId: !selectedRightModelId ? selectedRightVersionId ?? rightVersion?.id : undefined,
        selectedRightModelId: selectedRightModelId ?? undefined,
      },
      scroll: false,
    });
  }, [
    deployedVersion,
    versions,
    selectedLeftVersionId,
    selectedRightVersionId,
    selectedRightModelId,
    redirectWithParams,
  ]);

  return (
    <div className='flex flex-col w-full felx-1 border border-gray-200 rounded-[2px] overflow-hidden relative'>
      <SideBySideTableHeader
        versions={versions}
        models={models}
        baseVersion={selectedLeftVersion}
        selectedLeftVersionId={selectedLeftVersionId}
        setSelectedLeftVersionId={setSelectedLeftVersionId}
        selectedRightVersionId={selectedRightVersionId}
        setSelectedRightVersionId={setSelectedRightVersionId}
        selectedRightModelId={selectedRightModelId}
        setSelectedRightModelId={setSelectedRightModelId}
        page={page}
      />
      <div className='flex flex-col w-full flex-1 overflow-y-auto' id='side-by-side-table'>
        <SideBySideTableStatsRow
          tenant={tenant}
          taskId={taskId}
          taskSchemaId={taskSchemaId}
          selectedLeftVersionId={selectedLeftVersionId}
          selectedRightVersionId={selectedRightVersionId}
          selectedRightModelId={selectedRightModelId}
          inputs={inputs}
          leftVersion={selectedLeftVersion}
          rightVersion={selectedRightVersion}
        />
        {!!taskSchema && !!inputs ? (
          <>
            {inputs.map((input, index) => (
              <SideBySideTableRow
                key={index}
                input={input}
                taskSchema={taskSchema}
                selectedLeftVersion={selectedLeftVersion}
                selectedRightVersion={selectedRightVersion}
                selectedRightModel={selectedRightModel}
                tenant={tenant}
                taskId={taskId}
                taskSchemaId={taskSchemaId}
              />
            ))}
          </>
        ) : (
          <div className='flex w-full h-[200px] items-center justify-center'>
            <Loader2 className='w-8 h-8 animate-spin text-gray-200' />
          </div>
        )}
      </div>
      {!selectedLeftVersionId && (
        <div className='absolute top-[20%] left-[20%] w-[40%] items-center flex justify-center text-gray-400 text-[13px] font-medium'>
          Choose a version to compare output results...
        </div>
      )}
      {!selectedRightVersionId && !selectedRightModelId && (
        <div className='absolute top-[20%] left-[60%] w-[40%] items-center flex justify-center text-gray-400 text-[13px] font-medium'>
          Choose a version or model to compare output results...
        </div>
      )}
    </div>
  );
}
