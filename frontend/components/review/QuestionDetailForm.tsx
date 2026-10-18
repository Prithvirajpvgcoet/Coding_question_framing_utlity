"use client";

import { useState } from "react";
import { QuestionState } from "@/lib/types";
import { QAPanel } from "./QAPanel";
import { DeterministicChecks } from "./DeterministicChecks";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Eye, Code } from "lucide-react";

interface QuestionDetailFormProps {
  state: QuestionState;
  onUpdateTitle?: (title: string) => void;
}

export function QuestionDetailForm({ state, onUpdateTitle }: QuestionDetailFormProps) {
  const [title, setTitle] = useState(state.question?.title || "");
  const [purpose, setPurpose] = useState(state.question?.purpose || "");
  const [htmlView, setHtmlView] = useState<string>("preview");

  const formattedHtml = state.html?.formatted_question || "";
  const topics = state.question?.topics || [state.requirements?.topic || "General"];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Column: Question Details & Formatted HTML (8 cols) */}
      <div className="lg:col-span-8 space-y-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold">Question Overview</CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs font-mono capitalize">
                  {state.requirements?.difficulty?.toLowerCase() || "medium"}
                </Badge>
                <Badge variant="outline" className="text-xs font-mono capitalize">
                  {state.requirements?.target_language || "python"}
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Title */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Question Title *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  if (onUpdateTitle) onUpdateTitle(e.target.value);
                }}
                className="w-full text-sm font-semibold border border-slate-300 rounded-lg px-3.5 py-2 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>

            {/* Purpose */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Assessment Purpose
              </label>
              <textarea
                rows={2}
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="Identifies knowledge of algorithmic complexity and data structures..."
                className="w-full text-xs border border-slate-300 rounded-lg p-3 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600 resize-none"
              />
            </div>

            {/* Topics Tags */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Topic Tags
              </label>
              <div className="flex flex-wrap gap-1.5">
                {topics.map((t, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 text-xs font-medium"
                  >
                    #{t}
                  </span>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* HTML Content Specification */}
        <Card>
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-base font-semibold">Problem Specification (HTML)</CardTitle>
            <Tabs value={htmlView} onValueChange={setHtmlView} className="w-auto">
              <TabsList className="bg-slate-100 h-8">
                <TabsTrigger value="preview" className="gap-1 text-xs py-1">
                  <Eye className="w-3.5 h-3.5" /> Rendered
                </TabsTrigger>
                <TabsTrigger value="source" className="gap-1 text-xs py-1">
                  <Code className="w-3.5 h-3.5" /> HTML Code
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </CardHeader>
          <CardContent className="p-0">
            {htmlView === "preview" ? (
              <div className="p-4 border-t border-slate-100">
                <iframe
                  title="Formatted Question HTML Preview"
                  srcDoc={`<!DOCTYPE html><html><head><style>body{font-family:system-ui,-apple-system,sans-serif;line-height:1.6;color:#1e293b;padding:12px;}h2{color:#0f172a;}code{background:#f1f5f9;padding:2px 5px;border-radius:4px;font-family:monospace;}pre{background:#f8fafc;padding:10px;border-radius:6px;border:1px solid #e2e8f0;font-size:12px;}</style></head><body>${formattedHtml}</body></html>`}
                  sandbox="allow-scripts"
                  className="w-full h-[450px] border border-slate-200 rounded-lg bg-white"
                />
              </div>
            ) : (
              <div className="p-4 border-t border-slate-100">
                <textarea
                  readOnly
                  rows={18}
                  value={formattedHtml}
                  className="w-full font-mono text-xs p-3 bg-slate-900 text-slate-100 rounded-lg border border-slate-800 leading-relaxed resize-none focus:outline-none"
                />
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Right Column: QA Assessment & Gate Checks (4 cols) */}
      <div className="lg:col-span-4 space-y-6">
        <QAPanel quality={state.quality} finalQa={state.final_qa} />
        <DeterministicChecks
          finalQa={state.final_qa}
          testCasesCount={state.test_cases?.length || 0}
        />
      </div>
    </div>
  );
}
