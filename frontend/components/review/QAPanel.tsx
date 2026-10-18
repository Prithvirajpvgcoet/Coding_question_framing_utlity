"use client";

import { QualityAssessment, FinalQA } from "@/lib/types";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, XCircle, Award } from "lucide-react";

interface QAPanelProps {
  quality?: QualityAssessment;
  finalQa?: FinalQA;
}

export function QAPanel({ quality, finalQa }: QAPanelProps) {
  const scores = quality?.scores || {};
  const avgScore = quality?.avg_score || 0;
  // Convert 1-5 or 0-10 scale to 0-100 if necessary
  const normalizedScore = avgScore <= 5 ? Math.round(avgScore * 20) : Math.round(avgScore);
  const isPass = quality?.pass ?? true;

  const subCriteria = [
    { label: "Clarity & Readability", val: scores.clarity ?? 4, max: 5 },
    { label: "Edge Case Coverage", val: scores.edge_cases ?? 4, max: 5 },
    { label: "Algorithmic Efficiency", val: scores.efficiency ?? 4, max: 5 },
    { label: "Formatting & Standards", val: scores.formatting ?? 4, max: 5 },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <Award className="w-4 h-4 text-blue-600" />
          Agent D Quality Assessment
        </h4>
        <span
          className={`px-2 py-0.5 rounded text-xs font-bold ${
            isPass ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"
          }`}
        >
          {isPass ? "PASSED" : "FAILED"}
        </span>
      </div>

      {/* Main Score Gauge */}
      <div className="flex items-center gap-4 bg-slate-50 p-3 rounded-lg border border-slate-200">
        <div className="text-3xl font-extrabold text-slate-900 font-mono">
          {normalizedScore}
          <span className="text-sm font-normal text-slate-400">/100</span>
        </div>
        <div className="flex-1 space-y-1">
          <div className="flex justify-between text-xs text-slate-600 font-medium">
            <span>Overall Rubric Score</span>
            <span>Threshold: 80/100</span>
          </div>
          <Progress
            value={normalizedScore}
            max={100}
            className="h-2"
            indicatorClassName={isPass ? "bg-emerald-600" : "bg-red-500"}
          />
        </div>
      </div>

      {/* Sub-Criteria Breakdown */}
      <div className="space-y-3 pt-1">
        {subCriteria.map((crit) => {
          const pct = (crit.val / crit.max) * 100;
          return (
            <div key={crit.label} className="space-y-1">
              <div className="flex justify-between text-xs text-slate-600">
                <span>{crit.label}</span>
                <span className="font-semibold text-slate-800 font-mono">
                  {crit.val} / {crit.max}
                </span>
              </div>
              <Progress value={pct} max={100} className="h-1.5" />
            </div>
          );
        })}
      </div>

      {/* Scorer Feedback */}
      {quality?.scorer_feedback && (
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700 space-y-1">
          <strong className="text-slate-900">Scorer Feedback:</strong>
          <p className="text-[11px] text-slate-600 leading-relaxed font-mono whitespace-pre-wrap">
            {quality.scorer_feedback}
          </p>
        </div>
      )}
    </div>
  );
}
