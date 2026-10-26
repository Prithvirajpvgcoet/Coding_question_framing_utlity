"use client";

import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { QuestionSummary } from "@/lib/types";
import { Eye, ExternalLink } from "lucide-react";

interface QuestionTableProps {
  questions: QuestionSummary[];
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
  onSelectAll: () => void;
  isLoading?: boolean;
}

export function QuestionTable({
  questions,
  selectedIds,
  onToggleSelect,
  onSelectAll,
  isLoading,
}: QuestionTableProps) {
  if (isLoading) {
    return (
      <div className="p-8 text-center text-slate-500 font-medium">
        Loading questions...
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="p-12 text-center text-slate-500">
        <p className="text-base font-semibold text-slate-700">No questions found</p>
        <p className="text-sm mt-1">Try tweaking your search or filters.</p>
      </div>
    );
  }

  const allSelected =
    questions.length > 0 && selectedIds.length === questions.length;

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
      <Table>
        <TableHeader>
          <TableRow className="bg-slate-50 border-b border-slate-200">
            <TableHead className="w-12">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={onSelectAll}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
            </TableHead>
            <TableHead className="w-28 font-semibold text-slate-700">ID</TableHead>
            <TableHead className="font-semibold text-slate-700">Topic</TableHead>
            <TableHead className="w-24 font-semibold text-slate-700">Difficulty</TableHead>
            <TableHead className="w-24 font-semibold text-slate-700">Language</TableHead>
            <TableHead className="w-36 font-semibold text-slate-700">Status</TableHead>
            <TableHead className="w-32 font-semibold text-slate-700">Created</TableHead>
            <TableHead className="w-20 text-right font-semibold text-slate-700">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody className="divide-y divide-slate-100">
          {questions.map((q) => {
            const qId = q.question_id || (q as any).id || "";
            const isSelected = selectedIds.includes(qId);
            const isApproved = q.status === "APPROVED";
            const isNeedsReview =
              q.status === "AWAITING_REVIEW" || q.status === "NEEDS_HUMAN_REVIEW";

            return (
              <TableRow
                key={qId}
                className={isSelected ? "bg-blue-50/50" : ""}
              >
                <TableCell>
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => onToggleSelect(qId)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                </TableCell>
                <TableCell className="font-mono text-xs font-semibold text-slate-800">
                  Q-{qId ? qId.slice(0, 8) : "--------"}
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
                        : "secondary"
                    }
                    className="text-[11px]"
                  >
                    {q.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs text-slate-500">
                  {q.created_at
                    ? new Date(q.created_at).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })
                    : "—"}
                </TableCell>
                <TableCell className="text-right">
                  <Link href={`/runs/${qId}`}>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-slate-500 hover:text-blue-600">
                      <Eye className="h-4 w-4" />
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
