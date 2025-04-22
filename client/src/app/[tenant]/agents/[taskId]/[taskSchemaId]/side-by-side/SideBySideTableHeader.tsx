import { useMemo } from 'react';
import { ModelResponse, VersionV1 } from '@/types/workflowAI';
import { SideBySideVersionPopover } from './SideBySideVersionPopover';

type SideBySideTableHeaderProps = {
  versions: VersionV1[];
  models: ModelResponse[] | undefined;
  baseVersion: VersionV1 | undefined;

  selectedLeftVersionId: string | undefined;
  setSelectedLeftVersionId: (newVersionId: string | undefined) => void;

  selectedRightVersionId: string | undefined;
  setSelectedRightVersionId: (newVersionId: string | undefined) => void;

  selectedRightModelId: string | undefined;
  setSelectedRightModelId: (newModelId: string | undefined) => void;

  page: number;
};
export function SideBySideTableHeader(props: SideBySideTableHeaderProps) {
  const {
    versions,
    models,
    baseVersion,
    selectedLeftVersionId,
    setSelectedLeftVersionId,
    selectedRightVersionId,
    setSelectedRightVersionId,
    selectedRightModelId,
    setSelectedRightModelId,
    page,
  } = props;

  const modelIdsToFilter = useMemo(() => {
    const leftModelId =
      versions.find((version) => version.id === selectedLeftVersionId)?.properties?.model ?? undefined;
    return [selectedRightModelId, leftModelId];
  }, [selectedLeftVersionId, selectedRightModelId, versions]);

  return (
    <div className='flex items-center w-full h-[68px] border-b border-gray-100 font-lato text-gray-900 text-[13px] font-medium bg-white/60'>
      <div className='flex items-center w-[20%] h-full p-4 border-r border-gray-100'>
        <div className='flex w-full items-center justify-start gap-1 text-gray-700 pl-3 pr-2 py-[6px] border border-gray-300 rounded-[2px] bg-gray-100 shadow-sm'>
          <div>Last Runs</div>
          {page > 1 && <div>(Page {page})</div>}
        </div>
      </div>
      <div className='flex items-center w-[40%] h-full p-4 border-r border-gray-100'>
        <SideBySideVersionPopover
          versions={versions}
          selectedVersionId={selectedLeftVersionId}
          setSelectedVersionId={setSelectedLeftVersionId}
          filterVersionIds={[selectedLeftVersionId]}
          placeholder='Select Version'
        />
      </div>
      <div className='flex items-center w-[40%] h-full p-4'>
        <SideBySideVersionPopover
          versions={versions}
          models={models}
          baseVersion={baseVersion}
          selectedVersionId={selectedRightVersionId}
          setSelectedVersionId={setSelectedRightVersionId}
          selectedModelId={selectedRightModelId}
          setSelectedModelId={setSelectedRightModelId}
          filterVersionIds={[selectedLeftVersionId, selectedRightVersionId]}
          filterModelIds={modelIdsToFilter}
          placeholder='Select Version or Model'
        />
      </div>
    </div>
  );
}
