"use client";

import { Card } from "@/components/ui/card";
import { DashboardStats } from "@/lib/types";
import {
  Sparkles,
  CheckCircle2,
  Clock,
  ThumbsUp,
  CloudUpload,
  Upload,
} from "lucide-react";

interface StatCardsProps {
  stats: DashboardStats | null;
  loading: boolean;
}

export function StatCards({ stats, loading }: StatCardsProps) {
  const cards = [
    {
      label: "Generated",
      value: stats?.generated ?? 0,
      icon: Sparkles,
      color: "text-blue-600 bg-blue-50 border-blue-200",
      description: "Total questions generated",
    },
    {
      label: "QA Passed",
      value: stats?.qa_passed ?? 0,
      icon: CheckCircle2,
      color: "text-emerald-600 bg-emerald-50 border-emerald-200",
      description: "Passed automated quality gate",
    },
    {
      label: "Awaiting Review",
      value: stats?.awaiting_review ?? 0,
      icon: Clock,
      color: "text-amber-600 bg-amber-50 border-amber-200",
      description: "Pending human assessment",
    },
    {
      label: "Approved",
      value: stats?.approved ?? 0,
      icon: ThumbsUp,
      color: "text-indigo-600 bg-indigo-50 border-indigo-200",
      description: "Ready for export/upload",
    },
    {
      label: "Upload Queued",
      value: stats?.upload_queued ?? 0,
      icon: CloudUpload,
      color: "text-slate-600 bg-slate-100 border-slate-200",
      description: "Pending upload worker",
    },
    {
      label: "Uploaded",
      value: stats?.uploaded ?? 0,
      icon: Upload,
      color: "text-purple-600 bg-purple-50 border-purple-200",
      description: "Successfully on iMocha",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.label} className="p-4 flex flex-col justify-between hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">{card.label}</span>
              <div className={`p-1.5 rounded-lg border ${card.color}`}>
                <Icon className="w-3.5 h-3.5" />
              </div>
            </div>
            <div className="mt-3">
              {loading ? (
                <div className="h-7 w-12 bg-slate-200 animate-pulse rounded" />
              ) : (
                <div className="text-2xl font-bold tracking-tight text-slate-900">{card.value}</div>
              )}
              <p className="text-[11px] text-slate-400 mt-0.5 truncate">{card.description}</p>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
