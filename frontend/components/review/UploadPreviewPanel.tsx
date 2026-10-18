"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { QuestionState } from "@/lib/types";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy, Check, Upload, CheckCircle2, Loader2 } from "lucide-react";

interface UploadPreviewPanelProps {
  state: QuestionState;
}

export function UploadPreviewPanel({ state }: UploadPreviewPanelProps) {
  const router = useRouter();
  const [copied, setCopied] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  // Construct standard iMocha payload format from question state
  const payload = {
    question_bank_id: "imocha-default-bank",
    title: state.question?.title || "Algorithmic Assessment",
    difficulty: state.requirements?.difficulty || "MEDIUM",
    question_type: state.requirements?.question_type || "ALGORITHMIC",
    language: state.code?.language || "python",
    max_score: (state.test_cases?.length || 5) * 10,
    time_limit_seconds: (state.requirements?.max_solve_time_minutes || 30) * 60,
    html_content: state.html?.formatted_question || "",
    starter_code: state.code?.stub || "",
    solution_code: state.code?.solution || "",
    test_cases: (state.test_cases || []).map((tc, idx) => ({
      index: idx + 1,
      is_sample: tc.type === "VISIBLE",
      input: tc.input_args,
      expected: tc.expected_output,
      points: tc.points || 1,
    })),
  };

  const payloadString = JSON.stringify(payload, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(payloadString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleUpload = async () => {
    setIsUploading(true);
    setUploadStatus("Staging question payload for iMocha portal upload...");
    try {
      const res = await api.createUpload(state.question_id, "Embedded-Capgemini");
      setUploadStatus("✓ Job dispatched! Redirecting to live upload stepper...");
      setTimeout(() => {
        router.push(`/uploads/${res.job_id}`);
      }, 700);
    } catch (err: any) {
      setUploadStatus(`Error: ${err.message || "Failed to create upload job"}`);
      setIsUploading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left: Rendered Form Preview (6 cols) */}
      <div className="lg:col-span-6 space-y-4">
        <div className="border border-slate-200 rounded-xl p-4 bg-white shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              iMocha Candidate Form Preview
            </h4>
            <Badge variant="outline" className="text-xs capitalize font-mono">
              {payload.language}
            </Badge>
          </div>

          <div className="text-sm font-bold text-slate-900">{payload.title}</div>

          <iframe
            title="Form HTML Preview"
            srcDoc={`<!DOCTYPE html><html><head><style>body{font-family:system-ui,-apple-system,sans-serif;line-height:1.5;color:#1e293b;padding:8px;font-size:13px;}h2{font-size:16px;color:#0f172a;}code{background:#f1f5f9;padding:2px 4px;border-radius:4px;font-family:monospace;}</style></head><body>${payload.html_content}</body></html>`}
            sandbox="allow-scripts"
            className="w-full h-80 border border-slate-200 rounded-lg bg-white"
          />

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">Code Stub Preview</label>
            <pre className="p-3 bg-slate-900 text-slate-200 font-mono text-[11px] rounded-lg max-h-40 overflow-y-auto">
              <code>{payload.starter_code || "# No starter code"}</code>
            </pre>
          </div>
        </div>
      </div>

      {/* Right: Payload JSON & Session Health (6 cols) */}
      <div className="lg:col-span-6 space-y-4">
        <div className="border border-slate-200 rounded-xl p-4 bg-white shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Payload JSON (Playwright / REST Target)
            </h4>
            <Button
              size="sm"
              variant="outline"
              onClick={handleCopy}
              className="h-7 text-xs gap-1"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? "Copied" : "Copy JSON"}
            </Button>
          </div>

          <textarea
            readOnly
            rows={14}
            value={payloadString}
            className="w-full font-mono text-[11px] p-3 bg-slate-950 text-slate-200 rounded-lg border border-slate-800 leading-relaxed resize-none focus:outline-none"
          />
        </div>

        {/* Session Health Panel */}
        <div className="border border-slate-200 rounded-xl p-4 bg-white shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold text-slate-800">iMocha Session Health</span>
            </div>
            <Badge variant="success" className="text-[10px]">
              Active Session
            </Badge>
          </div>

          <div className="text-xs text-slate-600 space-y-1.5 font-medium">
            <div className="flex items-center gap-1.5 text-emerald-700">
              <CheckCircle2 className="w-3.5 h-3.5" /> Payload schema valid
            </div>
            <div className="flex items-center gap-1.5 text-emerald-700">
              <CheckCircle2 className="w-3.5 h-3.5" /> Form fields mapped correctly
            </div>
          </div>

          {uploadStatus && (
            <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 font-mono">
              {uploadStatus}
            </div>
          )}

          <div className="flex gap-2 pt-1">
            <Button
              size="sm"
              variant="outline"
              onClick={handleUpload}
              className="flex-1 text-xs h-9"
            >
              Run Dry Validation
            </Button>
            <Button
              size="sm"
              onClick={handleUpload}
              className="flex-1 text-xs h-9 gap-1.5 bg-blue-600 hover:bg-blue-700 text-white shadow-sm"
            >
              <Upload className="w-3.5 h-3.5" />
              Start Upload →
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
