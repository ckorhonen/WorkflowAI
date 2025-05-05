import { useCallback, useMemo } from 'react';
import { useLocalStorage } from 'usehooks-ts';

type ModelToAdvertise = {
  name: string;
  date: string;
  modelId: string;
};

const MODELS_TO_ADVERTISE: ModelToAdvertise[] = [
  {
    name: 'Qwen3',
    date: '2025-05-05',
    modelId: 'qwen3-235b-a22b',
  },
];

const STORAGE_KEY = 'dismissedModels';

export function useModelToAdvertise() {
  const [dismissedModels, setDismissedModels] = useLocalStorage<string[]>(STORAGE_KEY, []);

  const modelToAdvertise = useMemo(() => {
    const result = MODELS_TO_ADVERTISE.find((model) => {
      if (dismissedModels.includes(model.name)) {
        return false;
      }

      const date = new Date(model.date);
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - date.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return diffDays <= 3;
    });

    return result;
  }, [dismissedModels]);

  const dismiss = useCallback(
    (model: string) => {
      setDismissedModels((prev) => [...prev, model]);
    },
    [setDismissedModels]
  );

  return {
    modelToAdvertise: modelToAdvertise?.name,
    modelId: modelToAdvertise?.modelId,
    dismiss,
  };
}
