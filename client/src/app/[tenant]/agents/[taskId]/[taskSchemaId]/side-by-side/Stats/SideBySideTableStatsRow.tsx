import { useMemo } from 'react';
import { hashInput } from '@/store/utils';
import { TaskID, TaskSchemaID, TenantID } from '@/types/aliases';
import { TaskInputDict, VersionV1 } from '@/types/workflowAI';
import { useSideBySideStatsEffect } from '../useSideBySideStatsEffect';
import { StatsAccuracy } from './StatsAccuracy';
import { StatsDeploy } from './StatsDeploy';
import { StatsInstructions } from './StatsInstructions';
import { StatsLatency } from './StatsLatency';
import { StatsPrice } from './StatsPrice';

type StatsRowProps = {
  title: string;
  leftChild?: React.ReactNode;
  rightChild?: React.ReactNode;
  hideRightSide?: boolean;
};

function StatsRow(props: StatsRowProps) {
  const { title, leftChild, rightChild, hideRightSide = false } = props;

  return (
    <div className='flex items-stretch w-full'>
      <div className='flex flex-col items-start justify-center w-[20%] border-r border-slate-200/60 h-11 px-4 bg-slate-100/60 border-b'>
        <div className='text-[12px] font-medium text-gray-700'>{title}</div>
      </div>
      <div className='flex flex-col items-start justify-center w-[40%] border-r border-slate-200/60 h-11 px-4 bg-slate-100/60 border-b'>
        {leftChild}
      </div>
      {hideRightSide ? (
        <div className='flex flex-col items-start justify-center w-[40%] h-11 px-4' />
      ) : (
        <div className='flex flex-col items-start justify-center w-[40%] h-11 px-4 bg-slate-100/60 border-b'>
          {rightChild}
        </div>
      )}
    </div>
  );
}

type SideBySideTableStatsRowProps = {
  tenant: TenantID | undefined;
  taskId: TaskID;
  taskSchemaId: TaskSchemaID;
  selectedLeftVersionId: string | undefined;
  selectedRightVersionId: string | undefined;
  selectedRightModelId: string | undefined;
  inputs: TaskInputDict[] | undefined;
  leftVersion: VersionV1 | undefined;
  rightVersion: VersionV1 | undefined;
};

export function SideBySideTableStatsRow(props: SideBySideTableStatsRowProps) {
  const {
    tenant,
    taskId,
    taskSchemaId,
    selectedLeftVersionId,
    selectedRightVersionId,
    selectedRightModelId,
    inputs,
    leftVersion,
    rightVersion,
  } = props;

  const inputHashes = useMemo(() => {
    return inputs?.map((input) => hashInput(input));
  }, [inputs]);

  const { left: leftStats, right: rightStats } = useSideBySideStatsEffect(
    tenant,
    taskId,
    taskSchemaId,
    inputHashes,
    selectedLeftVersionId,
    selectedRightVersionId,
    selectedRightModelId
  );

  const hideRightSide = !selectedRightModelId && !selectedRightVersionId;

  return (
    <div className='flex flex-col w-full border-t border-slate-200/20'>
      <StatsRow
        title='Accuracy'
        leftChild={
          <StatsAccuracy
            accuracy={leftStats.accuracy}
            bestAccuracy={leftStats.bestAccuracy}
            worstAccuracy={leftStats.worstAccuracy}
          />
        }
        rightChild={
          <StatsAccuracy
            accuracy={rightStats.accuracy}
            bestAccuracy={rightStats.bestAccuracy}
            worstAccuracy={rightStats.worstAccuracy}
          />
        }
        hideRightSide={hideRightSide}
      />
      <StatsRow
        title='Price'
        leftChild={<StatsPrice price={leftStats.averageCost} bestPrice={leftStats.minimalCost} />}
        rightChild={<StatsPrice price={rightStats.averageCost} bestPrice={rightStats.minimalCost} />}
        hideRightSide={hideRightSide}
      />
      <StatsRow
        title='Latency'
        leftChild={<StatsLatency latency={leftStats.averageDuration} bestLatency={leftStats.minimalDuration} />}
        rightChild={<StatsLatency latency={rightStats.averageDuration} bestLatency={rightStats.minimalDuration} />}
        hideRightSide={hideRightSide}
      />
      <StatsRow
        title='Version Instructions'
        leftChild={<StatsInstructions version={leftVersion} baseVersion={leftVersion} />}
        rightChild={<StatsInstructions version={rightVersion} baseVersion={leftVersion} />}
        hideRightSide={hideRightSide}
      />
      <StatsRow
        title='Deploy Status'
        leftChild={<StatsDeploy version={leftVersion} tenant={tenant} taskId={taskId} taskSchemaId={taskSchemaId} />}
        rightChild={
          <StatsDeploy
            version={rightVersion}
            tenant={tenant}
            taskId={taskId}
            taskSchemaId={taskSchemaId}
            baseVersion={leftVersion}
            modelId={selectedRightModelId}
          />
        }
        hideRightSide={hideRightSide}
      />
    </div>
  );
}
