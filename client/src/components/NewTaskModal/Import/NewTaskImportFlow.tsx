import { ClockArrowDownload20Regular, Dismiss12Regular } from '@fluentui/react-icons';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { taskSchemaRoute } from '@/lib/routeFormatter';
import { useOrFetchIntegrationChat } from '@/store/integrations_messages';
import { TaskID, TaskSchemaID, TenantID } from '@/types/aliases';
import { Integration } from '@/types/workflowAI/models';
import { TaskConversationMessages } from '../TaskConversation';
import { TaskConversationInput } from '../TaskConversation';
import { ConversationMessage } from '../TaskConversationMessage';

type NewTaskFlowChoiceProps = {
  tenant: TenantID | undefined;
  integrationId: string | undefined;
  integrations: Integration[] | undefined;
  onClose: () => void;
};

export function NewTaskImportFlow(props: NewTaskFlowChoiceProps) {
  const { tenant, integrationId, integrations, onClose } = props;

  const integration = useMemo(() => {
    if (!integrationId) {
      return undefined;
    }
    return integrations?.find((integration) => integration.id === integrationId);
  }, [integrationId, integrations]);

  const router = useRouter();

  const { messages, isLoading, sendMessage, redirectToAgentPlayground } = useOrFetchIntegrationChat(integration?.id);

  useEffect(() => {
    const taskId = (redirectToAgentPlayground?.task_id ??
      redirectToAgentPlayground?.agent_name?.toLowerCase()) as TaskID;

    const taskSchemaId = (redirectToAgentPlayground?.task_schema_id ?? '1') as TaskSchemaID;

    if (!!taskId && !!taskSchemaId) {
      router.push(taskSchemaRoute(tenant, taskId, taskSchemaId));
    }
  }, [redirectToAgentPlayground, router, tenant]);

  const convertedMessages: ConversationMessage[] = useMemo(() => {
    const result: ConversationMessage[] = [];

    messages?.forEach((message, index) => {
      let component: React.ReactNode | undefined;
      const username = message.role === 'USER' ? 'You' : 'WorkflowAI';

      result.push({
        message: message.content,
        username: username,
        streamed: message.role === 'ASSISTANT' && index === messages.length - 1 && isLoading,
        component: component,
      });
    });

    return result;
  }, [messages, isLoading]);

  const [userMessage, setUserMessage] = useState('');

  const onSendMessage = useCallback(async () => {
    if (userMessage) {
      const message = userMessage;
      setUserMessage('');
      await sendMessage(message);
    }
  }, [sendMessage, userMessage]);

  return (
    <div className='flex flex-col h-full w-full overflow-hidden'>
      <div className='flex items-center px-4 justify-between h-[60px] flex-shrink-0'>
        <div className='flex items-center py-1.5 gap-4 text-gray-900 text-[16px] font-semibold'>
          <Button
            onClick={onClose}
            variant='newDesign'
            icon={<Dismiss12Regular className='w-3 h-3' />}
            className='w-7 h-7'
            size='none'
          />
          {integration?.display_name} + WorkflowAI Set up
        </div>

        <div className='flex items-center gap-3'>
          <div className='flex gap-1 items-center text-gray-500 text-[12px] font-normal'>
            <ClockArrowDownload20Regular className='w-4.5 h-4.5 text-gray-500' />
            <div>Waiting for the first run to appear...</div>
          </div>
          <Button variant='newDesignIndigo' disabled={true}>
            Next
          </Button>
        </div>
      </div>
      <div className='flex flex-col w-full h-full border-t border-dashed border-gray-300 overflow-hidden'>
        <TaskConversationMessages
          messages={convertedMessages}
          loading={isLoading}
          showRetry={false}
          retry={() => {}}
          className='pt-[6px]'
        />
        <TaskConversationInput
          setUserMessage={setUserMessage}
          onSendIteration={onSendMessage}
          userMessage={userMessage}
          autoFocus={true}
        />
      </div>
    </div>
  );
}
