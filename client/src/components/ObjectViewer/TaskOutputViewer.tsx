import isEmpty from 'lodash/isEmpty';
import { cn } from '@/lib/utils';
import { TaskOutput, ToolCallPreview } from '@/types';
import { ReasoningStep } from '@/types/workflowAI';
import { InternalReasoningSteps } from './InternalReasoningSteps';
import { ObjectViewer, ObjectViewerProps } from './ObjectViewer';

const OBJECT_VIEWER_BLACKLISTED_KEYS = new Set(['internal_reasoning_steps']);

type TaskOutputViewerProps = Omit<ObjectViewerProps, 'blacklistedKeys' | 'value'> & {
  value: TaskOutput | null | undefined;
  streamLoading?: boolean;
  toolCalls?: Array<ToolCallPreview>;
  reasoningSteps?: ReasoningStep[];
  defaultOpenForSteps?: boolean;
};

export function ObjectViewerPrefixSlot(props: {
  toolCalls: Array<ToolCallPreview> | undefined;
  reasoningSteps: ReasoningStep[] | undefined;
  streamLoading: boolean | undefined;
  defaultOpenForSteps?: boolean;
}) {
  const { streamLoading, toolCalls, reasoningSteps, defaultOpenForSteps } = props;

  if (isEmpty(reasoningSteps) && isEmpty(toolCalls)) {
    return null;
  }

  return (
    <InternalReasoningSteps
      steps={reasoningSteps}
      streamLoading={streamLoading}
      toolCalls={toolCalls}
      defaultOpen={defaultOpenForSteps}
    />
  );
}

export function TaskOutputViewer(props: TaskOutputViewerProps) {
  const { streamLoading, value, toolCalls: toolCallsPreview, reasoningSteps, defaultOpenForSteps, ...rest } = props;

  if (value === undefined && (rest.schema === undefined || rest.schema?.format === 'message') && !streamLoading) {
    return (
      <div className={cn('flex flex-col flex-1 w-full overflow-hidden', rest.className)}>
        <div className='flex flex-col flex-1 px-4 py-3 gap-1 overflow-hidden'>
          <div className='text-gray-700 text-[13px] font-medium'>{rest.schema?.format ?? 'message'}:</div>
          <div className='flex py-0.5 px-1.5 border border-gray-200 rounded-[2px] text-gray-700 text-[13px] font-medium w-fit'>
            {rest.schema?.type ?? 'string'}
          </div>
        </div>
      </div>
    );
  }

  return (
    <ObjectViewer
      blacklistedKeys={OBJECT_VIEWER_BLACKLISTED_KEYS}
      prefixSlot={
        <ObjectViewerPrefixSlot
          streamLoading={streamLoading}
          toolCalls={toolCallsPreview}
          reasoningSteps={reasoningSteps}
          defaultOpenForSteps={defaultOpenForSteps}
        />
      }
      value={value}
      {...rest}
    />
  );
}
