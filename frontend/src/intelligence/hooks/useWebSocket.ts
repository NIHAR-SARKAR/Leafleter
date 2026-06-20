import { useEffect, useRef, useState } from "react";

import { IntelligenceEvent } from "@/intelligence/services/intelligenceApi";

export function useWebSocket(url: string) {
  const [events, setEvents] = useState<IntelligenceEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}${url}`);
    ws.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (message) => {
      try {
        const event = JSON.parse(message.data) as IntelligenceEvent;
        setEvents((prev) => [...prev, event].slice(-100));
      } catch {
        // Ignore malformed messages.
      }
    };

    return () => {
      socket.close();
    };
  }, [url]);

  return { events, connected };
}
