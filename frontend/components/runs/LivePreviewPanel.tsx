"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { QuestionState } from "@/lib/types";
import { FileText, Code2, CheckSquare, Terminal } from "lucide-react";

interface LivePreviewPanelProps {
  state: Partial<QuestionState> | null;
}

export function LivePreviewPanel({ state }: LivePreviewPanelProps) {
  const [activeTab, setActiveTab] = useState<string>("question");

  const html = state?.html?.formatted_question || "";
  const codeSolution = state?.code?.solution || "";
  const codeStub = state?.code?.stub || "";
  const testCases = state?.test_cases || [];

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
          Live Artifact Preview
        </h4>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-auto">
          <TabsList className="bg-slate-100 h-8">
            <TabsTrigger value="question" className="gap-1 text-xs py-1">
              <FileText className="w-3.5 h-3.5 text-blue-600" />
              Question
            </TabsTrigger>
            <TabsTrigger value="stub" className="gap-1 text-xs py-1">
              <Terminal className="w-3.5 h-3.5 text-purple-600" />
              Stub
            </TabsTrigger>
            <TabsTrigger value="tests" className="gap-1 text-xs py-1">
              <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
              Tests ({testCases.length})
            </TabsTrigger>
            <TabsTrigger value="solution" className="gap-1 text-xs py-1">
              <Code2 className="w-3.5 h-3.5 text-slate-700" />
              Solution
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="flex-1 overflow-y-auto pt-3">
        {/* Question Tab: Sandboxed iframe */}
        {activeTab === "question" && (
          <div className="h-full min-h-[400px]">
            {html ? (
              <iframe
                title="Question HTML Preview"
                srcDoc={`<!DOCTYPE html><html><head><style>body{font-family:system-ui,-apple-system,sans-serif;line-height:1.6;color:#1e293b;padding:16px;}h2{color:#0f172a;}code{background:#f1f5f9;padding:2px 5px;border-radius:4px;font-family:monospace;}</style></head><body>${html}</body></html>`}
                sandbox="allow-scripts"
                className="w-full h-full min-h-[420px] border border-slate-200 rounded-lg bg-white"
              />
            ) : (
              <div className="text-center py-20 text-slate-400 text-xs">
                Draft question HTML will appear once Agent C completes Step 2...
              </div>
            )}
          </div>
        )}

        {/* Code Stub Tab */}
        {activeTab === "stub" && (
          <div className="h-full">
            {codeStub ? (
              <pre className="p-4 bg-slate-900 text-slate-100 rounded-lg font-mono text-xs overflow-x-auto leading-relaxed">
                <code>{codeStub}</code>
              </pre>
            ) : (
              <div className="text-center py-20 text-slate-400 text-xs">
                Candidate starter stub will appear once Agent C generates the harness...
              </div>
            )}
          </div>
        )}

        {/* Test Cases Tab */}
        {activeTab === "tests" && (
          <div className="h-full">
            {testCases.length > 0 ? (
              <div className="space-y-2">
                {testCases.map((tc, idx) => (
                  <div
                    key={idx}
                    className="p-3 border border-slate-200 rounded-lg bg-slate-50 text-xs space-y-1.5"
                  >
                    <div className="flex justify-between items-center font-semibold">
                      <span className="text-slate-700">Test Case #{idx + 1}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          tc.type === "VISIBLE"
                            ? "bg-blue-100 text-blue-700"
                            : "bg-slate-200 text-slate-700"
                        }`}
                      >
                        {tc.type}
                      </span>
                    </div>
                    <div className="font-mono text-[11px] text-slate-600 bg-white p-2 rounded border border-slate-200">
                      <div><strong className="text-slate-400">Input:</strong> {typeof tc.input_args === "object" ? JSON.stringify(tc.input_args) : String(tc.input_args)}</div>
                      <div><strong className="text-slate-400">Expected:</strong> {typeof tc.expected_output === "object" ? JSON.stringify(tc.expected_output) : String(tc.expected_output)}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-20 text-slate-400 text-xs">
                Test cases will appear once Agent C executes the test generation prompt...
              </div>
            )}
          </div>
        )}

        {/* Solution Tab */}
        {activeTab === "solution" && (
          <div className="h-full">
            {codeSolution ? (
              <pre className="p-4 bg-slate-900 text-emerald-400 rounded-lg font-mono text-xs overflow-x-auto leading-relaxed">
                <code>{codeSolution}</code>
              </pre>
            ) : (
              <div className="text-center py-20 text-slate-400 text-xs">
                Reference solution code will appear once Agent C completes sandbox verification...
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
