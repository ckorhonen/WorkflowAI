import { ChevronsUpDown } from 'lucide-react';
import { useCallback, useMemo, useState } from 'react';
import { CustomCommandInput } from '@/components/ui/Command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/Popover';
import { cn } from '@/lib/utils';
import { formatSemverVersion, sortVersionsTakingIntoAccountEnvironments } from '@/lib/versionUtils';
import { ModelResponse, VersionV1 } from '@/types/workflowAI';
import { SideBySideVersionPopoverItem } from './SideBySideVersionPopoverItem';
import { SideBySideVersionPopoverModelItem } from './SideBySideVersionPopoverModelItem';

type SideBySideVersionPopoverProps = {
  versions: VersionV1[];
  models?: ModelResponse[];
  baseVersion?: VersionV1;
  selectedVersionId: string | undefined;
  setSelectedVersionId: (newVersionId: string | undefined) => void;
  selectedModelId?: string | undefined;
  setSelectedModelId?: (newModelId: string | undefined) => void;
  filterVersionIds?: (string | undefined)[];
  filterModelIds?: (string | undefined)[];
  placeholder?: string;
  searchPlaceholder?: string;
};

export function SideBySideVersionPopover(props: SideBySideVersionPopoverProps) {
  const {
    versions,
    baseVersion,
    selectedVersionId,
    setSelectedVersionId,
    filterVersionIds,
    selectedModelId,
    setSelectedModelId,
    filterModelIds,
    models,
    placeholder = 'Select',
    searchPlaceholder = 'Search versions',
  } = props;

  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const searchLower = search.toLowerCase();

  const selectedVersion = useMemo(() => {
    return versions.find((version) => version.id === selectedVersionId);
  }, [versions, selectedVersionId]);

  const selectedModel = useMemo(() => {
    return models?.find((model) => model.id === selectedModelId);
  }, [models, selectedModelId]);

  const versionsToUse = useMemo(() => {
    let result = versions.filter((version) => {
      return !filterVersionIds?.includes(version.id);
    });
    result = sortVersionsTakingIntoAccountEnvironments(result);
    return result;
  }, [versions, filterVersionIds]);

  const filteredVersions = useMemo(() => {
    return versionsToUse.filter((version) => {
      const textBadge = formatSemverVersion(version);
      return textBadge?.includes(searchLower) || version.properties?.model?.toLowerCase().includes(searchLower);
    });
  }, [versionsToUse, searchLower]);

  const modelsToUse = useMemo(() => {
    const result = models?.filter((model) => {
      return !filterModelIds?.includes(model.id);
    });
    return result;
  }, [models, filterModelIds]);

  const filteredModels = useMemo(() => {
    return modelsToUse?.filter((model) => {
      const textBadge = model.name;
      return textBadge?.toLowerCase().includes(searchLower);
    });
  }, [modelsToUse, searchLower]);

  const onSelectedVersionId = useCallback(
    (versionId: string | undefined) => {
      setSelectedVersionId(versionId);
      setOpen(false);
    },
    [setSelectedVersionId, setOpen]
  );

  const onSelectedModelId = useCallback(
    (modelId: string | undefined) => {
      setSelectedModelId?.(modelId);
      setOpen(false);
    },
    [setSelectedModelId, setOpen]
  );

  const showTriggerVersionItem = !!selectedVersionId;
  const showTriggerModelItem = !!selectedModelId;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <div className='flex flex-row items-center gap-2 w-full border border-gray-300 rounded-[2px] min-h-9 px-3 shadow-sm cursor-pointer hover:bg-accent hover:text-accent-foreground'>
          <div className='flex-1 min-w-0'>
            {showTriggerVersionItem ? (
              <SideBySideVersionPopoverItem version={selectedVersion} className='px-0' showDetails={false} />
            ) : showTriggerModelItem ? (
              <SideBySideVersionPopoverModelItem model={selectedModel} baseVersion={baseVersion} />
            ) : (
              <div className='text-sm font-medium text-gray-500 truncate'>{placeholder}</div>
            )}
          </div>
          <ChevronsUpDown className='h-4 w-4 shrink-0 text-gray-500' />
        </div>
      </PopoverTrigger>
      <PopoverContent className='max-w-[90vw] w-fit overflow-auto max-h-[362px] p-0 rounded-[2px]' align='start'>
        <CustomCommandInput placeholder={searchPlaceholder} search={search} onSearchChange={setSearch} />
        {filteredVersions.length === 0 && (!filteredModels || filteredModels.length === 0) && (
          <div className='text-sm text-center p-4'>No versions found</div>
        )}
        {!!filteredVersions && filteredVersions.length > 0 && (
          <div
            className={cn(
              'flex flex-col pl-1 pr-1 pt-1 pb-2',
              !!filteredModels && filteredModels.length > 0 && 'border-b border-gray-200 border-dashed'
            )}
          >
            <div className='text-indigo-600 text-xs font-medium font-lato px-2 pt-2 pb-2'>VERSIONS</div>
            {filteredVersions.map((version) => {
              return (
                <SideBySideVersionPopoverItem
                  key={version.id}
                  version={version}
                  onClick={() => onSelectedVersionId(version.id)}
                />
              );
            })}
          </div>
        )}
        {!!filteredModels && filteredModels.length > 0 && (
          <div className='flex flex-col pl-1 pr-1 pt-1 pb-2'>
            <div className='text-indigo-600 text-xs font-medium font-lato px-2 pt-2 pb-2'>MODELS</div>
            {filteredModels.map((model) => {
              return (
                <SideBySideVersionPopoverModelItem
                  key={model.id}
                  model={model}
                  baseVersion={baseVersion}
                  onClick={() => onSelectedModelId(model.id)}
                  className='pl-2'
                />
              );
            })}
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
