"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { TopBar } from "@/components/layout/TopBar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { CloudUpload, ArrowUpRight, RotateCw, CheckCircle2, Clock, AlertCircle } from "lucide-react";

export default function UploadsPage() {
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const { data: uploadJobs, isLoading, mutate } = useSWR(
    "/uploads",
    () => api.listUploads(),
    { refreshInterval: 3000 }
  );

  const filtered = (uploadJobs || []).filter((job) => {
    if (statusFilter === "ALL") return true;
    return job.status === statusFilter;
  });

  const handleRetry = async (jobId: string) => {
    try {
      await api.retryUpload(jobId);
      mutate();
    } catch (err) {
      console.error("Retry failed:", err);
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <TopBar title="Upload Center" />

      <main className="p-6 md:p-8 space-y-6 max-w-7xl w-full mx-auto">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              <CloudUpload className="w-5 h-5 text-blue-600" />
              iMocha Platform Upload Center
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Live automation pipeline pushing approved assessments into iMocha question banks
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link href="/library">
              <Button size="sm" variant="outline" className="gap-1.5 text-xs">
                Select Questions to Upload
              </Button>
            </Link>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center justify-between">
          <Tabs value={statusFilter} onValueChange={setStatusFilter} className="w-auto">
            <TabsList className="bg-slate-200 h-8">
              <TabsTrigger value="ALL" className="text-xs py-1">
                All Jobs ({uploadJobs?.length || 0})
              </TabsTrigger>
              <TabsTrigger value="IN_PROGRESS" className="text-xs py-1">
                In Progress
              </TabsTrigger>
              <TabsTrigger value="QUEUED" className="text-xs py-1">
                Queued
              </TabsTrigger>
              <TabsTrigger value="COMPLETED" className="text-xs py-1">
                Completed
              </TabsTrigger>
              <TabsTrigger value="FAILED" className="text-xs py-1">
                Failed
              </TabsTrigger>
            </TabsList>
          </Tabs>

          <span className="text-xs font-mono text-slate-500 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Worker Concurrency: 2
          </span>
        </div>

        {/* Upload Jobs Table */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Upload Automation Queue</CardTitle>
            <CardDescription>
              Each job automates portal login, form filling, harness binding, and validation
            </CardDescription>
          </CardHeader>

          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-16 text-center text-sm text-slate-500">
                <div className="inline-block w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2" />
                <p>Loading upload jobs...</p>
              </div>
            ) : filtered.length === 0 ? (
              <div className="p-16 text-center text-sm text-slate-500">
                <CloudUpload className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <p className="font-semibold text-slate-700">No upload jobs found</p>
                <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                  Questions can be queued for upload from the Review Workbench or Question Library.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Job ID</TableHead>
                      <TableHead>Question ID</TableHead>
                      <TableHead>Bank</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Progression</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filtered.map((job) => {
                      const isComplete = job.status === "COMPLETED";
                      const isInProgress = job.status === "IN_PROGRESS";
                      const isFailed = job.status === "FAILED";

                      return (
                        <TableRow key={job.id}>
                          <TableCell className="font-mono text-xs font-semibold text-slate-800">
                            UP-{job.id.slice(0, 8)}
                          </TableCell>
                          <TableCell className="font-mono text-xs text-blue-600 hover:underline">
                            <Link href={`/review/${job.question_id}`}>
                              Q-{job.question_id.slice(0, 8)}
                            </Link>
                          </TableCell>
                          <TableCell className="text-xs text-slate-700">
                            {job.bank_id || "Embedded-Capgemini"}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                isComplete
                                  ? "success"
                                  : isInProgress
                                  ? "info"
                                  : isFailed
                                  ? "destructive"
                                  : "warning"
                              }
                              className="text-[11px]"
                            >
                              {job.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs font-mono text-slate-600">
                            {job.step_count > 0 ? `${job.step_count}/6 steps` : "In Queue"}
                          </TableCell>
                          <TableCell className="text-xs text-slate-400">
                            {job.created_at ? new Date(job.created_at).toLocaleTimeString() : "Recently"}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-2">
                              {isFailed && (
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleRetry(job.id)}
                                  className="h-7 text-xs text-amber-600 hover:text-amber-700"
                                >
                                  <RotateCw className="w-3 h-3 mr-1" />
                                  Retry
                                </Button>
                              )}
                              <Link href={`/uploads/${job.id}`}>
                                <Button size="sm" variant="outline" className="gap-1 text-xs h-7">
                                  View Job <ArrowUpRight className="w-3 h-3" />
                                </Button>
                              </Link>
                            </div>
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
