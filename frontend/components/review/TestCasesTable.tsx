"use client";

import { useState } from "react";
import { TestCase, TestExecutionResult } from "@/lib/types";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus, Trash2, Edit2, CheckCircle2, XCircle } from "lucide-react";

interface TestCasesTableProps {
  initialTestCases: TestCase[];
  executionResults?: TestExecutionResult[];
  onUpdateTestCases?: (tests: TestCase[]) => void;
}

export function TestCasesTable({
  initialTestCases = [],
  executionResults = [],
  onUpdateTestCases,
}: TestCasesTableProps) {
  const [testCases, setTestCases] = useState<TestCase[]>(initialTestCases);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  const handleDelete = (index: number) => {
    const updated = testCases.filter((_, i) => i !== index);
    setTestCases(updated);
    if (onUpdateTestCases) onUpdateTestCases(updated);
  };

  const handleAddRow = () => {
    const newTest: TestCase = {
      type: "HIDDEN",
      input_args: "",
      expected_output: "",
      points: 1,
    };
    const updated = [...testCases, newTest];
    setTestCases(updated);
    setEditingIndex(updated.length - 1);
    if (onUpdateTestCases) onUpdateTestCases(updated);
  };

  const formatVal = (val: any) => {
    if (typeof val === "object") return JSON.stringify(val);
    return String(val || "");
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-slate-800">
            Harness Test Suite ({testCases.length})
          </h4>
          <p className="text-xs text-slate-500">
            Sample visible test cases for candidates and hidden verification cases
          </p>
        </div>

        <Button
          size="sm"
          variant="outline"
          onClick={handleAddRow}
          className="gap-1.5 text-xs h-8"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Test Case
        </Button>
      </div>

      <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">#</TableHead>
              <TableHead className="w-24">Type</TableHead>
              <TableHead>Input Arguments</TableHead>
              <TableHead>Expected Output</TableHead>
              <TableHead className="w-20">Points</TableHead>
              <TableHead className="w-28">Sandbox</TableHead>
              <TableHead className="w-16 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {testCases.map((tc, idx) => {
              const execRes = executionResults.find((r) => r.test_index === idx);
              const hasPassed = execRes?.passed ?? true;

              return (
                <TableRow key={idx}>
                  <TableCell className="font-mono text-xs text-slate-500">{idx + 1}</TableCell>
                  <TableCell>
                    <Badge
                      variant={tc.type === "VISIBLE" ? "info" : "secondary"}
                      className="text-[10px] uppercase font-bold"
                    >
                      {tc.type}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs max-w-xs truncate text-slate-800">
                    {formatVal(tc.input_args)}
                  </TableCell>
                  <TableCell className="font-mono text-xs max-w-xs truncate text-slate-800">
                    {formatVal(tc.expected_output)}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-slate-700">
                    {tc.points ?? 1}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1.5 text-xs font-semibold">
                      {hasPassed ? (
                        <span className="flex items-center gap-1 text-emerald-600">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Passed
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-red-600">
                          <XCircle className="w-3.5 h-3.5" /> Failed
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => handleDelete(idx)}
                      className="h-7 w-7 text-slate-400 hover:text-red-600"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
