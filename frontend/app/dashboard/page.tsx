"use client";

import useSWR from "swr";
import { TopBar } from "@/components/layout/TopBar";
import { StatCards } from "@/components/dashboard/StatCards";
import { AttentionTable } from "@/components/dashboard/AttentionTable";
import { QuickActions } from "@/components/dashboard/QuickActions";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { DashboardStats, QuestionSummary } from "@/lib/types";

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useSWR<DashboardStats>(
    "/dashboard/stats",
    () => api.getDashboardStats(),
    { refreshInterval: 5000 }
  );

  const { data: questions, isLoading: questionsLoading, mutate } = useSWR<QuestionSummary[]>(
    "/questions",
    () => api.listQuestions({ limit: 50 }),
    { refreshInterval: 5000 }
  );

  // Filter for attention needed: QA_FAILED or NEEDS_HUMAN_REVIEW
  const attentionList = (questions || []).filter(
    (q) => q.status === "QA_FAILED" || q.status === "NEEDS_HUMAN_REVIEW"
  );

  const handleRetryFailed = async () => {
    const failedIds = attentionList.map((q) => q.question_id);
    if (failedIds.length === 0) return;
    try {
      await api.submitBulkFeedback({
        question_ids: failedIds,
        action: "REJECT",
        feedback_text: "Automated retry triggered from studio dashboard.",
      });
      mutate();
    } catch (err) {
      console.error("Retry failed:", err);
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <TopBar title="Studio Overview" />

      <main className="p-6 md:p-8 space-y-8 max-w-7xl w-full mx-auto">
        {/* Stat Cards */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">Metrics</h3>
            <span className="text-xs text-slate-500">Auto-refreshing every 5s</span>
          </div>
          <StatCards stats={stats || null} loading={statsLoading} />
        </section>

        {/* Main Grid: Attention Table + Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Attention Queue (2 cols) */}
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <span>Attention Needed</span>
                  {attentionList.length > 0 && (
                    <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                      {attentionList.length}
                    </span>
                  )}
                </CardTitle>
                <CardDescription>
                  Questions flagged by Agent D/G quality checks or needing manual review
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <AttentionTable questions={attentionList} loading={questionsLoading} />
            </CardContent>
          </Card>

          {/* Quick Actions (1 col) */}
          <div className="space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Quick Actions</CardTitle>
                <CardDescription>Launch pipeline or manage questions</CardDescription>
              </CardHeader>
              <CardContent>
                <QuickActions
                  onRetryFailed={handleRetryFailed}
                  failedCount={attentionList.length}
                />
              </CardContent>
            </Card>

            <Card className="bg-slate-900 text-slate-100 border-slate-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-100">Active Workflow</CardTitle>
                <CardDescription className="text-slate-400">
                  7-Agent Graph Architecture
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-slate-300">
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span>LLM Provider</span>
                  <span className="font-mono text-blue-400">Groq Cloud</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span>Code Verification</span>
                  <span className="font-mono text-emerald-400">Isolated Sandbox</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span>Target Platform</span>
                  <span className="font-mono text-purple-400">iMocha Studio</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
