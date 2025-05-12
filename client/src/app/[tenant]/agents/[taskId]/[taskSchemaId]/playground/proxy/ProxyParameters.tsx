import { Add16Regular } from '@fluentui/react-icons';
import { useCallback, useState } from 'react';
import { TemperatureSelector } from '@/components/TemperatureSelector/TemperatureSelector';
import { Button } from '@/components/ui/Button';
import { ToolKind, Tool_Output } from '@/types/workflowAI';
import { ProxySystemMessagesView } from './ProxySystemMessagesView';
import { ProxyTools } from './ProxyTools';
import { ProxyMessage, createEmptySystemMessage } from './utils';

type ProxyParametersProps = {
  systemMessages: ProxyMessage[];
  setSystemMessages: (systemMessages: ProxyMessage[]) => void;
  temperature: number;
  setTemperature: (temperature: number) => void;
  handleRunTasks: () => void;
  toolCalls: (ToolKind | Tool_Output)[] | undefined;
  setToolCalls: (toolCalls: (ToolKind | Tool_Output)[] | undefined) => void;
};

export function ProxyParameters(props: ProxyParametersProps) {
  const { systemMessages, setSystemMessages, temperature, setTemperature, handleRunTasks, toolCalls, setToolCalls } =
    props;

  const [isHovering, setIsHovering] = useState(false);

  const onAddSystemMessage = useCallback(() => {
    setSystemMessages([...systemMessages, createEmptySystemMessage()]);
  }, [systemMessages, setSystemMessages]);

  return (
    <div
      className='flex flex-col w-full h-full'
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <div className='flex flex-row h-[48px] w-full justify-between items-center shrink-0 border-b border-gray-200 border-dashed px-4'>
        <div className='flex w-full items-center font-semibold text-[16px] text-gray-700'>Parameters</div>
        {isHovering && (
          <Button variant='newDesign' size='sm' icon={<Add16Regular />} onClick={onAddSystemMessage}>
            Add System Message
          </Button>
        )}
      </div>
      <ProxySystemMessagesView systemMessages={systemMessages} setSystemMessages={setSystemMessages} />
      <div className='flex flex-col w-full border-t border-gray-200 border-dashed'>
        <div className='flex flex-col gap-1 px-4 pt-2'>
          <div className='flex w-full items-center font-medium text-[13px] text-gray-900'>Tools</div>
          <ProxyTools toolCalls={toolCalls} setToolCalls={setToolCalls} />
        </div>
        <div className='flex flex-col gap-1 px-4 pt-3 pb-3'>
          <div className='flex w-full items-center font-medium text-[13px] text-gray-900'>Temperature</div>
          <TemperatureSelector
            temperature={temperature}
            setTemperature={setTemperature}
            handleRunTasks={handleRunTasks}
          />
        </div>
      </div>
    </div>
  );
}
