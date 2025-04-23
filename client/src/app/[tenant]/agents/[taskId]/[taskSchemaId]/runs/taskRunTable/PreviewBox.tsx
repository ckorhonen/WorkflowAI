import { DeviceEqFilled, DocumentBulletList16Regular } from '@fluentui/react-icons';
import { Fragment, ReactNode, memo } from 'react';
import { ImagePlaceholderIcon } from '@/components/icons/ImagePlaceholderIcon';
import { cn } from '@/lib/utils';

function ImagePreview(props: { url: string }) {
  const { url } = props;

  if (!url) {
    return <ImagePlaceholderIcon />;
  }

  // eslint-disable-next-line @next/next/no-img-element
  return <img src={url} alt='' className='max-h-12 max-w-12 object-contain' loading='lazy' />;
}

function PreviewComponent(props: { prefix: string; url: string }) {
  if (props.prefix === 'img') {
    return <ImagePreview url={props.url} />;
  }

  switch (props.prefix) {
    case 'audio':
      return <DeviceEqFilled />;
    default:
      return <DocumentBulletList16Regular />;
  }
}

export function splitPreview(
  preview: string,
  mapper: (prefix: string, url: string, index: number) => string | ReactNode
) {
  const regex = /\[\[(\w+):(.*?)\]\]/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  // Loop over each match of our regex in the input text
  while ((match = regex.exec(preview)) !== null) {
    // Push the text that appears before the current match.
    if (match.index > lastIndex) {
      parts.push(preview.substring(lastIndex, match.index));
    }

    const fieldType = match[1]; // e.g., "img"
    const content = match[2]; // e.g., "https://link-to-the-image"
    parts.push(mapper(fieldType, content, match.index));
    // Update the last index to the end of the current match.
    lastIndex = regex.lastIndex;
  }

  // If there is any remaining text after the last match, add it.
  if (lastIndex < preview.length) {
    parts.push(preview.substring(lastIndex));
  }
  return parts;
}

export const PreviewBox = memo(function PreviewBox(props: { preview: string; pretty: boolean }) {
  const { preview, pretty } = props;
  const baseCls = 'flex-1 overflow-hidden text-ellipsis whitespace-nowrap';

  if (!pretty) {
    return <div className={baseCls}>{preview}</div>;
  }

  const parts = splitPreview(preview, (prefix, url, index) => (
    <PreviewComponent prefix={prefix} url={url} key={index} />
  ));

  return (
    <div className={cn(baseCls, 'flex flex-row gap-1 items-center')}>
      {parts.map((part, index) => (
        <Fragment key={index}>{part}</Fragment>
      ))}
    </div>
  );
});
