"use client";

import Link from "next/link";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { QuestionSummary } from "@/lib/types";
import { AlertCircle, ArrowUpRight } from "lucide-react";

interface AttentionTableProps {
  questions: QuestionSummary[];
  loading: boolean;
}

export function AttentionTable({ questions, loading }: AttentionTableProps) {
  if (loading) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        <div className="inline-block w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2" />
        <p>Loading attention queue...</p>
      </div>
    );
  }

  if (!questions || questions.length === 0) {
    return (
      <div className="p-10 text-center text-sm text-slate-500">
        <div className="w-10 h-10 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3">
          ✓
        </div>
        <p className="font-medium text-slate-700">All questions are reviewed!</p>
        <p className="text-xs text-slate-400 mt-1">No items currently need manual feedback or retry.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Question ID</TableHead>
            <TableHead>Topic</TableHead>
            <TableHead>Difficulty</TableHead>
            <TableHead>Language</TableHead>
            <TableHead>Issue / Status</TableHead>
            <TableHead className="text-right">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {questions.map((q) => {
            const shortId = q.question_id.slice(0, 8);
            const isFailed = q.status === "QA_FAILED";

            return (
              <TableRow key={q.question_id}>
                <TableCell className="font-mono text-xs font-semibold text-slate-800">
                  Q-{shortId}
                </TableCell>
                <TableCell className="font-medium text-slate-900">{q.topic || "Algorithmic"}</TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-[11px] capitalize">
                    {q.difficulty?.toLowerCase() || "medium"}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs text-slate-600 capitalize">{q.language || "python"}</TableCell>
                <TableCell>
                  <Badge variant={isFailed ? "destructive" : "warning"} className="gap-1 text-[11px]">
                    <AlertCircle className="w-3 h-3" />
                    {isFailed ? "QA Gate Failed" : "Human Review Needed"}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Link href={`/review/${q.question_id}`}>
                    <Button size="sm" variant="outline" className="gap-1 text-xs h-7">
                      Review <ArrowUpRight className="w-3 h-3" />
                    </Button>
                  </Link>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
