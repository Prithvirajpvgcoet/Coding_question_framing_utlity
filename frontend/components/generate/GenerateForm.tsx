"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { TestCasePolicy } from "./TestCasePolicy";
import { api } from "@/lib/api";
import { QuestionBankItem } from "@/lib/types";
import { Sparkles, Loader2 } from "lucide-react";

const TOPICS = [
  "Arrays",
  "Strings",
  "Hash Maps",
  "Linked Lists",
  "Stacks & Queues",
  "Trees",
  "Binary Search",
  "Dynamic Programming",
  "Graphs",
  "Heaps",
  "Two Pointers",
  "Sliding Window",
  "Greedy",
  "Backtracking",
  "Bit Manipulation",
  "Math",
  "Sorting",
  "Recursion",
  "System Design",
  "SQL",
];

const LANGUAGES = [
  { value: "python", label: "Python 3" },
  { value: "javascript", label: "JavaScript (Node.js)" },
  { value: "java", label: "Java 17" },
  { value: "cpp", label: "C++ (GCC)" },
  { value: "csharp", label: "C# (.NET)" },
  { value: "typescript", label: "TypeScript" },
  { value: "go", label: "Go" },
];

const DIFFICULTIES = ["EASY", "MEDIUM", "HARD", "EXPERT"];

export function GenerateForm() {
  const router = useRouter();
  const { data: banks } = useSWR<QuestionBankItem[]>("/banks", () => api.listBanks());

  const [bankId, setBankId] = useState<string>("");
  const [domainContext, setDomainContext] = useState<string>("auto");
  const [topic, setTopic] = useState<string>("Arrays");
  const [subtopic, setSubtopic] = useState<string>("");
  const [difficulty, setDifficulty] = useState<string>("MEDIUM");
  const [questionType, setQuestionType] = useState<string>("ALGORITHMIC");
  const [language, setLanguage] = useState<string>("python");
  const [solveTime, setSolveTime] = useState<number>(30);
  const [instructions, setInstructions] = useState<string>("");

  const [visibleCount, setVisibleCount] = useState<number>(2);
  const [hiddenCount, setHiddenCount] = useState<number>(3);
  const [pointsPerTest, setPointsPerTest] = useState<number>(1);

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const constraints = instructions.trim()
        ? instructions.split("\n").filter((line) => line.trim().length > 0)
        : [];

      if (domainContext === "fintech") {
        constraints.unshift("Domain context: FinTech & Banking (e.g. fraud detection, payment idempotency, ledger reconciliation)");
      } else if (domainContext === "ecommerce") {
        constraints.unshift("Domain context: E-Commerce & Logistics (e.g. flash sales, AMR warehouse routing, bin packing)");
      } else if (domainContext === "embedded") {
        constraints.unshift("Domain context: Embedded Systems & Automotive (e.g. CAN-bus telemetry, ring buffer, sensor noise filtering)");
      } else if (domainContext === "distributed") {
        constraints.unshift("Domain context: Core Algorithms & Distributed Systems (e.g. distributed LRU cache, topological build order, search tries)");
      }

      const res = await api.generate({
        topic,
        subtopic,
        difficulty,
        question_type: questionType,
        target_language: language,
        max_solve_time_minutes: solveTime,
        bank_id: bankId || undefined,
        custom_constraints: constraints,
      });

      // Redirect immediately to live run SSE monitoring page
      router.push(`/runs/${res.question_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to initiate generation");
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="max-w-3xl mx-auto shadow-sm">
      <form onSubmit={handleSubmit}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <span>Generate New Coding Assessment</span>
          </CardTitle>
          <CardDescription>
            Specify requirements for the 7-Agent workflow to draft, sandbox-test, and score
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">
              {error}
            </div>
          )}

          {/* Question Bank */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Target Question Bank (Optional)
            </label>
            <select
              value={bankId}
              onChange={(e) => setBankId(e.target.value)}
              className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              <option value="">-- No Bank (Uncategorized) --</option>
              {banks?.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.question_count} questions)
                </option>
              ))}
            </select>
          </div>

          {/* Domain Context & Knowledge Base */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Enterprise Domain Context (Agent B Retrieval)
            </label>
            <select
              value={domainContext}
              onChange={(e) => setDomainContext(e.target.value)}
              className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              <option value="auto">🌐 Auto-Match (Hybrid Retrieval across all datasets)</option>
              <option value="fintech">💳 FinTech & Banking (Payments, Fraud, Ledgers, FX)</option>
              <option value="ecommerce">📦 E-Commerce & Logistics (Warehouse AMR, Inventory Locks, Bin Packing)</option>
              <option value="embedded">🚗 Embedded Systems & Automotive (CAN-Bus, Telemetry Ring Buffer, Sensor DSP)</option>
              <option value="distributed">⚡ Core Algorithms & Distributed Systems (Distributed LRU, Graph Dependency, Tries)</option>
            </select>
            <p className="text-[11px] text-slate-400 mt-1">
              Agent B queries the backend knowledge dataset to extract industry scenarios before passing context to Agent C.
            </p>
          </div>

          {/* Topic & Subtopic */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Topic *
              </label>
              <select
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
                required
              >
                {TOPICS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Subtopic / Pattern (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Sliding Window, Kadane's, Dijkstra"
                value={subtopic}
                onChange={(e) => setSubtopic(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>
          </div>

          {/* Difficulty Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-2">
              Difficulty *
            </label>
            <div className="grid grid-cols-4 gap-2">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDifficulty(d)}
                  className={`py-2 text-xs font-semibold rounded-lg border transition-all ${
                    difficulty === d
                      ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* Language & Question Type */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Target Language *
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
              >
                {LANGUAGES.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Question Type *
              </label>
              <select
                value={questionType}
                onChange={(e) => setQuestionType(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
              >
                <option value="ALGORITHMIC">Algorithmic Problem</option>
                <option value="DEBUG">Bug Fix / Code Repair</option>
                <option value="FILL_IN_BLANK">Fill in the Blank / Code Completion</option>
                <option value="SQL">Database / SQL Query</option>
              </select>
            </div>
          </div>

          {/* Test Case Policy */}
          <TestCasePolicy
            hiddenCount={hiddenCount}
            visibleCount={visibleCount}
            pointsPerTest={pointsPerTest}
            onHiddenChange={setHiddenCount}
            onVisibleChange={setVisibleCount}
            onPointsChange={setPointsPerTest}
          />

          {/* Custom Constraints / Prompt Details */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Custom Constraints & Instructions
            </label>
            <textarea
              rows={3}
              placeholder="e.g. Must use O(N) time complexity and no extra hash set, or tailor for financial services scenario..."
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              className="w-full text-sm border border-slate-300 rounded-md p-3 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 resize-none"
            />
          </div>
        </CardContent>

        <CardFooter className="flex justify-between items-center border-t border-slate-100 pt-4">
          <span className="text-xs text-slate-400">
            Estimated generation time: ~30-45s
          </span>
          <Button type="submit" disabled={isSubmitting} className="gap-2 px-6">
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Dispatching Agents...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate Question →
              </>
            )}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
