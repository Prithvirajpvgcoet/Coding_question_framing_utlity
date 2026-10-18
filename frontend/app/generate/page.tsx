"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { TopBar } from "@/components/layout/TopBar";
import { GenerateForm } from "@/components/generate/GenerateForm";
import { BatchGenerateForm } from "@/components/generate/BatchGenerateForm";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Sparkles, Layers } from "lucide-react";

function GeneratePageContent() {
  const searchParams = useSearchParams();
  const initialTab = searchParams.get("tab") === "batch" ? "batch" : "single";
  const [activeTab, setActiveTab] = useState<string>(initialTab);

  return (
    <div className="flex-1 flex flex-col">
      <TopBar title="Generate Coding Assessments" />

      <main className="p-6 md:p-8 space-y-6 max-w-5xl w-full mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900">
              Question Generation Studio
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Powered by Groq LLMs, LangGraph 7-agent consensus, and local sandbox verification
            </p>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-auto">
            <TabsList className="bg-slate-200">
              <TabsTrigger value="single" className="gap-1.5 text-xs">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                Single
              </TabsTrigger>
              <TabsTrigger value="batch" className="gap-1.5 text-xs">
                <Layers className="w-3.5 h-3.5 text-purple-600" />
                Batch Fan-Out
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsContent value="single">
            <GenerateForm />
          </TabsContent>

          <TabsContent value="batch">
            <BatchGenerateForm />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default function GeneratePage() {
  return (
    <Suspense fallback={<div className="p-10 text-center text-xs text-slate-400">Loading generator...</div>}>
      <GeneratePageContent />
    </Suspense>
  );
}
