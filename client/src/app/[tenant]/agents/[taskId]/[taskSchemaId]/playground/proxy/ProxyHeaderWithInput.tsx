import { useCallback, useMemo } from 'react';
import { TenantID } from '@/types/aliases';
import { TaskID } from '@/types/aliases';
import { JsonSchema } from '@/types/json_schema';
import { GeneralizedTaskInput } from '@/types/task_run';
import { ToolKind, Tool_Output } from '@/types/workflowAI';
import { ProxyMessagesView } from './ProxyMessagesView';
import { ProxyParameters } from './parameters/ProxyParameters';
import { ProxyMessage } from './utils';

interface Props {
  inputSchema: JsonSchema | undefined;
  input: GeneralizedTaskInput | undefined;
  setInput: (input: GeneralizedTaskInput) => void;
  temperature: number;
  setTemperature: (temperature: number) => void;
  handleRunTasks: () => void;
  toolCalls: (ToolKind | Tool_Output)[] | undefined;
  setToolCalls: (toolCalls: (ToolKind | Tool_Output)[] | undefined) => void;
  maxHeight: number | undefined;
  proxyMessages: ProxyMessage[] | undefined;
  setProxyMessages: (proxyMessages: ProxyMessage[] | undefined) => void;
  tenant: TenantID | undefined;
  taskId: TaskID;
}

export function ProxyHeaderWithInput(props: Props) {
  const {
    inputSchema,
    input,
    setInput,
    temperature,
    setTemperature,
    handleRunTasks,
    toolCalls,
    setToolCalls,
    maxHeight,
    proxyMessages,
    setProxyMessages,
    tenant,
    taskId,
  } = props;

  const { inputMessages, cleanInput } = useMemo(() => {
    if (!input || !('workflowai.replies' in input)) {
      return { inputMessages: [], cleanInput: input as Record<string, unknown> };
    }

    const taskInput = input as Record<string, unknown>;
    const messages = taskInput['workflowai.replies'] as ProxyMessage[];

    const cleanTaskInput = {
      ...taskInput,
    };
    delete cleanTaskInput['workflowai.replies'];

    return {
      inputMessages: messages || [],
      cleanInput: cleanTaskInput,
    };
  }, [input]);

  const onUpdateInput = useCallback(
    (inputMessages: ProxyMessage[], cleanInput: Record<string, unknown>) => {
      const taskInput = {
        'workflowai.replies': inputMessages,
        ...cleanInput,
      };

      setInput(taskInput as GeneralizedTaskInput);
    },
    [setInput]
  );

  return (
    <div
      className='flex w-full items-stretch border-b border-gray-200 border-dashed overflow-hidden'
      style={{ maxHeight }}
    >
      <div className='w-1/2 border-r border-gray-200 border-dashed overflow-hidden'>
        <ProxyMessagesView
          tenant={tenant}
          taskId={taskId}
          title='Input'
          messages={inputMessages}
          setMessages={(messages) => onUpdateInput(messages, cleanInput)}
          inputSchema={inputSchema}
          input={cleanInput}
          setInput={(input) => onUpdateInput(inputMessages, input)}
        />
      </div>
      <div className='w-1/2'>
        <ProxyParameters
          messages={proxyMessages || []}
          setMessages={setProxyMessages}
          temperature={temperature}
          setTemperature={setTemperature}
          handleRunTasks={handleRunTasks}
          toolCalls={toolCalls}
          setToolCalls={setToolCalls}
          supportOnlySystemMessages={false}
        />
      </div>
    </div>
  );
}
