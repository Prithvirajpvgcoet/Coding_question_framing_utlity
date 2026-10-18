"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import useSWR from "swr";
import { TopBar } from "@/components/layout/TopBar";
import { RunTimeline } from "@/components/runs/RunTimeline";
import { AgentStepList } from "@/components/runs/AgentStepList";
import { LivePreviewPanel } from "@/components/runs/LivePreviewPanel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useSSE } from "@/hooks/useSSE";
import { useLiveRunStore } from "@/lib/store";
import { api } from "@/lib/api";
import { RunDetails } from "@/lib/types";
import { ArrowLeft, Square, ArrowRight, CheckCircle2, AlertTriangle } from "lucide-react";

export default function RunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const runId = params?.run_id as string;

  // Real-time SSE connection
  useSSE(runId);

  const {
    events,
    currentAgent,
    liveState,
    status: liveStatus,
    isCompleted,
    error: liveError,
  } = useLiveRunStore();

  // Also query DB run details (for page reload or historical runs)
  const { data: runDetails, mutate } = useSWR<RunDetails>(
    runId ? `/runs/${runId}` : null,
    () => api.getRun(runId),
    { refreshInterval: isCompleted ? 0 : 4000 }
  );

  const [isCancelling, setIsCancelling] = useState(false);

  const displayState = liveState || runDetails?.state || null;
  const currentStatus = liveStatus !== "INITIALIZING" ? liveStatus : (runDetails?.status || "PROCESSING");
  const isFinished = isCompleted || runDetails?.status === "AWAITING_REVIEW" || runDetails?.status === "APPROVED";

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to stop this agent run?")) return;
    setIsCancelling(true);
    try {
      await api.cancelRun(runId);
      mutate();
    } catch (err) {
      console.error("Cancel failed:", err);
    } finally {
      setIsCancelling(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      <TopBar title={`Live Execution · ${runId.slice(0, 8)}`} />

      <main className="flex-1 flex flex-col p-6 space-y-4 overflow-hidden max-w-7xl w-full mx-auto">
        {/* Top Header Row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/runs">
              <Button size="icon" variant="ghost" className="h-8 w-8">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-slate-900 text-lg font-mono">
                  RUN-{runId.slice(0, 8)}
                </h3>
                <Badge
                  variant={
                    isFinished
                      ? "success"
                      : currentStatus === "CANCELLED" || currentStatus === "FAILED"
                      ? "destructive"
                      : "info"
                  }
                  className="font-mono text-[11px]"
                >
                  {currentStatus}
                </Badge>
              </div>
              <p className="text-xs text-slate-500">
                Topic: {displayState?.requirements?.topic || "Coding"} · Language: {displayState?.requirements?.target_language || "python"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!isFinished && currentStatus !== "CANCELLED" && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancel}
                disabled={isCancelling}
                className="gap-1.5 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                Stop Run
              </Button>
            )}

            {isFinished && (
              <Link href={`/review/${runId}`}>
                <Button size="sm" className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 shadow-sm">
                  Go to Review <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            )}
          </div>
        </div>

        {/* Completion Banner */}
        {isFinished && (
          <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-900">
            <div className="flex items-center gap-2 font-medium">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>
                Generation pipeline completed successfully! Scored and ready for human review.
              </span>
            </div>
            <Link href={`/review/${runId}`}>
              <Button size="sm" variant="outline" className="h-7 text-xs bg-white text-emerald-700 border-emerald-300 hover:bg-emerald-50">
                Review Workbench →
              </Button>
            </Link>
          </div>
        )}

        {/* Agent Workflow Stepper */}
        <RunTimeline
          currentAgent={currentAgent || (displayState?.current_agent as string) || "agent_a"}
          status={currentStatus}
          internalRetries={displayState?.internal_retry_count || 0}
          revisionCount={displayState?.revision_count || 0}
        />

        {/* Two-Column Execution View: Steps (40%) vs Preview (60%) */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-0 overflow-hidden">
          <div className="lg:col-span-5 h-full overflow-hidden">
            <AgentStepList
              events={events}
              historicalSteps={runDetails?.steps || []}
              currentAgent={currentAgent}
            />
          </div>

          <div className="lg:col-span-7 h-full overflow-hidden">
            <LivePreviewPanel state={displayState} />
          </div>
        </div>
      </main>
    </div>
  );
}
