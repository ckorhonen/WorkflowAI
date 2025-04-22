import { Dismiss12Regular } from '@fluentui/react-icons';
import Link from 'next/link';
import { useMemo } from 'react';
import { Button } from '@/components/ui/Button';
import { useTaskParams } from '@/lib/hooks/useTaskParams';
import { taskSideBySideRoute } from '@/lib/routeFormatter';

type ModelBannerProps = {
  model: string;
  modelId?: string;
  onClose: (model: string) => void;
  routeForSignUp?: string;
};

export function ModelBanner(props: ModelBannerProps) {
  const { model, modelId, onClose, routeForSignUp } = props;

  const { tenant, taskId, taskSchemaId } = useTaskParams();

  const tryItOutLink = useMemo(() => {
    if (!modelId || !taskId || !taskSchemaId) {
      return null;
    }

    return taskSideBySideRoute(tenant, taskId, taskSchemaId, { selectedRightModelId: modelId });
  }, [modelId, tenant, taskId, taskSchemaId]);

  return (
    <div className='flex w-full h-9 bg-indigo-500 text-white justify-between items-center px-4 flex-shrink-0'>
      <div />
      <div className='flex flex-row gap-2 items-center'>
        <div className='font-semibold text-indigo-50 text-[12px] px-[6px] py-[2px] rounded-[2px] bg-indigo-400'>
          New
        </div>
        <div className='text-white text-[13px] font-medium'>{model} available</div>
        {routeForSignUp && (
          <Link href={routeForSignUp} className='text-white text-[13px] font-medium underline'>
            Sign up to try
          </Link>
        )}
        {tryItOutLink && (
          <Link href={tryItOutLink} className='text-white text-[13px] font-medium underline'>
            Try it out
          </Link>
        )}
      </div>
      <Button
        onClick={() => onClose(model)}
        variant='default'
        icon={<Dismiss12Regular className='w-4 h-4' />}
        className='w-4 h-4 text-white hover:text-white/60 bg-transparent hover:bg-transparent'
        size='none'
      />
    </div>
  );
}
