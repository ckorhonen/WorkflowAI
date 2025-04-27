import { DeviceEqFilled, DocumentBulletList16Regular } from '@fluentui/react-icons';
import { cx } from 'class-variance-authority';
import { Check, ChevronsUpDown } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Command, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/Command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/Popover';
import { SelectableFieldType } from '@/lib/schemaEditorUtils';
import { ImagePlaceholderIcon } from '../icons/ImagePlaceholderIcon';
import { Button } from '../ui/Button';

type FieldTypeWithIconProps = {
  title: string;
  icon: React.ReactNode;
};

function FieldTypeWithIcon(props: FieldTypeWithIconProps) {
  const { title, icon } = props;
  return (
    <div className='flex items-center gap-2'>
      <div>{title}</div>
      {icon}
    </div>
  );
}

function FieldTypeDisplay(props: { type: SelectableFieldType }) {
  const { type } = props;
  if (type === 'array') {
    return 'list';
  } else if (type === 'image') {
    return <FieldTypeWithIcon title='image' icon={<ImagePlaceholderIcon />} />;
  } else if (type === 'audio') {
    return <FieldTypeWithIcon title='audio' icon={<DeviceEqFilled />} />;
  } else if (type === 'document') {
    return <FieldTypeWithIcon title='document' icon={<DocumentBulletList16Regular />} />;
  }
  return type;
}

const REGULAR_FIELD_TYPES: SelectableFieldType[] = [
  'string',
  'boolean',
  'number',
  'array',
  'enum',
  'object',
  'date',
  'date-time',
  'time',
  'timezone',
  'html',
  'image',
  'audio',
  'document',
];

type SchemaTypeSelectorProps = {
  type: SelectableFieldType;
  onChange: (newType: SelectableFieldType) => void;
  noArray?: boolean;
  disableImage?: boolean;
  disableAudio?: boolean;
  disableDocuments?: boolean;
  disabled?: boolean;
};

export function SchemaTypeSelector(props: SchemaTypeSelectorProps) {
  const { type, onChange, noArray, disableImage, disableAudio, disableDocuments, disabled = false } = props;

  const selectableFieldTypes = useMemo(() => {
    return REGULAR_FIELD_TYPES.filter((fieldType) => {
      if (noArray && fieldType === 'array') {
        return false;
      }
      if (disableImage && fieldType === 'image') {
        return false;
      }
      if (disableAudio && fieldType === 'audio') {
        return false;
      }
      if (disableDocuments && fieldType === 'document') {
        return false;
      }
      return true;
    });
  }, [noArray, disableImage, disableAudio, disableDocuments]);

  const [open, setOpen] = useState(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild disabled={disabled}>
        <Button
          variant='outline'
          role='combobox'
          aria-expanded={open}
          className='min-w-14 w-fit h-8 px-2 shrink-0 font-lato text-[13px] font-normal text-gray-500 rounded-[2px] border-gray-200'
        >
          <FieldTypeDisplay type={type} />
          <ChevronsUpDown size={12} className='shrink-0' />
        </Button>
      </PopoverTrigger>
      <PopoverContent className='w-[150px] p-0 rounded-[2px] border-gray-300 font-lato'>
        <Command>
          <CommandInput placeholder='Search...' className='h-8 font-lato font-normal text-[13px] text-gray-900' />
          <CommandList>
            <CommandGroup>
              {selectableFieldTypes.map((fieldType) => (
                <CommandItem
                  key={fieldType}
                  value={fieldType}
                  onSelect={(currentValue) => {
                    if (currentValue !== type) {
                      onChange(currentValue as SelectableFieldType);
                    }
                    setOpen(false);
                  }}
                >
                  <div className='flex items-center gap-2 font-lato font-normal text-[13px] text-gray-500'>
                    <Check
                      size={14}
                      className={cx('text-indigo-700', fieldType === type ? 'opacity-100' : 'opacity-0')}
                    />
                    <FieldTypeDisplay type={fieldType} />
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
