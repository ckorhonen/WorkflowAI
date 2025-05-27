import { Add16Regular } from '@fluentui/react-icons';
import { useCallback, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/Popover';

type Props = {
  isHovering: boolean;
  addSystemMessage: () => void;
  addUserMessage: () => void;
  supportOnlySystemMessages: boolean;
};

export function ProxyAddMessageButton(props: Props) {
  const { isHovering, addSystemMessage, addUserMessage, supportOnlySystemMessages } = props;

  const [showAddMessagePopover, setShowAddMessagePopover] = useState(false);

  const onAddSystemMessage = useCallback(() => {
    addSystemMessage();
    setShowAddMessagePopover(false);
  }, [addSystemMessage, setShowAddMessagePopover]);

  const onAddUserMessage = useCallback(() => {
    addUserMessage();
    setShowAddMessagePopover(false);
  }, [addUserMessage, setShowAddMessagePopover]);

  if (!supportOnlySystemMessages) {
    return (
      <>
        {(isHovering || showAddMessagePopover) && (
          <Popover open={showAddMessagePopover} onOpenChange={setShowAddMessagePopover}>
            <PopoverTrigger asChild>
              <Button
                variant='newDesign'
                size='sm'
                icon={<Add16Regular />}
                onClick={() => setShowAddMessagePopover(true)}
              >
                Add Message
              </Button>
            </PopoverTrigger>
            <PopoverContent className='flex flex-col w-full p-1 rounded-[2px]'>
              <Button
                variant='newDesignText'
                onClick={onAddSystemMessage}
                className='w-full justify-start hover:bg-gray-100 hover:text-gray-900 font-normal'
              >
                System Message
              </Button>
              <Button
                variant='newDesignText'
                onClick={onAddUserMessage}
                className='w-full justify-start hover:bg-gray-100 hover:text-gray-900 font-normal'
              >
                User Message
              </Button>
            </PopoverContent>
          </Popover>
        )}
      </>
    );
  }

  return (
    <>
      {isHovering && (
        <Button variant='newDesign' size='sm' icon={<Add16Regular />} onClick={addSystemMessage}>
          Add System Message
        </Button>
      )}
    </>
  );
}
