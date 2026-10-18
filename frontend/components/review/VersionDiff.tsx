"use client";

import { useState } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { History, GitCommit } from "lucide-react";

interface VersionDiffProps {
  questionId: string;
  currentVersion: number;
}

export function VersionDiff({ questionId, currentVersion }: VersionDiffProps) {
  const { data: versionData, isLoading } = useSWR(
    `/questions/${questionId}/versions`,
    () => api.getVersions(questionId)
  );

  const versions = versionData?.versions || [];

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div>
          <h4 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <History className="w-4 h-4 text-blue-600" />
            Revision History & State Snapshots
          </h4>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit trail of human feedback triggers and re-entry routing iterations
          </p>
        </div>
        <Badge variant="outline" className="font-mono text-xs">
          Current: v{currentVersion}
        </Badge>
      </div>

      {isLoading ? (
        <div className="text-center py-10 text-xs text-slate-500">Loading version logs...</div>
      ) : versions.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <GitCommit className="w-8 h-8 mx-auto mb-2 text-slate-300" />
          <p className="text-xs font-medium">Initial Version (v1)</p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            No revision iterations recorded yet. If rejected with feedback, revision snapshots will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {versions.map((v) => (
            <div
              key={v.version}
              className="p-4 border border-slate-200 rounded-lg bg-slate-50 flex items-center justify-between text-xs"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-900 font-mono">Version {v.version}</span>
                  <Badge variant="secondary" className="text-[10px]">
                    Triggered by: {v.triggered_by || "Human Review"}
                  </Badge>
                </div>
                <div className="text-slate-500 text-[11px]">
                  Re-entry Node: <strong className="text-blue-600 font-mono">{v.re_entry_agent || "agent_c"}</strong> · Recorded {v.created_at || "recently"}
                </div>
              </div>
              <Badge variant="outline" className="font-mono text-[10px]">
                Preserved
              </Badge>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
