import { useCallback, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { TaskInputDict, TaskOutputDict } from '@/types/workflowAI';
import { ProxyMessage } from './utils';

type Props = {
  input: TaskInputDict;
  output: TaskOutputDict;
  updateInputAndRun: (input: TaskInputDict) => void;
};

export function ProxyReplyView(props: Props) {
  const { input, output, updateInputAndRun } = props;
  const [text, setText] = useState('');

  const onSendMessage = useCallback(() => {
    const taskInput = input as Record<string, unknown>;
    const oldMessages = taskInput.messages as ProxyMessage[];

    const messages = [...oldMessages];

    const assistantText = JSON.stringify(output);

    const assistantMessage: ProxyMessage = {
      role: 'assistant',
      content: [
        {
          text: assistantText,
        },
      ],
    };
    messages.push(assistantMessage);

    const newMessage: ProxyMessage = {
      role: 'user',
      content: [
        {
          text: text,
        },
      ],
    };

    messages.push(newMessage);

    const updatedInput: TaskInputDict = { ...input, messages };
    updateInputAndRun(updatedInput);
  }, [input, text, output, updateInputAndRun]);

  return (
    <div className='flex flex-col w-full px-4 py-2 gap-2.5'>
      <Textarea
        className='flex w-full text-gray-900 placeholder:text-gray-500 font-normal text-[13px] rounded-[2px] border-gray-300 overflow-y-auto focus-within:ring-inset'
        placeholder={'User Message'}
        value={text}
        onChange={(e) => setText(e.target.value)}
        autoFocus
      />
      <div className='flex flex-row w-full justify-between items-center'>
        <Button variant='newDesign' size='sm' onClick={onSendMessage} disabled={!text}>
          Send
        </Button>
        <div className='text-[12px] text-gray-500'>Will be send to all models</div>
      </div>
    </div>
  );
}
