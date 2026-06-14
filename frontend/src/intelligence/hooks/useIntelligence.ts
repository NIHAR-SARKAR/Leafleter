import { useCallback, useEffect, useState } from "react";

import { intelligenceApi, IntelligenceToday } from "@/intelligence/services/intelligenceApi";

export function useIntelligence() {
  const [today, setToday] = useState<IntelligenceToday | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await intelligenceApi.getToday();
      setToday(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load intelligence");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { today, loading, error, refresh };
}
