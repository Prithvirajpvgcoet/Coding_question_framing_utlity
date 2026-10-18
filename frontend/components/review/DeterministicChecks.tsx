"use client";

import { FinalQA } from "@/lib/types";
import { CheckCircle2, XCircle, ShieldCheck } from "lucide-react";

interface DeterministicChecksProps {
  finalQa?: FinalQA;
  testCasesCount?: number;
}

export function DeterministicChecks({
  finalQa,
  testCasesCount = 0,
}: DeterministicChecksProps) {
  const checks = finalQa?.deterministic_checks || {};

  const items = [
    {
      label: "HTML Schema Valid",
      description: "Well-formed tags, semantic structure",
      passed: checks.html_valid ?? true,
    },
    {
      label: "Sandbox Execution Passed",
      description: "Python solution passed all sample tests",
      passed: checks.sandbox_passed ?? true,
    },
    {
      label: "Required Fields Present",
      description: "Title, description, stub, and solution",
      passed: checks.required_fields ?? true,
    },
    {
      label: "Dedup Semantic Check",
      description: "No cosine/n-gram collision with bank",
      passed: checks.no_duplicates ?? true,
    },
    {
      label: "Test Case Policy",
      description: `Target test cases present (${testCasesCount} total)`,
      passed: testCasesCount >= 4,
    },
  ];

  const allPassed = items.every((i) => i.passed);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          Agent G Deterministic Checks
        </h4>
        <span
          className={`px-2 py-0.5 rounded text-xs font-bold ${
            allPassed ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
          }`}
        >
          {allPassed ? "READY FOR UPLOAD" : "ACTION REQUIRED"}
        </span>
      </div>

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.label} className="flex items-start gap-2.5 text-xs">
            {item.passed ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
            )}
            <div>
              <div className="font-semibold text-slate-800">{item.label}</div>
              <div className="text-[11px] text-slate-500">{item.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
