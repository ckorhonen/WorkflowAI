import { Dismiss12Regular } from '@fluentui/react-icons';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { useTaskParams } from '@/lib/hooks/useTaskParams';
import { taskSideBySideRoute } from '@/lib/routeFormatter';

type ModelBannerProps = {
  // A tuple modelName, modelId
  models: [string, string][];
  onClose: (model: [string, string][]) => void;
  routeForSignUp?: string;
};

function ModelLink(props: { model: [string, string] }) {
  const { tenant, taskId, taskSchemaId } = useTaskParams();
  const {
    model: [modelName, modelId],
  } = props;

  const className = 'text-white text-[13px] font-medium underline';

  if (!taskId || !taskSchemaId) {
    return <span className={className}>{modelName}</span>;
  }

  const link = taskSideBySideRoute(tenant, taskId, taskSchemaId, { requestedRightModelId: modelId });

  return (
    <Link className={className} href={link}>
      {modelName}
    </Link>
  );
}

export function ModelBanner(props: ModelBannerProps) {
  const { models, onClose, routeForSignUp } = props;

  return (
    <div className='flex w-full h-9 bg-indigo-500 text-white justify-between items-center px-4 flex-shrink-0'>
      <div />
      <div className='flex flex-row gap-2 items-center'>
        <div className='font-semibold text-indigo-50 text-[12px] px-[6px] py-[2px] rounded-[2px] bg-indigo-400'>
          New model{models.length > 1 ? 's' : ''} available
        </div>

        {models.map((model, idx) => (
          <>
            <ModelLink key={model[1]} model={model} />
            {idx < models.length - 1 && <span> </span>}
          </>
        ))}
        {routeForSignUp && (
          <Link href={routeForSignUp} className='text-white text-[13px] font-medium underline'>
            Sign up to try
          </Link>
        )}
      </div>
      <Button
        onClick={() => onClose(models)}
        variant='default'
        icon={<Dismiss12Regular className='w-4 h-4' />}
        className='w-4 h-4 text-white hover:text-white/60 bg-transparent hover:bg-transparent'
        size='none'
      />
    </div>
  );
}
