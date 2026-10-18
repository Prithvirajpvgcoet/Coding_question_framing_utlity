"use client";

import { useEffect, useRef } from "react";
import { useLiveRunStore } from "@/lib/store";
import { api } from "@/lib/api";
import { SSEProgressEvent } from "@/lib/types";

export function useSSE(questionId: string | null) {
  const { initRun, addEvent, setError } = useLiveRunStore();
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!questionId) return;

    initRun(questionId);
    const streamUrl = api.getStreamUrl(questionId);

    const es = new EventSource(streamUrl);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as SSEProgressEvent;
        addEvent(data);

        if (data.type === "done" || data.type === "error") {
          es.close();
        }
      } catch (err) {
        console.error("Failed to parse SSE event:", err);
      }
    };

    es.onerror = () => {
      // EventSource reconnects automatically on network drops, but if closed on server:
      if (es.readyState === EventSource.CLOSED) {
        es.close();
      }
    };

    return () => {
      if (es) {
        es.close();
      }
    };
  }, [questionId, initRun, addEvent, setError]);

  return {
    close: () => eventSourceRef.current?.close(),
  };
}
