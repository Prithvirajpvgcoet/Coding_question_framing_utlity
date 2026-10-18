"use client";

import Link from "next/link";
import useSWR from "swr";
import { TopBar } from "@/components/layout/TopBar";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { PlayCircle, ArrowUpRight, Sparkles } from "lucide-react";

export default function RunsListPage() {
  const { data: runs, isLoading } = useSWR("/runs", () => api.listRuns(), {
    refreshInterval: 4000,
  });

  return (
    <div className="flex-1 flex flex-col">
      <TopBar title="Agent Generation Runs" />

      <main className="p-6 md:p-8 space-y-6 max-w-7xl w-full mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              <PlayCircle className="w-5 h-5 text-blue-600" />
              Active & Historical Pipeline Runs
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Monitor multi-agent execution traces, sandbox verification, and quality scores
            </p>
          </div>

          <Link href="/generate">
            <Button className="gap-2 text-xs">
              <Sparkles className="w-4 h-4" />
              New Generation
            </Button>
          </Link>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">All Executions</CardTitle>
            <CardDescription>
              Real-time feed of questions processed through the LangGraph agent graph
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-10 text-center text-sm text-slate-500">
                <div className="inline-block w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2" />
                <p>Loading runs history...</p>
              </div>
            ) : !runs || runs.length === 0 ? (
              <div className="p-12 text-center text-sm text-slate-500">
                <PlayCircle className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <p className="font-medium text-slate-700">No runs found</p>
                <p className="text-xs text-slate-400 mt-1 mb-4">Start your first question generation to see agent activity.</p>
                <Link href="/generate">
                  <Button size="sm">Generate Question</Button>
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Run ID</TableHead>
                      <TableHead>Title / Topic</TableHead>
                      <TableHead>Difficulty</TableHead>
                      <TableHead>Language</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Current Agent</TableHead>
                      <TableHead>Retries</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {runs.map((r: any) => {
                      const isComplete = r.status === "AWAITING_REVIEW" || r.status === "APPROVED";
                      const isProcessing = r.status === "PROCESSING";

                      return (
                        <TableRow key={r.run_id}>
                          <TableCell className="font-mono text-xs font-semibold text-slate-800">
                            RUN-{r.run_id.slice(0, 8)}
                          </TableCell>
                          <TableCell>
                            <div className="font-medium text-slate-900">{r.title || r.topic}</div>
                            <div className="text-[11px] text-slate-400">{r.topic}</div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="text-[11px] capitalize">
                              {r.difficulty?.toLowerCase() || "medium"}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs text-slate-600 capitalize">
                            {r.language || "python"}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                isComplete
                                  ? "success"
                                  : isProcessing
                                  ? "info"
                                  : r.status === "CANCELLED"
                                  ? "outline"
                                  : "destructive"
                              }
                              className="text-[11px]"
                            >
                              {r.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-mono text-xs text-slate-600">
                            {r.current_agent || (isComplete ? "Completed" : "Pipeline")}
                          </TableCell>
                          <TableCell className="text-xs text-slate-500 font-mono">
                            {r.internal_retries || 0}
                          </TableCell>
                          <TableCell className="text-right">
                            <Link href={`/runs/${r.run_id}`}>
                              <Button size="sm" variant="outline" className="gap-1 text-xs h-7">
                                View Run <ArrowUpRight className="w-3 h-3" />
                              </Button>
                            </Link>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
