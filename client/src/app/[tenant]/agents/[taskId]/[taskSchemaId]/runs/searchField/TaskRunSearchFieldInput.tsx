import { cx } from 'class-variance-authority';
import { useEffect, useRef, useState } from 'react';

type TaskRunSearchFieldInputProps = {
  inputRef: React.RefObject<HTMLInputElement>;
  text: string;
  handleInputChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  handleKeyDown: (event: React.KeyboardEvent) => void;
  handleFocus: () => void;
  handleBlur: () => void;
  isEmpty: boolean;
  showBorder: boolean;
};

export function TaskRunSearchFieldInput(props: TaskRunSearchFieldInputProps) {
  const { inputRef, text, handleInputChange, handleKeyDown, handleFocus, handleBlur, isEmpty, showBorder } = props;

  const [textWidth, setTextWidth] = useState(0);
  const textMeasureRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (textMeasureRef.current && inputRef.current) {
      const inputStyles = window.getComputedStyle(inputRef.current);
      textMeasureRef.current.style.font = inputStyles.font;
      textMeasureRef.current.style.letterSpacing = inputStyles.letterSpacing;
      setTextWidth(textMeasureRef.current.offsetWidth);
    }
  }, [text, inputRef]);

  const rightBorderMargin = 10;

  return (
    <div className='flex flex-row justify-between items-center h-6 relative'>
      <input
        ref={inputRef}
        type='text'
        value={text}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={handleFocus}
        onBlur={handleBlur}
        className='flex-grow outline-none font-normal text-[13px] bg-transparent z-10 relative placeholder:text-gray-400 text-gray-900'
        placeholder={isEmpty ? 'Filter run by version, input, output, model and more...' : undefined}
        autoComplete='off'
        spellCheck={false}
        autoCapitalize='off'
        data-1p-ignore
      />
      <div
        className={cx(
          'absolute left-0 top-0 h-6 rounded-r-[2px] pointer-events-none border-gray-200',
          showBorder && 'border-t border-b border-r'
        )}
        style={{
          width: `${textWidth + rightBorderMargin}px`,
        }}
      />
      <span ref={textMeasureRef} className='absolute left-0 top-0 invisible whitespace-pre'>
        {text}
      </span>
    </div>
  );
}
