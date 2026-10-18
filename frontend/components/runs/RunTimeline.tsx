"use client";

import { Check, Loader2, AlertCircle } from "lucide-react";

interface RunTimelineProps {
  currentAgent: string;
  status: string;
  internalRetries?: number;
  revisionCount?: number;
}

const AGENTS = [
  { id: "agent_a", label: "A. Intake & Blueprint", short: "A" },
  { id: "agent_b", label: "B. Retrieval", short: "B" },
  { id: "agent_c", label: "C. Build Question", short: "C" },
  { id: "dedup_check", label: "Dedup Gate", short: "Dedup" },
  { id: "agent_d", label: "D. Quality Check", short: "D" },
  { id: "agent_e", label: "E/F. Revision", short: "E/F" },
  { id: "agent_g", label: "G. Final Gate", short: "G" },
];

export function RunTimeline({
  currentAgent,
  status,
  internalRetries = 0,
  revisionCount = 0,
}: RunTimelineProps) {
  const currentIndex = AGENTS.findIndex((a) => a.id === currentAgent);
  const isDone = status === "COMPLETED" || status === "APPROVED" || status === "AWAITING_REVIEW";
  const isFailed = status === "FAILED" || status === "QA_FAILED" || status === "CANCELLED";

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
          LangGraph Agent Workflow Pipeline
        </h4>
        <div className="flex items-center gap-3 text-xs">
          {internalRetries > 0 && (
            <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-mono">
              Internal Retries: {internalRetries}/3
            </span>
          )}
          {revisionCount > 0 && (
            <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-mono">
              Revisions: {revisionCount}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between relative">
        {/* Connecting Line */}
        <div className="absolute left-6 right-6 top-1/2 -translate-y-1/2 h-0.5 bg-slate-200 -z-0" />

        {AGENTS.map((agent, idx) => {
          let state: "completed" | "current" | "pending" | "failed" = "pending";

          if (isDone) {
            state = "completed";
          } else if (isFailed && idx === currentIndex) {
            state = "failed";
          } else if (idx < currentIndex) {
            state = "completed";
          } else if (idx === currentIndex) {
            state = "current";
          }

          return (
            <div key={agent.id} className="relative z-10 flex flex-col items-center group">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition-all border-2 ${
                  state === "completed"
                    ? "bg-emerald-600 border-emerald-600 text-white shadow-sm"
                    : state === "current"
                    ? "bg-blue-600 border-blue-600 text-white shadow-md ring-4 ring-blue-100"
                    : state === "failed"
                    ? "bg-red-600 border-red-600 text-white shadow-sm"
                    : "bg-white border-slate-300 text-slate-400"
                }`}
              >
                {state === "completed" ? (
                  <Check className="w-4 h-4 stroke-[3]" />
                ) : state === "current" ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : state === "failed" ? (
                  <AlertCircle className="w-4 h-4" />
                ) : (
                  agent.short
                )}
              </div>
              <span
                className={`text-[11px] font-medium mt-2 max-w-[80px] text-center truncate ${
                  state === "current"
                    ? "text-blue-700 font-bold"
                    : state === "completed"
                    ? "text-slate-800"
                    : "text-slate-400"
                }`}
              >
                {agent.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
