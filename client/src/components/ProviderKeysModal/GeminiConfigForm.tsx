import { Dispatch, SetStateAction, useCallback, useEffect, useState } from 'react';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { SelectSimple } from '../ui/SelectSimple';

type GeminiConfigFormProps = {
  setConfig: Dispatch<SetStateAction<Record<string, unknown> | undefined>>;
};

export function GeminiConfigForm(props: GeminiConfigFormProps) {
  const { setConfig } = props;

  const [apiKey, setApiKey] = useState<string>();
  const [blockThreshold, setBlockThreshold] = useState<string>();

  const onChangeApiKey = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setApiKey(e.target.value);
  }, []);

  const onChangeBlockThreshold = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setBlockThreshold(e.target.value);
  }, []);

  useEffect(() => {
    setConfig({
      api_key: apiKey,
      block_threshold: blockThreshold || undefined,
    });
  }, [apiKey, blockThreshold, setConfig]);

  return (
    <div className='flex flex-col items-start gap-3 w-full max-w-[600px]'>
      <label htmlFor='api-key' className='text-[14px] text-slate-600 font-medium'>
        API Key
      </label>
      <Input
        id='api-key'
        placeholder='Your Gemini API Key'
        onChange={onChangeApiKey}
        value={apiKey}
        className='w-full rounded-[10px]'
      />

      <label htmlFor='block-threshold' className='text-[14px] text-slate-600 font-medium'>
        Block Threshold
      </label>
      <SelectSimple
        id='block-threshold'
        name='Block threshold'
        value={blockThreshold}
        onSelect={onChangeBlockThreshold}
        className='w-full rounded-[10px] mb-32'
      >
        <option value=''>Default</option>
        <option value='BLOCK_LOW_AND_ABOVE'>Block Low and Above</option>
        <option value='BLOCK_MEDIUM_AND_ABOVE'>Block Medium and Above</option>
        <option value='BLOCK_ONLY_HIGH'>Block Only High</option>
        <option value='BLOCK_NONE'>Block None</option>
      </SelectSimple>
    </div>
  );
}
