import { useCallback, useMemo } from 'react';
import { ProxyFile } from './ProxyFile';
import { ProxyTextarea } from './ProxyTextarea';
import { ProxyMessage, ProxyMessageContent } from './utils';

type Props = {
  message: ProxyMessage;
  setMessage: (message: ProxyMessage) => void;
};

export function ProxyMessageView(props: Props) {
  const { message, setMessage } = props;

  const title = useMemo(() => {
    switch (message.role) {
      case 'user':
        return 'User Message';
      case 'assistant':
        return 'Assistant Message';
      case 'system':
        return 'System Message';
    }
  }, [message.role]);

  const onMessageChange = useCallback(
    (index: number, content: ProxyMessageContent) => {
      const newMessage = {
        ...message,
        content: message.content.map((item, i) => (i === index ? content : item)),
      };
      setMessage(newMessage);
    },
    [message, setMessage]
  );

  return (
    <div className='flex flex-col border border-gray-200 rounded-[2px]'>
      <div className='flex w-full px-4 py-2 text-[13px] text-gray-900 font-medium border-b border-gray-200 border-dashed'>
        {title}
      </div>
      {message.content.map((content, index) => (
        <div key={index} className='flex flex-col gap-2'>
          {content.text && (
            <div className='flex w-full px-4 py-3 last:border-b-0 border-b border-gray-200 border-dashed'>
              <ProxyTextarea
                key={index}
                content={content}
                setContent={(content) => onMessageChange(index, content)}
                placeholder='Message text content'
              />
            </div>
          )}
          {content.file && (
            <div className='flex w-full px-4 py-3 last:border-b-0 border-b border-gray-200 border-dashed'>
              <ProxyFile content={content} setContent={(content) => onMessageChange(index, content)} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
