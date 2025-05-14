import { TaskOutputViewer } from '@/components/ObjectViewer/TaskOutputViewer';
import { cn } from '@/lib/utils';
import { JsonSchema, ToolCallPreview } from '@/types';
import { TaskOutput } from '@/types/task_run';
import { ReasoningStep } from '@/types/workflowAI';

type ProxyOutputViewerProps = {
  taskOutput: TaskOutput | undefined;
  toolCalls: ToolCallPreview[] | undefined;
  reasoningSteps: ReasoningStep[] | undefined;
  streamLoading: boolean;
  outputSchema: JsonSchema | undefined;
  referenceValue: Record<string, unknown> | undefined;
  emptyMode: boolean;
};

export function ProxyOutputViewer(props: ProxyOutputViewerProps) {
  const { taskOutput, toolCalls, reasoningSteps, streamLoading, outputSchema, referenceValue, emptyMode } = props;

  if (taskOutput === undefined && (outputSchema === undefined || outputSchema.format === 'message')) {
    return (
      <div className='flex flex-col flex-1 w-full bg-white border-b border-gray-200 border-dashed overflow-hidden'>
        <div className='flex flex-col flex-1 px-4 py-3 gap-1 overflow-hidden'>
          <div className='text-gray-700 text-[13px] font-medium'>{outputSchema?.format ?? 'message'}:</div>
          <div className='flex py-0.5 px-1.5 border border-gray-200 rounded-[2px] text-gray-700 text-[13px] font-medium w-fit'>
            {outputSchema?.type ?? 'string'}
          </div>
        </div>
      </div>
    );
  }

  return (
    <TaskOutputViewer
      schema={outputSchema}
      value={taskOutput}
      referenceValue={referenceValue}
      defs={outputSchema?.$defs}
      textColor='text-gray-900'
      className={cn(
        'flex sm:flex-1 w-full border-b border-gray-200 border-dashed bg-white sm:overflow-y-scroll',
        !!taskOutput && 'min-h-[150px]'
      )}
      showTypes={emptyMode}
      showExamplesHints
      onShowEditDescriptionModal={undefined}
      streamLoading={streamLoading}
      toolCalls={toolCalls}
      reasoningSteps={reasoningSteps}
      showDescriptionExamples={undefined}
    />
  );
}
