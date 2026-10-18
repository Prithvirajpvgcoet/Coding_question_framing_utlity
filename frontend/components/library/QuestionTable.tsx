"use client";

import Link from "next/link";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { QuestionSummary } from "@/lib/types";
import { ArrowUpRight } from "lucide-react";

interface QuestionTableProps {
  questions: QuestionSummary[];
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
  onSelectAll: () => void;
}

export function QuestionTable({
  questions,
  selectedIds,
  onToggleSelect,
  onSelectAll,
}: QuestionTableProps) {
  const isAllSelected = questions.length > 0 && selectedIds.length === questions.length;

  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">
              <input
                type="checkbox"
                checked={isAllSelected}
                onChange={onSelectAll}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
            </TableHead>
            <TableHead>Question ID</TableHead>
            <TableHead>Topic</TableHead>
            <TableHead>Difficulty</TableHead>
            <TableHead>Language</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Version</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="text-right">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {questions.map((q) => {
            const isSelected = selectedIds.includes(q.question_id);
            const isApproved = q.status === "APPROVED";
            const isNeedsReview = q.status === "AWAITING_REVIEW" || q.status === "NEEDS_HUMAN_REVIEW";

            return (
              <TableRow
                key={q.question_id}
                className={isSelected ? "bg-blue-50/50" : ""}
              >
                <TableCell>
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => onToggleSelect(q.question_id)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                </TableCell>
                <TableCell className="font-mono text-xs font-semibold text-slate-800">
                  Q-{q.question_id.slice(0, 8)}
                </TableCell>
                <TableCell className="font-medium text-slate-900">{q.topic || "Algorithmic"}</TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-[11px] capitalize">
                    {q.difficulty?.toLowerCase() || "medium"}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs text-slate-600 capitalize">{q.language || "python"}</TableCell>
                <TableCell>
                  <Badge
                    variant={
                      isApproved
                        ? "success"
                        : isNeedsReview
                        ? "warning"
                        : q.status === "QA_FAILED"
                        ? "destructive"
                        : "info"
                    }
                    className="text-[11px]"
                  >
                    {q.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs font-mono text-slate-500">v{q.version || 1}</TableCell>
                <TableCell className="text-xs text-slate-400">
                  {q.created_at ? new Date(q.created_at).toLocaleDateString() : "Recently"}
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
