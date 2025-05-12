import { useCallback } from 'react';
import { ProxySystemMessageView } from './ProxySystemMessageView';
import { ProxyMessage } from './utils';

type ProxySystemMessagesViewProps = {
  systemMessages: ProxyMessage[];
  setSystemMessages: (systemMessages: ProxyMessage[]) => void;
};

export function ProxySystemMessagesView(props: ProxySystemMessagesViewProps) {
  const { systemMessages, setSystemMessages } = props;

  const onUpdateSystemMessage = useCallback(
    (index: number, systemMessage: ProxyMessage | undefined) => {
      if (systemMessage) {
        const newSystemMessages = systemMessages.map((m, i) => (i === index ? systemMessage : m));
        setSystemMessages(newSystemMessages);
      } else {
        const newSystemMessages = systemMessages.filter((_, i) => i !== index);
        setSystemMessages(newSystemMessages);
      }
    },
    [systemMessages, setSystemMessages]
  );

  return (
    <div className='flex flex-col gap-2 px-4 pt-4 pb-4 flex-1 overflow-y-auto'>
      {systemMessages.map((systemMessage, index) => (
        <ProxySystemMessageView
          key={index}
          systemMessage={systemMessage}
          setSystemMessage={(systemMessage) => onUpdateSystemMessage(index, systemMessage)}
        />
      ))}
    </div>
  );
}
