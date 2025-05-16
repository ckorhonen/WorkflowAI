import { ProxyMessage } from '@/types/workflowAI';
import { ProxyMessageView } from './ProxyMessageView';

type ProxyReadonlyMessagesProps = {
  messages: ProxyMessage[];
};

export function ProxyReadonlyMessages(props: ProxyReadonlyMessagesProps) {
  const { messages } = props;

  return (
    <div className='flex flex-col w-full gap-4 py-1'>
      {messages.map((message, index) => (
        <ProxyMessageView key={index} message={message} />
      ))}
    </div>
  );
}
