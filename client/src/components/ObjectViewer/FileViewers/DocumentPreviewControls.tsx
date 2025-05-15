import { ArrowExpand16Regular, Dismiss16Regular } from '@fluentui/react-icons';
import { cx } from 'class-variance-authority';
import { useCallback } from 'react';
import { useToggle } from 'usehooks-ts';
import { Button } from '@/components/ui/Button';
import { Dialog, DialogContent, DialogHeader } from '@/components/ui/Dialog';
import { FileValueType } from './utils';

type DocumentPreviewControlsProps = {
  className: string | undefined;
  children: React.ReactNode;
  dialogContent?: React.ReactNode;
  onEdit?: (value: FileValueType | undefined) => void;
  readonly?: boolean;
};

export function DocumentPreviewControls(props: DocumentPreviewControlsProps) {
  const { className, children, dialogContent, onEdit, readonly } = props;

  const [dialogOpen, toggleDialog] = useToggle(false);

  const onResetField = useCallback(() => {
    onEdit?.(undefined);
  }, [onEdit]);

  return (
    <div className={cx('relative', className)}>
      <Dialog open={dialogOpen} onOpenChange={toggleDialog}>
        <DialogContent className='p-0 gap-0 flex flex-col h-[95vh] max-w-[95vw] overflow-hidden'>
          <DialogHeader title='Preview' onClose={toggleDialog} />
          <div className='p-4 flex-1 overflow-y-auto max-h-full'>{dialogContent || children}</div>
        </DialogContent>
      </Dialog>
      <div className='absolute left-2 top-2 flex gap-1 items-center z-10'>
        {!readonly && (
          <Button
            variant='newDesign'
            icon={<Dismiss16Regular />}
            onClick={onResetField}
            className='w-7 h-7 px-0 py-0'
          />
        )}
        <Button
          variant='newDesign'
          icon={<ArrowExpand16Regular />}
          onClick={toggleDialog}
          className='w-7 h-7 px-0 py-0'
        />
      </div>
      {children}
    </div>
  );
}
