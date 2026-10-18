"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import useSWR from "swr";
import { TopBar } from "@/components/layout/TopBar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { ArrowLeft, CheckCircle2, Clock, RotateCw, ExternalLink, Bot, Terminal } from "lucide-react";

const STEPS = [
  { id: "OPEN_PAGE", label: "Open Studio Portal" },
  { id: "SELECT_BANK", label: "Select Question Bank" },
  { id: "FILL_DETAILS", label: "Fill Metadata & HTML" },
  { id: "ADD_TEST_CASES", label: "Add Test Sets" },
  { id: "ADD_CODE", label: "Bind Code & Stubs" },
  { id: "VERIFY_AND_CONFIRM", label: "Verify & Save" },
];

export default function UploadJobDetailPage() {
  const params = useParams();
  const jobId = params?.job_id as string;

  const { data: job, isLoading, mutate } = useSWR(
    jobId ? `/uploads/${jobId}` : null,
    () => api.getUploadDetails(jobId),
    { refreshInterval: 2500 }
  );

  const stepsLog = job?.steps_log || [];
  const isComplete = job?.status === "COMPLETED";
  const isFailed = job?.status === "FAILED";

  const handleRetry = async () => {
    try {
      await api.retryUpload(jobId);
      mutate();
    } catch (err) {
      console.error("Retry failed:", err);
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <TopBar title={`Upload Job · UP-${jobId?.slice(0, 8)}`} />

      <main className="p-6 md:p-8 space-y-6 max-w-6xl w-full mx-auto">
        {/* Header Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/uploads">
              <Button size="icon" variant="ghost" className="h-8 w-8">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-slate-900 text-lg font-mono">
                  UP-{jobId?.slice(0, 8)}
                </h3>
                <Badge
                  variant={isComplete ? "success" : isFailed ? "destructive" : "info"}
                  className="font-mono text-xs"
                >
                  {job?.status || "QUEUED"}
                </Badge>
              </div>
              <p className="text-xs text-slate-500">
                Target Bank: <strong>{job?.bank_id || "Embedded-Capgemini"}</strong> · Question:{" "}
                <Link
                  href={`/review/${job?.question_id}`}
                  className="text-blue-600 hover:underline font-mono"
                >
                  Q-{job?.question_id?.slice(0, 8)}
                </Link>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isFailed && (
              <Button size="sm" onClick={handleRetry} className="gap-1 text-xs">
                <RotateCw className="w-3.5 h-3.5" />
                Retry Upload
              </Button>
            )}
            <Link href={`/review/${job?.question_id}`}>
              <Button size="sm" variant="outline" className="gap-1 text-xs">
                Review Question <ExternalLink className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Upload Progression Stepper */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
          <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
            Automated Form Progression Steps
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            {STEPS.map((step, idx) => {
              const executed = stepsLog.find((s: any) => s.step === step.id);
              const isStepDone = Boolean(executed && executed.status === "COMPLETED");

              return (
                <div
                  key={step.id}
                  className={`p-3 rounded-lg border text-center space-y-1 transition-all ${
                    isStepDone
                      ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                      : "bg-slate-50 border-slate-200 text-slate-400"
                  }`}
                >
                  <div className="flex items-center justify-center">
                    {isStepDone ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <span className="w-4 h-4 rounded-full border border-slate-300 text-[10px] flex items-center justify-center font-mono">
                        {idx + 1}
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] font-semibold truncate">{step.label}</div>
                  <div className="text-[10px] font-mono text-slate-500">
                    {executed?.duration_ms ? `${executed.duration_ms}ms` : "Pending"}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Execution Log & Payload JSON Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Step Log (6 cols) */}
          <Card className="lg:col-span-6">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Terminal className="w-4 h-4 text-blue-600" />
                Browser Automation Trace
              </CardTitle>
              <CardDescription>Playwright actions executed on iMocha DOM</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              {stepsLog.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <Clock className="w-6 h-6 mx-auto mb-2 text-slate-300 animate-spin" />
                  <p>Queued for execution...</p>
                </div>
              ) : (
                stepsLog.map((log: any, i: number) => (
                  <div
                    key={i}
                    className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1 font-mono text-[11px]"
                  >
                    <div className="flex justify-between font-semibold text-slate-800">
                      <span>{log.name}</span>
                      <span className="text-emerald-600">{log.duration_ms}ms</span>
                    </div>
                    <div className="text-slate-400 text-[10px]">{log.timestamp}</div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Payload JSON (6 cols) */}
          <Card className="lg:col-span-6">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Verified Payload JSON</CardTitle>
              <CardDescription>Standardized data model committed to portal</CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="p-4 bg-slate-950 text-slate-200 font-mono text-[11px] rounded-lg max-h-[420px] overflow-y-auto leading-relaxed">
                <code>{JSON.stringify(job?.payload_json || {}, null, 2)}</code>
              </pre>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
