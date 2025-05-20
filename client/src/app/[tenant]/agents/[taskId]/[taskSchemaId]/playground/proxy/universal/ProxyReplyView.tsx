import { nanoid } from 'nanoid';
import { useCallback, useMemo, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { JsonSchema } from '@/types/json_schema';
import { ToolCallPreview } from '@/types/task_run';
import { TaskInputDict, TaskOutputDict, ToolCallRequestWithID } from '@/types/workflowAI';
import { ProxyMessage, ProxyMessageContent } from '@/types/workflowAI';
import { checkInputSchemaForInputVaribles } from '../hooks/useIsProxy';
import { cleanMessageContent } from '../utils';
import { ProxyMessageView } from './ProxyMessageView';

type Props = {
  input: TaskInputDict;
  output: TaskOutputDict;
  inputSchema: JsonSchema | undefined;
  toolCalls: ToolCallPreview[] | undefined;
  updateInputAndRun: (input: TaskInputDict) => Promise<void>;
};

export function ProxyReplyView(props: Props) {
  const { input, output, toolCalls, updateInputAndRun, inputSchema } = props;
  const [toolCallResultText, setToolCallResultText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const toolCallRequest: ToolCallRequestWithID | undefined = useMemo(() => {
    if (!toolCalls || toolCalls.length === 0) {
      return undefined;
    }

    const toolCallPreview = toolCalls[0];

    try {
      return {
        tool_name: toolCallPreview.name,
        tool_input_dict: JSON.parse(toolCallPreview.input_preview),
        id: toolCallPreview.id,
      };
    } catch {
      return undefined;
    }
  }, [toolCalls]);

  const keyForMessage = useMemo(() => {
    if (!inputSchema) {
      return 'workflowai.replies';
    }

    if (checkInputSchemaForInputVaribles(inputSchema)) {
      return 'workflowai.replies';
    } else {
      return 'messages';
    }
  }, [inputSchema]);

  const blankMessage: ProxyMessage = useMemo(() => {
    return {
      role: 'user',
      content: [
        {
          text: '',
        },
      ],
    };
  }, []);

  const [userMessage, setUserMessage] = useState<ProxyMessage>(blankMessage);

  const onSendMessage = useCallback(async () => {
    const taskInput = input as Record<string, unknown>;
    const oldMessages: ProxyMessage[] = (taskInput[keyForMessage] as ProxyMessage[]) ?? [];

    const messages = [...oldMessages];

    const assistantText = JSON.stringify(output);

    const requestContent: ProxyMessageContent[] = [];

    if (toolCallRequest) {
      requestContent.push({
        tool_call_request: toolCallRequest,
      });
    }

    if (!!assistantText && assistantText !== '{}') {
      requestContent.push({
        text: assistantText,
      });
    }

    const assistantMessage: ProxyMessage = {
      role: 'assistant',
      content: requestContent,
    };

    messages.push(assistantMessage);

    let responseContent: ProxyMessageContent[] = [];

    if (toolCallRequest && !!toolCallResultText) {
      responseContent.push({
        tool_call_result: {
          id: toolCallRequest?.id ?? nanoid(),
          result: toolCallResultText,
          tool_name: toolCallRequest?.tool_name,
          tool_input_dict: toolCallRequest?.tool_input_dict,
        },
      });
    }

    if (!toolCallRequest) {
      responseContent = userMessage.content;
    }

    const newMessage: ProxyMessage = {
      role: 'user',
      content: responseContent,
    };

    messages.push(newMessage);

    const updatedInput: TaskInputDict = { ...input, [keyForMessage]: messages };

    setToolCallResultText('');
    setIsLoading(true);
    await updateInputAndRun(updatedInput);
    setIsLoading(false);
  }, [input, toolCallResultText, output, updateInputAndRun, toolCallRequest, keyForMessage, userMessage]);

  const handleSetMessage = useCallback(
    (message: ProxyMessage | undefined) => {
      if (!message || message.content.length === 0) {
        setUserMessage(blankMessage);
        return;
      }

      setUserMessage({
        ...message,
        content: cleanMessageContent(message.content),
      });
    },
    [blankMessage]
  );

  if (!!toolCallRequest) {
    return (
      <div className='flex flex-col w-full px-4 py-2 gap-2.5'>
        <Textarea
          className='flex w-full text-gray-900 placeholder:text-gray-500 font-normal text-[13px] rounded-[2px] border-gray-300 overflow-y-auto focus-within:ring-inset'
          placeholder={'Tool Call Result'}
          value={toolCallResultText}
          onChange={(e) => setToolCallResultText(e.target.value)}
          autoFocus
          disabled={isLoading}
        />
        <div className='flex flex-row w-full justify-between items-center'>
          <div className='flex flex-row gap-2 items-center'>
            <Button variant='newDesign' size='sm' onClick={onSendMessage} disabled={!toolCallResultText}>
              Send Tool Call Result
            </Button>
          </div>
          <div className='text-[12px] text-gray-500'>Will be sent to all models</div>
        </div>
      </div>
    );
  }

  return (
    <div className='flex flex-col w-full px-4 py-2 gap-2.5'>
      <ProxyMessageView
        message={userMessage}
        avaibleTypes={['user']}
        setMessage={handleSetMessage}
        oneMessageMode={true}
      />
      <div className='flex flex-row w-full justify-between items-center'>
        <div className='flex flex-row gap-2 items-center'>
          <Button variant='newDesign' size='sm' onClick={onSendMessage}>
            Send
          </Button>
        </div>
        <div className='text-[12px] text-gray-500'>Will be sent to all models</div>
      </div>
    </div>
  );
}
