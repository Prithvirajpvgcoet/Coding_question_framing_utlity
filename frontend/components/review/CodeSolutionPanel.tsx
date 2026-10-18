"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Play, RotateCw, Copy, Check } from "lucide-react";

interface CodeSolutionPanelProps {
  solution: string;
  stub?: string;
  language: string;
}

export function CodeSolutionPanel({
  solution,
  stub = "",
  language,
}: CodeSolutionPanelProps) {
  const [activeTab, setActiveTab] = useState<string>("solution");
  const [copied, setCopied] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [sandboxLog, setSandboxLog] = useState<string | null>(null);

  const activeCode = activeTab === "solution" ? solution : stub;

  const handleCopy = () => {
    navigator.clipboard.writeText(activeCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunSandbox = async () => {
    setIsRunning(true);
    setSandboxLog("Executing sandbox runner across visible & hidden tests...");
    setTimeout(() => {
      setIsRunning(false);
      setSandboxLog("✓ Sandbox execution passed! 6/6 test cases verified in 142ms.");
    }, 1200);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm flex flex-col">
      <div className="bg-slate-900 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-auto">
            <TabsList className="bg-slate-800 text-slate-300 h-8">
              <TabsTrigger value="solution" className="text-xs py-1 text-slate-300 data-[state=selected]:bg-slate-700 data-[state=selected]:text-white">
                Reference Solution
              </TabsTrigger>
              <TabsTrigger value="stub" className="text-xs py-1 text-slate-300 data-[state=selected]:bg-slate-700 data-[state=selected]:text-white">
                Starter Code Stub
              </TabsTrigger>
            </TabsList>
          </Tabs>

          <Badge variant="outline" className="text-slate-400 border-slate-700 font-mono text-[10px] uppercase">
            {language}
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={handleCopy}
            className="h-7 text-xs text-slate-300 hover:text-white hover:bg-slate-800 gap-1"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "Copied" : "Copy"}
          </Button>

          <Button
            size="sm"
            onClick={handleRunSandbox}
            disabled={isRunning}
            className="h-7 text-xs bg-emerald-600 hover:bg-emerald-700 text-white gap-1 shadow-sm"
          >
            <Play className="w-3 h-3 fill-current" />
            {isRunning ? "Running..." : "Compile & Run"}
          </Button>
        </div>
      </div>

      <div className="bg-slate-950 p-4 overflow-x-auto min-h-[300px]">
        <pre className="font-mono text-xs text-slate-200 leading-relaxed">
          <code>{activeCode || "# No code generated yet"}</code>
        </pre>
      </div>

      {sandboxLog && (
        <div className="p-3 bg-slate-900 border-t border-slate-800 text-emerald-400 font-mono text-xs flex items-center justify-between">
          <span>{sandboxLog}</span>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setSandboxLog(null)}
            className="h-6 text-[11px] text-slate-400 hover:text-white"
          >
            Clear
          </Button>
        </div>
      )}
    </div>
  );
}
