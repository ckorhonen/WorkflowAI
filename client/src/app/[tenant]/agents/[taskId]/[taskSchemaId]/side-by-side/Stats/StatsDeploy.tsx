import { useCallback } from 'react';
import { useDeployVersionModal } from '@/components/DeployIterationModal/DeployVersionModal';
import { TaskEnvironmentBadge } from '@/components/TaskEnvironmentBadge';
import { Button } from '@/components/ui/Button';
import { useRedirectWithParams } from '@/lib/queryString';
import { environmentsForVersion } from '@/lib/versionUtils';
import { useVersions } from '@/store/versions';
import { TaskID, TaskSchemaID, TenantID } from '@/types/aliases';
import { VersionV1 } from '@/types/workflowAI';

type SaveVersionDeployStatusProps = {
  tenant: TenantID | undefined;
  taskId: TaskID;
  taskSchemaId: TaskSchemaID;
  baseVersion: VersionV1;
  modelId: string;
};

function SaveVersionDeployStatus(props: SaveVersionDeployStatusProps) {
  const { baseVersion, modelId, tenant, taskId, taskSchemaId } = props;

  const createVersion = useVersions((state) => state.createVersion);
  const saveVersion = useVersions((state) => state.saveVersion);
  const redirectWithParams = useRedirectWithParams();

  const saveAndDeployVersion = useCallback(
    async (baseVersion: VersionV1, modelId: string) => {
      const body = {
        properties: {
          ...baseVersion.properties,
          model: modelId,
        },
        save: false,
      };

      try {
        const version = await createVersion(tenant, taskId, taskSchemaId, body);
        await saveVersion(tenant, taskId, version.id);

        redirectWithParams({
          params: {
            selectedRightModelId: undefined,
            selectedRightVersionId: version.id,
            deployVersionId: version.id,
            deploySchemaId: taskSchemaId,
            deployIterationModalOpen: 'true',
          },
        });
      } catch (error) {
        console.error(error);
      }
    },
    [createVersion, tenant, taskId, taskSchemaId, saveVersion, redirectWithParams]
  );

  return (
    <div className='flex items-center justify-start w-full h-full'>
      <Button variant='newDesign' size='sm' onClick={() => saveAndDeployVersion(baseVersion, modelId)}>
        Deploy
      </Button>
    </div>
  );
}

type ClassicDeployStatusProps = {
  version: VersionV1;
};

function ClassicDeployStatus(props: ClassicDeployStatusProps) {
  const { version } = props;
  const environments = environmentsForVersion(version);

  const { onDeployToClick } = useDeployVersionModal();

  if (environments && environments.length > 0) {
    return (
      <div className='flex items-center gap-2 justify-start w-full h-full'>
        {environments.map((environment) => (
          <TaskEnvironmentBadge key={environment} environment={environment} />
        ))}
        <div className='text-gray-700 text-[13px] py-[2px] px-[6px] rounded-[2px] bg-gray-200'>
          #{version.schema_id}
        </div>
      </div>
    );
  }

  return (
    <div className='flex items-center justify-start w-full h-full'>
      <Button
        variant='newDesign'
        size='sm'
        onClick={() => onDeployToClick(version.id, `${version.schema_id}` as TaskSchemaID, false)}
      >
        Deploy
      </Button>
    </div>
  );
}

type StatsDeployProps = {
  version: VersionV1 | undefined;
  baseVersion?: VersionV1;
  modelId?: string;
  tenant: TenantID | undefined;
  taskId: TaskID;
  taskSchemaId: TaskSchemaID;
};

export function StatsDeploy(props: StatsDeployProps) {
  const { version, baseVersion, modelId, tenant, taskId, taskSchemaId } = props;

  if (!!version) {
    return <ClassicDeployStatus version={version} />;
  }

  if (!!baseVersion && !!modelId) {
    return (
      <SaveVersionDeployStatus
        baseVersion={baseVersion}
        modelId={modelId}
        tenant={tenant}
        taskId={taskId}
        taskSchemaId={taskSchemaId}
      />
    );
  }

  return <div className='flex items-center justify-start w-full h-full text-gray-500 text-[13px]'>-</div>;
}
