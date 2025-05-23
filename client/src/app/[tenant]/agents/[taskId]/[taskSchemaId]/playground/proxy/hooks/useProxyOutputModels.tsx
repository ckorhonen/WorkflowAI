import { useCallback, useEffect, useMemo, useState } from 'react';
import { useCompatibleAIModels } from '@/lib/hooks/useCompatibleAIModels';
import { ModelOptional, TaskID, TaskSchemaID, TenantID } from '@/types/aliases';
import { RunV1 } from '@/types/workflowAI';
import { PlaygroundModels } from '../../hooks/utils';

export function useProxyOutputModels(
  tenant: TenantID | undefined,
  taskId: TaskID,
  taskSchemaId: TaskSchemaID,
  run1: RunV1 | undefined,
  run2: RunV1 | undefined,
  run3: RunV1 | undefined
) {
  const [model1, setModel1] = useState<string | undefined>(undefined);
  const [model2, setModel2] = useState<string | undefined>(undefined);
  const [model3, setModel3] = useState<string | undefined>(undefined);

  const { compatibleModels, allModels, defaultModels } = useCompatibleAIModels({
    tenant,
    taskId,
    taskSchemaId,
  });

  const outputModels = useMemo(() => {
    return [
      model1 ?? defaultModels[0]?.id ?? undefined,
      model2 ?? defaultModels[1]?.id ?? undefined,
      model3 ?? defaultModels[2]?.id ?? undefined,
    ] as PlaygroundModels;
  }, [model1, model2, model3, defaultModels]);

  const setOutputModels = useCallback((index: number, model: ModelOptional) => {
    switch (index) {
      case 0:
        setModel1(model ?? undefined);
        break;
      case 1:
        setModel2(model ?? undefined);
        break;
      case 2:
        setModel3(model ?? undefined);
        break;
    }
  }, []);

  useEffect(() => {
    if (!!run1?.version.properties.model) {
      setModel1(run1.version.properties.model);
    }
  }, [run1?.version.properties.model]);

  useEffect(() => {
    if (!!run2?.version.properties.model) {
      setModel2(run2.version.properties.model);
    }
  }, [run2?.version.properties.model]);

  useEffect(() => {
    if (!!run3?.version.properties.model) {
      setModel3(run3.version.properties.model);
    }
  }, [run3?.version.properties.model]);

  return {
    outputModels,
    setOutputModels,
    compatibleModels: compatibleModels,
    allModels: allModels,
  };
}
