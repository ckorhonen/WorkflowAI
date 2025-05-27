import Image from 'next/image';

type NewTaskFlowChoiceSectionProps = {
  title: string;
  subtitle: string;
  imageURL: string;
  children: React.ReactNode;
};

export function NewTaskFlowChoiceSection(props: NewTaskFlowChoiceSectionProps) {
  const { title, subtitle, imageURL, children } = props;

  return (
    <div className='flex flex-col w-full h-full items-center'>
      <div className='text-gray-900 text-[16px] font-semibold pt-10'>{title}</div>
      <div className='text-gray-500 text-[13px] font-normal pt-2 max-w-[550px]'>{subtitle}</div>
      <Image src={imageURL} alt={title} width={1184} height={620} className='px-10 pt-6' />
      <div className='flex items-end justify-center w-full flex-1'>{children}</div>
    </div>
  );
}
