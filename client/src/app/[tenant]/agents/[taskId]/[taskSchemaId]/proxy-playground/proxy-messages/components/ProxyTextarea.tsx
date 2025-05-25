import { useCallback, useMemo } from 'react';
import { ProxyMessageContent } from '@/types/workflowAI';
import { createEmptyMessageContent, formatResponseToText } from '../utils';
import { VariablesTextarea } from '../variables-textarea/VariablesTextarea';

type ProxyTextareaProps = {
  content: ProxyMessageContent | undefined;
  setContent: (content: ProxyMessageContent) => void;
  placeholder: string;
  minHeight?: number;
  readOnly?: boolean;
  inputVariblesKeys?: string[];
  supportInputVaribles?: boolean;
};

export function ProxyTextarea(props: ProxyTextareaProps) {
  const { content, placeholder, setContent, readOnly, inputVariblesKeys, supportInputVaribles = true } = props;

  const onChange = useCallback(
    (value: string) => {
      let newContent = content ?? createEmptyMessageContent();
      newContent = { ...newContent, text: value };
      setContent(newContent);
    },
    [content, setContent]
  );

  const text = useMemo(() => {
    return formatResponseToText(content?.text);
  }, [content]);

  return (
    <VariablesTextarea
      text={text ?? ''}
      onTextChange={onChange}
      placeholder={placeholder}
      readOnly={readOnly}
      inputVariblesKeys={inputVariblesKeys}
      supportInputVaribles={supportInputVaribles}
    />
  );
}
