import { useCallback, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { ProxyMessage, ProxyMessageContent } from '@/types/workflowAI';
import { ProxyTextarea } from './ProxyTextarea';

type ProxySystemMessageViewProps = {
  systemMessage: ProxyMessage;
  setSystemMessage: (systemMessage: ProxyMessage | undefined) => void;
};

export function ProxySystemMessageView(props: ProxySystemMessageViewProps) {
  const { systemMessage, setSystemMessage } = props;

  const onSystemMessageChange = useCallback(
    (index: number, content: ProxyMessageContent) => {
      const newSystemMessage = systemMessage;
      const newContent = [...newSystemMessage.content];
      newContent[index] = content;
      setSystemMessage({ ...newSystemMessage, content: newContent });
    },
    [systemMessage, setSystemMessage]
  );

  const [isHovering, setIsHovering] = useState(false);

  return (
    <div
      className='flex flex-col w-full border border-gray-200 hover:border-gray-300 rounded-[2px] hover:shadow-md'
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <div className='flex w-full items-center flex-shrink-0 justify-between px-4 border-b border-gray-200 border-dashed'>
        <div className='flex w-full items-center font-medium text-[13px] text-gray-900 py-3'>System Message</div>
        {isHovering && (
          <Button variant='destructive' size='sm' onClick={() => setSystemMessage(undefined)}>
            Remove Message
          </Button>
        )}
      </div>
      <div className='flex flex-col gap-1 px-4 py-3'>
        {systemMessage?.content.map((content, index) => (
          <ProxyTextarea
            key={index}
            content={content}
            setContent={(content) => onSystemMessageChange(index, content)}
            placeholder='System message content'
            minHeight={80}
          />
        ))}
      </div>
    </div>
  );
}
