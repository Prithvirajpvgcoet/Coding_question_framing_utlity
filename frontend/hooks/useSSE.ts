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

    const handleMessage = (event: MessageEvent, eventType: string = "progress") => {
      try {
        const data = JSON.parse(event.data);
        addEvent({
          type: (eventType === "message" ? (data.event || "progress") : eventType) as any,
          current_agent: data.current_agent || data.agent,
          step: data.step,
          total_steps: data.total_steps,
          state: data.state,
          message: data.message || data.error,
        });

        if (eventType === "done" || eventType === "error") {
          es.close();
        }
      } catch (err) {
        console.error("Failed to parse SSE event:", err);
      }
    };

    es.addEventListener("progress", (e) => handleMessage(e, "progress"));
    es.addEventListener("connected", (e) => handleMessage(e, "connected"));
    es.addEventListener("done", (e) => handleMessage(e, "done"));
    es.addEventListener("error", (e) => handleMessage(e, "error"));
    es.onmessage = (e) => handleMessage(e, "message");

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
