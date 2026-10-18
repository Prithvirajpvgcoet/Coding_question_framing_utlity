"use client";

import { useState } from "react";
import useSWR from "swr";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { QuestionBankItem } from "@/lib/types";
import { Check, X, CloudUpload, FolderPlus, Loader2 } from "lucide-react";

interface BulkActionBarProps {
  selectedIds: string[];
  onSuccess: () => void;
  onClear: () => void;
}

export function BulkActionBar({ selectedIds, onSuccess, onClear }: BulkActionBarProps) {
  const { data: banks } = useSWR<QuestionBankItem[]>("/banks", () => api.listBanks());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedBankId, setSelectedBankId] = useState<string>("");

  if (selectedIds.length === 0) return null;

  const handleBulkApprove = async () => {
    setIsSubmitting(true);
    try {
      await api.submitBulkFeedback({
        question_ids: selectedIds,
        action: "APPROVE",
      });
      onSuccess();
      onClear();
    } catch (err) {
      console.error("Bulk approve failed:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBulkReject = async () => {
    const feedback = prompt("Enter revision feedback for selected questions:");
    if (!feedback) return;
    setIsSubmitting(true);
    try {
      await api.submitBulkFeedback({
        question_ids: selectedIds,
        action: "REJECT",
        feedback_text: feedback,
      });
      onSuccess();
      onClear();
    } catch (err) {
      console.error("Bulk reject failed:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAssignToBank = async (bankId: string) => {
    if (!bankId) return;
    setIsSubmitting(true);
    try {
      await api.addQuestionsToBank(bankId, selectedIds);
      onSuccess();
      onClear();
    } catch (err) {
      console.error("Assign to bank failed:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-900 text-white rounded-xl px-5 py-3 shadow-lg flex flex-wrap items-center justify-between gap-4 animate-in fade-in slide-in-from-bottom-2">
      <div className="flex items-center gap-3">
        <span className="w-6 h-6 rounded-full bg-blue-600 text-xs font-bold flex items-center justify-center">
          {selectedIds.length}
        </span>
        <span className="text-xs font-medium text-slate-200">
          question{selectedIds.length > 1 ? "s" : ""} selected
        </span>
        <button
          onClick={onClear}
          className="text-xs text-slate-400 hover:text-white underline ml-2"
        >
          Deselect all
        </button>
      </div>

      <div className="flex items-center gap-2">
        <Button
          size="sm"
          onClick={handleBulkApprove}
          disabled={isSubmitting}
          className="h-8 text-xs bg-emerald-600 hover:bg-emerald-700 text-white gap-1"
        >
          {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
          Approve Selected
        </Button>

        <Button
          size="sm"
          variant="outline"
          onClick={handleBulkReject}
          disabled={isSubmitting}
          className="h-8 text-xs bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700 gap-1"
        >
          <X className="w-3.5 h-3.5 text-red-400" />
          Reject
        </Button>

        <Button
          size="sm"
          onClick={async () => {
            setIsSubmitting(true);
            try {
              await api.createBulkUpload(selectedIds, selectedBankId || undefined);
              onSuccess();
              onClear();
            } finally {
              setIsSubmitting(false);
            }
          }}
          disabled={isSubmitting}
          className="h-8 text-xs bg-blue-600 hover:bg-blue-700 text-white gap-1"
        >
          <CloudUpload className="w-3.5 h-3.5" />
          Queue for Upload
        </Button>

        {banks && banks.length > 0 && (
          <select
            value={selectedBankId}
            onChange={(e) => {
              setSelectedBankId(e.target.value);
              handleAssignToBank(e.target.value);
            }}
            disabled={isSubmitting}
            className="h-8 text-xs bg-slate-800 border border-slate-700 text-slate-200 rounded-lg px-2.5 focus:outline-none"
          >
            <option value="">Add to Bank...</option>
            {banks.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
}
