import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { GeneralizedTaskInput } from '@/types/task_run';
import { ToolKind, Tool_Output } from '@/types/workflowAI';
import { ProxyMessagesView } from './ProxyMessagesView';
import { ProxyParameters } from './ProxyParameters';
import { ProxyMessage, createEmptySystemMessage, createEmptyUserMessage } from './utils';

interface Props {
  input: GeneralizedTaskInput | undefined;
  setInput: (input: GeneralizedTaskInput) => void;
  temperature: number;
  setTemperature: (temperature: number) => void;
  handleRunTasks: () => void;
  toolCalls: (ToolKind | Tool_Output)[] | undefined;
  setToolCalls: (toolCalls: (ToolKind | Tool_Output)[] | undefined) => void;
  maxHeight: number | undefined;
}
const areMessagesEqual = (prev: ProxyMessage[], next: ProxyMessage[]) => {
  return JSON.stringify(prev) === JSON.stringify(next);
};

export function ProxyInput(props: Props) {
  const { input, setInput, temperature, setTemperature, handleRunTasks, toolCalls, setToolCalls, maxHeight } = props;

  const [systemMessages, setSystemMessages] = useState<ProxyMessage[]>([createEmptySystemMessage()]);
  const [otherMessages, setOtherMessages] = useState<ProxyMessage[]>([createEmptyUserMessage()]);

  const systemMessagesRef = useRef(systemMessages);
  systemMessagesRef.current = systemMessages;

  const otherMessagesRef = useRef(otherMessages);
  otherMessagesRef.current = otherMessages;

  const { newSystemMessages, newOtherMessages } = useMemo(() => {
    if (!input || !('messages' in input)) {
      return { newSystemMessages: [], newOtherMessages: [] };
    }

    const taskInput = input as Record<string, unknown>;
    const messages = taskInput?.messages as ProxyMessage[];

    return {
      newSystemMessages: messages.filter((message) => message.role === 'system'),
      newOtherMessages: messages.filter((message) => message.role !== 'system'),
    };
  }, [input]);

  useEffect(() => {
    setSystemMessages((prev) => {
      if (!areMessagesEqual(prev, newSystemMessages)) {
        return newSystemMessages;
      }
      return prev;
    });
  }, [newSystemMessages]);

  useEffect(() => {
    setOtherMessages((prev) => {
      if (!areMessagesEqual(prev, newOtherMessages)) {
        return newOtherMessages;
      }
      return prev;
    });
  }, [newOtherMessages]);

  const onUpdateInput = useCallback(
    (systemMessages: ProxyMessage[], otherMessages: ProxyMessage[]) => {
      const messages = [...systemMessages, ...otherMessages];
      const taskInput = {
        messages,
      };

      setSystemMessages(systemMessages);
      setOtherMessages(otherMessages);
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
          messages={otherMessages}
          setMessages={(messages) => onUpdateInput(systemMessages, messages)}
        />
      </div>
      <div className='w-1/2'>
        <ProxyParameters
          systemMessages={systemMessages}
          setSystemMessages={(messages) => onUpdateInput(messages, otherMessages)}
          temperature={temperature}
          setTemperature={setTemperature}
          handleRunTasks={handleRunTasks}
          toolCalls={toolCalls}
          setToolCalls={setToolCalls}
        />
      </div>
    </div>
  );
}
