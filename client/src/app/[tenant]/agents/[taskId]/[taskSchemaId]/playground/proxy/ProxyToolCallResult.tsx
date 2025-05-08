import { StreamOutputRegular } from '@fluentui/react-icons';
import { useMemo } from 'react';
import { ToolCallResult } from './utils';

type Props = {
  result: ToolCallResult;
};

export function ProxyToolCallResult(props: Props) {
  const { result } = props;

  const dictText = useMemo(() => JSON.stringify(result.result), [result.result]);

  if (!result.result) {
    return null;
  }

  return (
    <div className='flex flex-col'>
      <div className='flex items-center justify-between px-1'>
        <div className='flex items-center gap-2 text-gray-700 text-xsm'>
          <StreamOutputRegular className='w-4 h-4 text-gray-400' />
          Tool Call Result
        </div>
      </div>
      <div className='pl-6 py-2'>
        <div className='flex flex-col text-gray-700 text-xsm border-l px-3 gap-2'>{dictText}</div>
      </div>
    </div>
  );
}
