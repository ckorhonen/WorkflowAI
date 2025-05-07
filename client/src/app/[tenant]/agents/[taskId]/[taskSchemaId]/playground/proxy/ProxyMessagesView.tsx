import { useCallback } from 'react';
import { ProxyMessageView } from './ProxyMessageView';
import { ProxyMessage } from './utils';

type Props = {
  messages: ProxyMessage[];
  setMessages: (messages: ProxyMessage[]) => void;
};

export function ProxyMessagesView(props: Props) {
  const { messages, setMessages } = props;

  const onMessageChange = useCallback(
    (message: ProxyMessage, index: number) => {
      const newMessages = messages.map((m, i) => (i === index ? message : m));
      setMessages(newMessages);
    },
    [messages, setMessages]
  );

  return (
    <div className='flex flex-col w-full h-full'>
      <div className='flex w-full items-center px-4 h-[48px] border-b border-gray-200 border-dashed font-semibold text-[16px] text-gray-700'>
        Messages
      </div>
      <div className='flex flex-col gap-2 px-4 py-4'>
        {messages.map((message, index) => (
          <ProxyMessageView key={index} message={message} setMessage={(message) => onMessageChange(message, index)} />
        ))}
      </div>
    </div>
  );
}
