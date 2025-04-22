import { ArrowUp } from 'lucide-react';
import { cn } from '@/lib/utils';

type StatsLatencyProps = {
  latency: number | undefined;
  bestLatency: number | undefined;
};

export function StatsLatency(props: StatsLatencyProps) {
  const { latency, bestLatency } = props;

  const isBest = latency === bestLatency;
  const text = latency ? `${latency.toFixed(1)}s` : '-';

  const worserText =
    bestLatency && latency && bestLatency < latency ? `${(latency / bestLatency).toFixed(1)}x` : undefined;

  if (!latency) {
    return <div className='flex items-center justify-start w-full h-full text-gray-500 text-[16px]'>-</div>;
  }

  return (
    <div className='flex items-center justify-start w-full h-full text-gray-500 text-[13px]'>
      {worserText && (
        <span className='flex flex-row items-center text-[13px] font-medium text-red-500 mr-2'>
          {worserText}
          <ArrowUp size={12} />
        </span>
      )}
      <span
        className={cn(
          isBest
            ? 'text-green-700 font-medium bg-green-50 border-green-200 border rounded-[2px] px-[6px] py-[1px]'
            : 'text-gray-500 font-medium'
        )}
      >
        {text}
      </span>
    </div>
  );
}
