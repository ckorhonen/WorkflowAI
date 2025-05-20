import { useCallback } from 'react';
import { ProxyMessage } from '@/types/workflowAI';
import { ProxyMessageView } from '../ProxyMessageView';
import { ProxySystemMessageView } from '../ProxySystemMessageView';

type Props = {
  messages: ProxyMessage[];
  setMessages: (messages: ProxyMessage[]) => void;
};

export function ProxyParametersMessagesView(props: Props) {
  const { messages, setMessages } = props;

  const onUpdateMessage = useCallback(
    (index: number, message: ProxyMessage | undefined) => {
      if (message) {
        const newMessages = messages.map((m, i) => (i === index ? message : m));
        setMessages(newMessages);
      } else {
        const newMessages = messages.filter((_, i) => i !== index);
        setMessages(newMessages);
      }
    },
    [messages, setMessages]
  );

  return (
    <div className='flex flex-col gap-2 px-4 pt-4 pb-4 flex-1 overflow-y-auto'>
      {messages.map((message, index) => {
        if (message.role === 'system') {
          return (
            <ProxySystemMessageView
              key={index}
              systemMessage={message}
              setSystemMessage={(systemMessage) => onUpdateMessage(index, systemMessage)}
            />
          );
        }
        return (
          <ProxyMessageView
            key={index}
            message={message}
            setMessage={(message) => onUpdateMessage(index, message)}
            supportToolCalls={false}
          />
        );
      })}
    </div>
  );
}
