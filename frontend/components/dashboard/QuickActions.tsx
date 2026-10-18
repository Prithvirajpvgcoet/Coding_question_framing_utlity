"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Sparkles, Layers, RefreshCw, BookOpen } from "lucide-react";

interface QuickActionsProps {
  onRetryFailed?: () => void;
  failedCount?: number;
}

export function QuickActions({ onRetryFailed, failedCount = 0 }: QuickActionsProps) {
  return (
    <div className="space-y-3">
      <Link href="/generate" className="block">
        <Button className="w-full justify-start gap-2 h-10 font-medium">
          <Sparkles className="w-4 h-4 text-blue-200" />
          Generate New Question
        </Button>
      </Link>

      <Link href="/generate?tab=batch" className="block">
        <Button variant="outline" className="w-full justify-start gap-2 h-10 font-medium text-slate-700">
          <Layers className="w-4 h-4 text-slate-500" />
          Batch Generation
        </Button>
      </Link>

      <Link href="/library" className="block">
        <Button variant="outline" className="w-full justify-start gap-2 h-10 font-medium text-slate-700">
          <BookOpen className="w-4 h-4 text-slate-500" />
          Browse Question Library
        </Button>
      </Link>

      {failedCount > 0 && onRetryFailed && (
        <Button
          variant="secondary"
          className="w-full justify-start gap-2 h-10 font-medium text-amber-800 bg-amber-50 hover:bg-amber-100 border border-amber-200"
          onClick={onRetryFailed}
        >
          <RefreshCw className="w-4 h-4 text-amber-600" />
          Retry Failed ({failedCount})
        </Button>
      )}
    </div>
  );
}
