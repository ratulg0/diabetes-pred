import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";

type ResourceState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

export function useApiResource<T>(
  load: () => Promise<T>,
  dependencies: readonly unknown[] = [],
) {
  const [state, setState] = useState<ResourceState<T>>({
    data: null,
    loading: true,
    error: null,
  });
  const refresh = useCallback(async () => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const data = await load();
      setState({ data, loading: false, error: null });
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Unable to load data.";
      setState((current) => ({ ...current, loading: false, error: message }));
    }
    // The caller controls reloads through the explicit dependency array.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  useEffect(() => {
    void refresh();
  }, [refresh]);
  return { ...state, refresh };
}
