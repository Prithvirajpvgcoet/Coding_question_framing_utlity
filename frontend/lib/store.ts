import { create } from "zustand";
import { QuestionState, SSEProgressEvent } from "./types";

interface LiveRunStore {
  activeRunId: string | null;
  status: string;
  currentAgent: string;
  events: SSEProgressEvent[];
  liveState: Partial<QuestionState> | null;
  error: string | null;
  isCompleted: boolean;

  // Actions
  initRun: (runId: string) => void;
  addEvent: (event: SSEProgressEvent) => void;
  setError: (err: string) => void;
  reset: () => void;
}

export const useLiveRunStore = create<LiveRunStore>((set) => ({
  activeRunId: null,
  status: "INITIALIZING",
  currentAgent: "agent_a",
  events: [],
  liveState: null,
  error: null,
  isCompleted: false,

  initRun: (runId: string) =>
    set({
      activeRunId: runId,
      status: "PROCESSING",
      currentAgent: "agent_a",
      events: [],
      liveState: null,
      error: null,
      isCompleted: false,
    }),

  addEvent: (event: SSEProgressEvent) =>
    set((state) => {
      const updatedEvents = [...state.events, event];
      const nextAgent = event.current_agent || state.currentAgent;
      const isDone = event.type === "done";
      const isErr = event.type === "error";

      return {
        events: updatedEvents,
        currentAgent: nextAgent,
        status: isDone ? "COMPLETED" : isErr ? "FAILED" : "PROCESSING",
        isCompleted: isDone,
        error: isErr ? event.message : state.error,
        liveState: event.state ? { ...(state.liveState || {}), ...event.state } : state.liveState,
      };
    }),

  setError: (err: string) =>
    set({
      error: err,
      status: "FAILED",
    }),

  reset: () =>
    set({
      activeRunId: null,
      status: "INITIALIZING",
      currentAgent: "agent_a",
      events: [],
      liveState: null,
      error: null,
      isCompleted: false,
    }),
}));
