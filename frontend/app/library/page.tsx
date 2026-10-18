"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { TopBar } from "@/components/layout/TopBar";
import { QuestionTable } from "@/components/library/QuestionTable";
import { BulkActionBar } from "@/components/library/BulkActionBar";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { QuestionSummary } from "@/lib/types";
import { BookOpen, Search, Sparkles, Filter, RotateCcw } from "lucide-react";

export default function LibraryPage() {
  const [topicFilter, setTopicFilter] = useState<string>("");
  const [difficultyFilter, setDifficultyFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data: questions, isLoading, mutate } = useSWR<QuestionSummary[]>(
    "/questions",
    () => api.listQuestions({ limit: 100 })
  );

  const filtered = (questions || []).filter((q) => {
    if (topicFilter && q.topic.toLowerCase() !== topicFilter.toLowerCase()) return false;
    if (difficultyFilter && q.difficulty.toUpperCase() !== difficultyFilter.toUpperCase()) return false;
    if (statusFilter && q.status !== statusFilter) return false;
    if (searchQuery) {
      const qText = `${q.topic} ${q.difficulty} ${q.language} ${q.question_id}`.toLowerCase();
      if (!qText.includes(searchQuery.toLowerCase())) return false;
    }
    return true;
  });

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (selectedIds.length === filtered.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filtered.map((q) => q.question_id));
    }
  };

  const resetFilters = () => {
    setTopicFilter("");
    setDifficultyFilter("");
    setStatusFilter("");
    setSearchQuery("");
  };

  return (
    <div className="flex-1 flex flex-col">
      <TopBar title="Question Library" />

      <main className="p-6 md:p-8 space-y-6 max-w-7xl w-full mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-blue-600" />
              Question Assessment Library
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Filter, inspect, and bulk-approve generated coding problems
            </p>
          </div>

          <Link href="/generate">
            <Button className="gap-2 text-xs">
              <Sparkles className="w-4 h-4" />
              New Generation
            </Button>
          </Link>
        </div>

        {/* Filter Toolbar */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by topic, difficulty, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white"
            />
          </div>

          <select
            value={topicFilter}
            onChange={(e) => setTopicFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg px-3 py-2 bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600"
          >
            <option value="">All Topics</option>
            <option value="Arrays">Arrays</option>
            <option value="Strings">Strings</option>
            <option value="Trees">Trees</option>
            <option value="Graphs">Graphs</option>
            <option value="Dynamic Programming">Dynamic Programming</option>
            <option value="Hash Maps">Hash Maps</option>
            <option value="Sorting">Sorting</option>
          </select>

          <select
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg px-3 py-2 bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600"
          >
            <option value="">All Difficulties</option>
            <option value="EASY">Easy</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
            <option value="EXPERT">Expert</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg px-3 py-2 bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600"
          >
            <option value="">All Statuses</option>
            <option value="APPROVED">Approved</option>
            <option value="AWAITING_REVIEW">Awaiting Review</option>
            <option value="NEEDS_HUMAN_REVIEW">Needs Review</option>
            <option value="QA_FAILED">QA Failed</option>
            <option value="PROCESSING">Processing</option>
          </select>

          {(topicFilter || difficultyFilter || statusFilter || searchQuery) && (
            <Button
              size="sm"
              variant="ghost"
              onClick={resetFilters}
              className="text-xs text-slate-500 hover:text-slate-800 gap-1 h-8"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Reset
            </Button>
          )}
        </div>

        {/* Bulk Action Bar (fixed/floating when items selected) */}
        <BulkActionBar
          selectedIds={selectedIds}
          onSuccess={() => mutate()}
          onClear={() => setSelectedIds([])}
        />

        {/* Table View */}
        {isLoading ? (
          <div className="p-16 text-center text-sm text-slate-500 bg-white border border-slate-200 rounded-xl">
            <div className="inline-block w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2" />
            <p>Loading questions library...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-16 text-center text-sm text-slate-500 bg-white border border-slate-200 rounded-xl">
            <BookOpen className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="font-medium text-slate-700">No questions match criteria</p>
            <p className="text-xs text-slate-400 mt-1 mb-4">
              Try adjusting your search filters or generate a new assessment.
            </p>
            <Link href="/generate">
              <Button size="sm">Generate Question</Button>
            </Link>
          </div>
        ) : (
          <QuestionTable
            questions={filtered}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onSelectAll={selectAll}
          />
        )}
      </main>
    </div>
  );
}
