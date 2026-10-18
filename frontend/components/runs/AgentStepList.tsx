"use client";

import { SSEProgressEvent, AgentRunStep } from "@/lib/types";
import { CheckCircle2, Clock, AlertCircle, Bot } from "lucide-react";

interface AgentStepListProps {
  events: SSEProgressEvent[];
  historicalSteps?: AgentRunStep[];
  currentAgent: string;
}

const AGENT_LABELS: Record<string, string> = {
  agent_a: "Agent A · Intake & Blueprint",
  agent_b: "Agent B · Knowledge Retrieval",
  agent_c: "Agent C · Build Question & Sandbox",
  dedup_check: "Dedup Gate · Semantic Check",
  agent_d: "Agent D · Multi-Factor Scorer",
  agent_e: "Agent E · Feedback Analysis",
  agent_f: "Agent F · Revision Router",
  agent_g: "Agent G · Deterministic Gate",
};

export function AgentStepList({
  events,
  historicalSteps = [],
  currentAgent,
}: AgentStepListProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <Bot className="w-4 h-4 text-blue-600" />
          Agent Execution Logs
        </h4>
        <span className="text-[11px] text-slate-400 font-mono">
          {events.length} event{events.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 py-3 pr-1 text-xs">
        {events.length === 0 && historicalSteps.length === 0 && (
          <div className="text-center py-10 text-slate-400">
            <Clock className="w-6 h-6 mx-auto mb-2 text-slate-300 animate-spin" />
            <p>Waiting for agent pipeline to start...</p>
          </div>
        )}

        {/* Real-time SSE events */}
        {events.map((ev, i) => {
          const isDone = ev.type === "done";
          const isErr = ev.type === "error";
          const agentLabel = AGENT_LABELS[ev.current_agent] || ev.current_agent;

          return (
            <div
              key={i}
              className={`p-3 rounded-lg border transition-all ${
                isErr
                  ? "bg-red-50 border-red-200 text-red-900"
                  : isDone
                  ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                  : "bg-slate-50 border-slate-200 text-slate-800"
              }`}
            >
              <div className="flex items-center justify-between font-medium">
                <span className="font-semibold text-blue-700">{agentLabel}</span>
                <span className="text-[10px] text-slate-400 font-mono">
                  {isDone ? "COMPLETE" : isErr ? "ERROR" : "PROGRESS"}
                </span>
              </div>
              <p className="mt-1 text-slate-600 font-mono text-[11px] whitespace-pre-wrap">
                {ev.message}
              </p>
            </div>
          );
        })}

        {/* Historical DB Steps (if loaded on page refresh) */}
        {historicalSteps.length > 0 && events.length === 0 && (
          <div className="space-y-2">
            {historicalSteps.map((step) => (
              <div
                key={step.id}
                className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>{AGENT_LABELS[step.agent_name] || step.agent_name}</span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">
                    Model: {step.model} · {step.latency_ms}ms · ${(step.cost_usd || 0).toFixed(4)}
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-700 uppercase">
                  {step.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
