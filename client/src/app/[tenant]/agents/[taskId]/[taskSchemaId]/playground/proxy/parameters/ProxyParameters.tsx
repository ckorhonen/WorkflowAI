import { useCallback, useState } from 'react';
import { TemperatureSelector } from '@/components/TemperatureSelector/TemperatureSelector';
import { ToolKind, Tool_Output } from '@/types/workflowAI';
import { ProxyTools } from '../ProxyTools';
import { ProxyMessage, createEmptySystemMessage, createEmptyUserMessage } from '../utils';
import { ProxyAddMessageButton } from './ProxyAddMessageButton';
import { ProxyParametersMessagesView } from './ProxyParametersMessagesView';

type ProxyParametersProps = {
  messages: ProxyMessage[];
  setMessages: (messages: ProxyMessage[]) => void;
  temperature: number;
  setTemperature: (temperature: number) => void;
  handleRunTasks: () => void;
  toolCalls: (ToolKind | Tool_Output)[] | undefined;
  setToolCalls: (toolCalls: (ToolKind | Tool_Output)[] | undefined) => void;
  supportOnlySystemMessages: boolean;
};

export function ProxyParameters(props: ProxyParametersProps) {
  const {
    messages,
    setMessages,
    temperature,
    setTemperature,
    handleRunTasks,
    toolCalls,
    setToolCalls,
    supportOnlySystemMessages,
  } = props;

  const [isHovering, setIsHovering] = useState(false);

  const onAddSystemMessage = useCallback(() => {
    setMessages([...messages, createEmptySystemMessage()]);
  }, [messages, setMessages]);

  const addUserMessage = useCallback(() => {
    setMessages([...messages, createEmptyUserMessage('text')]);
  }, [messages, setMessages]);

  return (
    <div
      className='flex flex-col w-full h-full'
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <div className='flex flex-row h-[48px] w-full justify-between items-center shrink-0 border-b border-gray-200 border-dashed px-4'>
        <div className='flex w-full items-center font-semibold text-[16px] text-gray-700'>Parameters</div>
        <ProxyAddMessageButton
          isHovering={isHovering}
          addSystemMessage={onAddSystemMessage}
          addUserMessage={addUserMessage}
          supportOnlySystemMessages={supportOnlySystemMessages}
        />
      </div>
      <ProxyParametersMessagesView messages={messages} setMessages={setMessages} />
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
