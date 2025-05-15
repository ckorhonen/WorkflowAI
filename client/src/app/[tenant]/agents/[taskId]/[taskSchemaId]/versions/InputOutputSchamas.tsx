import { useMemo } from 'react';
import { ObjectViewer } from '@/components/ObjectViewer/ObjectViewer';
import { TaskOutputViewer } from '@/components/ObjectViewer/TaskOutputViewer';
import { Loader } from '@/components/ui/Loader';
import { useOrFetchVersion } from '@/store/fetchers';
import { TaskID } from '@/types/aliases';
import { TenantID } from '@/types/aliases';
import { JsonSchema } from '@/types/json_schema';
import { checkVersionForProxy } from '../playground/hooks/useIsProxy';
import { ProxyOutputViewer } from '../playground/proxy/ProxyOutputViewer';

type InputOutputSchemasProps = {
  tenant: TenantID;
  taskId: TaskID;
  versionId: string;
};

export function InputOutputSchemas(props: InputOutputSchemasProps) {
  const { tenant, taskId, versionId } = props;

  const { version, isInitialized } = useOrFetchVersion(tenant, taskId, versionId);
  const isProxy = useMemo(() => checkVersionForProxy(version), [version]);

  if (!isInitialized || !version) {
    return <Loader centered />;
  }

  const inputSchema = version.input_schema as JsonSchema;
  const outputSchema = version.output_schema as JsonSchema;

  return (
    <div className='flex flex-row w-full h-max border-gray-200 border rounded-[2px] bg-gradient-to-b from-white to-white/0'>
      <div className='flex flex-col w-1/2 min-h-full border-gray-200 border-r border-dashed'>
        <div className='text-gray-700 text-[13px] font-semibold px-4 py-2 flex w-full border-b border-gray-200 border-dashed'>
          Input
        </div>
        <ObjectViewer
          textColor='text-gray-500'
          value={undefined}
          schema={inputSchema}
          defs={inputSchema?.$defs}
          showDescriptionExamples={'all'}
          showTypes={false}
          showDescriptionPopover={false}
        />
      </div>
      <div className='flex flex-col w-1/2 min-h-full'>
        <div className='text-gray-700 text-[13px] font-semibold px-4 py-2 flex w-full border-b border-gray-200 border-dashed'>
          Output
        </div>
        {isProxy ? (
          <ProxyOutputViewer
            taskOutput={undefined}
            toolCalls={undefined}
            reasoningSteps={undefined}
            streamLoading={false}
            outputSchema={outputSchema}
            referenceValue={undefined}
            emptyMode={false}
          />
        ) : (
          <TaskOutputViewer
            textColor='text-gray-500'
            value={undefined}
            schema={outputSchema}
            defs={outputSchema?.$defs}
            showDescriptionExamples={'all'}
            showTypes={false}
            showDescriptionPopover={false}
          />
        )}
      </div>
    </div>
  );
}
