import { ModelBadge } from '@/components/ModelBadge/ModelBadge';
import { TaskVersionBadgeContainer } from '@/components/TaskIterationBadge/TaskVersionBadgeContainer';
import { cn } from '@/lib/utils';
import { ModelResponse, VersionV1 } from '@/types/workflowAI';

type SideBySideVersionPopoverModelItemProps = {
  model?: ModelResponse;
  onClick?: () => void;
  className?: string;
  baseVersion?: VersionV1;
};

export function SideBySideVersionPopoverModelItem(props: SideBySideVersionPopoverModelItemProps) {
  const { model, onClick, className, baseVersion } = props;

  if (!model) {
    return null;
  }

  return (
    <div
      className={cn(
        'flex flex-row items-center gap-1 rounded-[1px] hover:bg-gray-100 cursor-pointer py-1 overflow-hidden',
        className
      )}
      onClick={onClick}
    >
      {model && (
        <div className='flex flex-row items-center gap-2'>
          {baseVersion && (
            <TaskVersionBadgeContainer
              version={baseVersion}
              showDetails={false}
              showNotes={false}
              showHoverState={false}
              showSchema={true}
              interaction={false}
              showFavorite={false}
              hideMinorVersion={true}
            />
          )}
          <ModelBadge model={model} />
        </div>
      )}
    </div>
  );
}
