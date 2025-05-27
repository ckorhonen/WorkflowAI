import { Add16Regular } from '@fluentui/react-icons';
import { useCallback, useMemo, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { ProxyMessage, ProxyMessageContent } from '@/types/workflowAI';
import { ProxyFile } from './ProxyFile';
import { ProxyRemovableContent } from './ProxyRemovableContent';
import { ProxyTextarea } from './ProxyTextarea';
import { ProxyToolCallRequest } from './ProxyToolCallRequest';
import { ProxyToolCallResultView } from './ProxyToolCallResult';
import { createEmptyMessageContent } from './utils';

type Props = {
  message: ProxyMessage;
  setMessage?: (message: ProxyMessage | undefined) => void;
  supportToolCalls?: boolean;
};

export function ProxyMessageView(props: Props) {
  const { message, setMessage, supportToolCalls = true } = props;

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

  const isEditable = message.role === 'user' || message.role === 'assistant';

  const onMessageChange = useCallback(
    (index: number, content: ProxyMessageContent) => {
      if (!setMessage) {
        return;
      }
      const newMessage = {
        ...message,
        content: message.content.map((item, i) => (i === index ? content : item)),
      };
      setMessage(newMessage);
    },
    [message, setMessage]
  );

  const onAddContentEntry = useCallback(
    (type: 'text' | 'document' | 'image' | 'audio' | 'toolCallResult' | 'toolCallRequest') => {
      if (!setMessage) {
        return;
      }
      const newMessage = {
        ...message,
        content: [...message.content, createEmptyMessageContent(type)],
      };
      setMessage(newMessage);
    },
    [message, setMessage]
  );

  const onRemoveContentEntry = useCallback(
    (index: number) => {
      if (!setMessage) {
        return;
      }
      const newMessage = {
        ...message,
        content: message.content.filter((_, i) => i !== index),
      };
      setMessage(newMessage);
    },
    [message, setMessage]
  );

  const [isHovering, setIsHovering] = useState(false);

  const canModify = useMemo(() => {
    return !!setMessage;
  }, [setMessage]);

  return (
    <div className='relative' onMouseEnter={() => setIsHovering(true)} onMouseLeave={() => setIsHovering(false)}>
      <div
        className={cn(
          'flex flex-col border border-gray-200 rounded-[2px] min-h-[90px]',
          canModify && 'hover:border-gray-300 hover:shadow-md'
        )}
      >
        <div className='flex w-full px-4 text-[13px] text-gray-900 font-medium border-b border-gray-200 border-dashed justify-between items-center'>
          <div className='py-3'>{title}</div>
          {isHovering && canModify && (
            <Button variant='destructive' size='sm' onClick={() => setMessage?.(undefined)}>
              Remove Message
            </Button>
          )}
        </div>
        {message.content.map((content, index) => {
          return (
            <ProxyRemovableContent
              key={index}
              className='flex flex-col gap-2 last:border-b-0 border-b border-gray-200 border-dashed'
              isRemovable={!content.tool_call_request && !content.tool_call_result && canModify}
              onRemove={() => onRemoveContentEntry(index)}
            >
              {content.text !== undefined && (
                <div className='flex w-full px-4 py-3'>
                  <ProxyTextarea
                    key={index}
                    content={content}
                    setContent={(content) => onMessageChange(index, content)}
                    placeholder='Message text content'
                    readOnly={!canModify}
                  />
                </div>
              )}
              {content.file && (
                <div className='flex w-full px-4 py-3'>
                  <ProxyFile
                    content={content}
                    setContent={(content) => onMessageChange(index, content)}
                    readonly={!canModify}
                  />
                </div>
              )}
              {content.tool_call_request && (
                <div className='flex w-full px-4 py-3'>
                  <ProxyToolCallRequest
                    content={content}
                    setContent={(content) => onMessageChange(index, content)}
                    onRemove={() => onRemoveContentEntry(index)}
                    readonly={!canModify}
                  />
                </div>
              )}
              {content.tool_call_result && (
                <div className='flex w-full px-4 py-3'>
                  <ProxyToolCallResultView
                    result={content.tool_call_result}
                    setContent={(content) => onMessageChange(index, content)}
                    onRemove={() => onRemoveContentEntry(index)}
                    readonly={!canModify}
                  />
                </div>
              )}
            </ProxyRemovableContent>
          );
        })}
        {isHovering && isEditable && canModify && (
          <div className='flex w-full gap-1 px-4 py-2 items-center justify-start'>
            <Button variant='newDesign' size='sm' icon={<Add16Regular />} onClick={() => onAddContentEntry('text')}>
              Text
            </Button>
            {message.role === 'user' && (
              <>
                <Button
                  variant='newDesign'
                  size='sm'
                  icon={<Add16Regular />}
                  onClick={() => onAddContentEntry('document')}
                >
                  File
                </Button>
                <Button
                  variant='newDesign'
                  size='sm'
                  icon={<Add16Regular />}
                  onClick={() => onAddContentEntry('audio')}
                >
                  Audio
                </Button>
                {supportToolCalls && (
                  <div className='flex flex-row px-2 ml-1 border-l border-gray-200'>
                    <Button
                      variant='newDesign'
                      size='sm'
                      icon={<Add16Regular />}
                      onClick={() => onAddContentEntry('toolCallResult')}
                    >
                      Tool Call Result
                    </Button>
                  </div>
                )}
              </>
            )}
            {message.role === 'assistant' && supportToolCalls && (
              <div className='flex flex-row px-2 ml-1 border-l border-gray-200'>
                <Button
                  variant='newDesign'
                  size='sm'
                  icon={<Add16Regular />}
                  onClick={() => onAddContentEntry('toolCallRequest')}
                >
                  Tool Call Request
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
