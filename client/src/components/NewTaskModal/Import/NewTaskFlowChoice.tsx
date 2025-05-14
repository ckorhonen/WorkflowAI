import { Dismiss12Regular } from '@fluentui/react-icons';
import { useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { useRedirectWithParams } from '@/lib/queryString';
import { useIntegrationChat } from '@/store/integrations_messages';
import { Integration } from '@/types/workflowAI/models';
import { IntegrationCombobox } from './IntegrationCombobox';
import { NewTaskFlowChoiceSection } from './NewTaskFlowChoiceSection';

type NewTaskFlowChoiceProps = {
  integrationId: string | undefined;
  integrations: Integration[] | undefined;
  onClose: () => void;
};

export function NewTaskFlowChoice(props: NewTaskFlowChoiceProps) {
  const { integrationId, integrations, onClose } = props;

  const redirectWithParams = useRedirectWithParams();
  const { clean } = useIntegrationChat();

  const onCreateFeatureFlow = useCallback(() => {
    redirectWithParams({
      params: {
        flow: 'create',
        integrationId: undefined,
      },
    });
  }, [redirectWithParams]);

  const onImportFeatureFlow = useCallback(() => {
    if (!integrationId) {
      return;
    }

    clean();

    redirectWithParams({
      params: {
        flow: 'import',
        integrationId: integrationId,
      },
    });
  }, [redirectWithParams, integrationId, clean]);

  const setIntegrationId = useCallback(
    (integrationId: string | undefined) => {
      redirectWithParams({
        params: {
          integrationId,
        },
      });
    },
    [redirectWithParams]
  );

  return (
    <div className='flex flex-col h-full w-full overflow-hidden'>
      <div className='flex items-center px-4 justify-between h-[60px] flex-shrink-0'>
        <div className='flex items-center py-1.5 gap-4 text-gray-700 text-base font-medium font-lato'>
          <Button
            onClick={onClose}
            variant='newDesign'
            icon={<Dismiss12Regular className='w-3 h-3' />}
            className='w-7 h-7'
            size='none'
          />
          What would you like to create?
        </div>
      </div>
      <div className='flex w-full h-full border-t border-dashed border-gray-300'>
        <div className='flex flex-col w-1/2 h-full border-r border-gray-200'>
          <NewTaskFlowChoiceSection
            title='Create New AI Feature'
            subtitle='Build your AI feature directly in WorkflowAI—no coding required. Ideal for product managers, designers, and
            other low-code roles.'
            imageURL='https://workflowai.blob.core.windows.net/workflowai-public/createFlowIllustration.jpg'
          >
            <div className='flex justify-center w-full px-10 pb-10' onClick={onCreateFeatureFlow}>
              <Button variant='newDesignIndigo' className='w-full'>
                Create New AI Feature
              </Button>
            </div>
          </NewTaskFlowChoiceSection>
        </div>
        <div className='flex flex-col w-1/2 h-full'>
          <NewTaskFlowChoiceSection
            title='Import Existing Feature'
            subtitle='Import existing features built in code with your existing integrations. Great for developers.'
            imageURL='https://workflowai.blob.core.windows.net/workflowai-public/integrateFlowIllustration.jpg'
          >
            <div className='flex flex-col gap-4 justify-center w-full px-10 pb-10'>
              <div className='flex flex-col gap-2 p-4 border border-gray-200 rounded-[2px]'>
                <div className='text-[13px] font-medium text-gray-700'>Integration:</div>
                <IntegrationCombobox
                  integrations={integrations}
                  integrationId={integrationId}
                  setIntegrationId={setIntegrationId}
                />
              </div>
              <Button
                variant='newDesignIndigo'
                className='w-full'
                disabled={!integrationId}
                onClick={onImportFeatureFlow}
              >
                Import Existing Feature
              </Button>
            </div>
          </NewTaskFlowChoiceSection>
        </div>
      </div>
    </div>
  );
}
