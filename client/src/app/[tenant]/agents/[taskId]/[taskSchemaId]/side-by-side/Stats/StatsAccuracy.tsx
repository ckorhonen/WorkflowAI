import { cn } from '@/lib/utils';

type StatsAccuracyProps = {
  accuracy: number | undefined;
  bestAccuracy: number | undefined;
  worstAccuracy: number | undefined;
};

export function StatsAccuracy(props: StatsAccuracyProps) {
  const { accuracy, bestAccuracy, worstAccuracy } = props;

  const isBest = accuracy === bestAccuracy;
  const text = accuracy ? `${Math.ceil(accuracy * 100)}%` : '-';
  const betterText =
    isBest && worstAccuracy && bestAccuracy && bestAccuracy !== worstAccuracy
      ? `${(bestAccuracy / worstAccuracy).toFixed(1)}x better`
      : undefined;

  if (!accuracy) {
    return <div className='flex items-center justify-start w-full h-full text-gray-500 text-[16px]'>-</div>;
  }

  return (
    <div className='flex items-center justify-start w-full h-full text-gray-500 text-[13px]'>
      <span
        className={cn(
          isBest
            ? 'text-green-700 font-medium bg-green-50 border-green-200 border rounded-[2px] px-[6px] py-[1px]'
            : 'text-red-500 font-medium'
        )}
      >
        {text}
      </span>
      {betterText && <span className='ml-1 text-gray-500'>{betterText}</span>}
    </div>
  );
}
