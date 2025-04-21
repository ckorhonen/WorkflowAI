import { Dismiss12Regular } from '@fluentui/react-icons';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

type ModelBannerProps = {
  model: string;
  onClose: (model: string) => void;
  routeForSignUp?: string;
};

export function ModelBanner(props: ModelBannerProps) {
  const { model, onClose, routeForSignUp } = props;

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
