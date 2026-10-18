"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { TopBar } from "@/components/layout/TopBar";
import { ApproveRejectBar } from "@/components/review/ApproveRejectBar";
import { QuestionDetailForm } from "@/components/review/QuestionDetailForm";
import { TestCasesTable } from "@/components/review/TestCasesTable";
import { CodeSolutionPanel } from "@/components/review/CodeSolutionPanel";
import { UploadPreviewPanel } from "@/components/review/UploadPreviewPanel";
import { VersionDiff } from "@/components/review/VersionDiff";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { FileText, CheckSquare, UploadCloud, History, Loader2 } from "lucide-react";

export default function ReviewPage() {
  const params = useParams();
  const router = useRouter();
  const questionId = params?.question_id as string;
  const [activeTab, setActiveTab] = useState<string>("details");

  const { data: questionData, isLoading, mutate } = useSWR(
    questionId ? `/questions/${questionId}` : null,
    () => api.getQuestion(questionId)
  );

  const state = questionData?.state;
  const status = questionData?.status || "AWAITING_REVIEW";
  const version = questionData?.version || 1;

  const isBlocked = state?.final_qa?.approved === false || state?.quality?.pass === false;

  const handleApprove = async () => {
    await api.submitFeedback({
      question_id: questionId,
      action: "APPROVE",
    });
    mutate();
  };

  const handleReject = async (feedbackText: string) => {
    await api.submitFeedback({
      question_id: questionId,
      action: "REJECT",
      feedback_text: feedbackText,
    });
    // Redirect to runs to monitor the feedback revision execution
    router.push(`/runs/${questionId}`);
  };

  if (isLoading || !state) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-screen text-slate-500 space-y-2">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        <p className="text-sm">Loading assessment review workbench...</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      <TopBar title={`Review Workbench · ${questionId.slice(0, 8)}`} />

      <ApproveRejectBar
        questionId={questionId}
        version={version}
        status={status}
        isApprovalBlocked={isBlocked && status !== "APPROVED"}
        onApprove={handleApprove}
        onReject={handleReject}
      />

      <main className="p-6 md:p-8 space-y-6 max-w-7xl w-full mx-auto">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="border-b border-slate-200 pb-2">
            <TabsList className="bg-slate-100">
              <TabsTrigger value="details" className="gap-1.5 text-xs">
                <FileText className="w-3.5 h-3.5" />
                Question Details
              </TabsTrigger>
              <TabsTrigger value="tests" className="gap-1.5 text-xs">
                <CheckSquare className="w-3.5 h-3.5" />
                Tests & Solution
              </TabsTrigger>
              <TabsTrigger value="upload" className="gap-1.5 text-xs">
                <UploadCloud className="w-3.5 h-3.5" />
                Upload Preview
              </TabsTrigger>
              <TabsTrigger value="versions" className="gap-1.5 text-xs">
                <History className="w-3.5 h-3.5" />
                Version History
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="details" className="pt-4">
            <QuestionDetailForm state={state} />
          </TabsContent>

          <TabsContent value="tests" className="pt-4 space-y-6">
            <TestCasesTable
              initialTestCases={state.test_cases || []}
              executionResults={state.execution?.results || []}
            />
            <CodeSolutionPanel
              solution={state.code?.solution || ""}
              stub={state.code?.stub || ""}
              language={state.code?.language || "python"}
            />
          </TabsContent>

          <TabsContent value="upload" className="pt-4">
            <UploadPreviewPanel state={state} />
          </TabsContent>

          <TabsContent value="versions" className="pt-4">
            <VersionDiff questionId={questionId} currentVersion={version} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
