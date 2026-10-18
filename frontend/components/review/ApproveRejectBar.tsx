"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, X, AlertTriangle, Loader2 } from "lucide-react";

interface ApproveRejectBarProps {
  questionId: string;
  version: number;
  status: string;
  isApprovalBlocked?: boolean;
  onApprove: () => Promise<void>;
  onReject: (feedback: string) => Promise<void>;
}

export function ApproveRejectBar({
  questionId,
  version,
  status,
  isApprovalBlocked = false,
  onApprove,
  onReject,
}: ApproveRejectBarProps) {
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      await onApprove();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackText.trim()) return;
    setIsSubmitting(true);
    try {
      await onReject(feedbackText);
      setShowRejectModal(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <div className="bg-white border-b border-slate-200 px-6 py-3 sticky top-16 z-20 flex flex-wrap items-center justify-between gap-4 shadow-xs">
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm font-bold text-slate-800">
            Q-{questionId.slice(0, 8)}
          </span>
          <Badge variant="outline" className="text-xs font-mono">
            v{version}
          </Badge>
          <Badge
            variant={
              status === "APPROVED"
                ? "success"
                : status === "NEEDS_HUMAN_REVIEW" || status === "QA_FAILED"
                ? "warning"
                : "info"
            }
            className="text-xs"
          >
            {status}
          </Badge>
        </div>

        <div className="flex items-center gap-3">
          <Button
            size="sm"
            variant="outline"
            className="text-red-700 border-red-200 hover:bg-red-50 gap-1.5 text-xs h-8"
            onClick={() => setShowRejectModal(true)}
            disabled={isSubmitting}
          >
            <X className="w-3.5 h-3.5" />
            Reject & Revise
          </Button>

          <Button
            size="sm"
            className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5 text-xs h-8 shadow-sm"
            onClick={handleApprove}
            disabled={isSubmitting || isApprovalBlocked || status === "APPROVED"}
          >
            {isSubmitting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Check className="w-3.5 h-3.5" />
            )}
            {status === "APPROVED" ? "Approved ✓" : "Approve Assessment"}
          </Button>
        </div>
      </div>

      {/* Approval Blocked Warning Banner */}
      {isApprovalBlocked && (
        <div className="bg-amber-50 border-b border-amber-200 px-6 py-2.5 flex items-center gap-2 text-xs text-amber-900 font-medium">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            <strong>Approval Blocked:</strong> Automated checks detected failures (e.g. failing sandbox tests or invalid HTML). Resolve the issues or trigger revision before approving.
          </span>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
            <h3 className="font-semibold text-slate-900 text-base">Reject with Feedback</h3>
            <p className="text-xs text-slate-500">
              Agent E will analyze your feedback, categorize it (Requirements, Logic, or Formatting), and route it to Agent A, C, or D for revision.
            </p>
            <form onSubmit={handleRejectSubmit} className="space-y-4">
              <textarea
                rows={4}
                required
                placeholder="Explain what needs to be improved (e.g., 'Make test cases stricter', 'Simplify problem description', 'Edge case with negative values fails')..."
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-lg p-3 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 resize-none"
              />
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowRejectModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  variant="destructive"
                  disabled={isSubmitting || !feedbackText.trim()}
                >
                  {isSubmitting ? "Dispatching Revision..." : "Submit Revision"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
