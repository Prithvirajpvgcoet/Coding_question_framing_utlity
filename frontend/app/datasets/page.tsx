"use client";

import { useState } from "react";
import useSWR from "swr";
import { TopBar } from "@/components/layout/TopBar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { ReferenceDocumentItem } from "@/lib/types";
import {
  Database,
  UploadCloud,
  Sparkles,
  Trash2,
  Eye,
  FileText,
  CheckCircle2,
  Search,
} from "lucide-react";

export default function DatasetsPage() {
  const [domainFilter, setDomainFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedDoc, setSelectedDoc] = useState<ReferenceDocumentItem | null>(null);

  const [isSeeding, setIsSeeding] = useState<boolean>(false);
  const [seedMessage, setSeedMessage] = useState<string | null>(null);

  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDocType, setUploadDocType] = useState<string>("DOMAIN_SCENARIO");
  const [uploadTags, setUploadTags] = useState<string>("");
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const { data: datasets, isLoading, mutate } = useSWR<ReferenceDocumentItem[]>(
    "/datasets",
    () => api.listDatasets(),
    { revalidateOnFocus: false }
  );

  const handleSeed = async () => {
    setIsSeeding(true);
    setSeedMessage(null);
    try {
      const res = await api.seedDatasets();
      setSeedMessage(`Successfully ingested ${res.count} reference scenarios across 4 enterprise domains.`);
      mutate();
    } catch (err: any) {
      setSeedMessage(`Failed to seed: ${err.message}`);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setIsUploading(true);
    setUploadError(null);
    try {
      await api.uploadDatasetFile(uploadFile, uploadDocType, uploadTags);
      setUploadFile(null);
      setUploadTags("");
      mutate();
    } catch (err: any) {
      setUploadError(err.message || "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to remove this reference document?")) return;
    try {
      await api.deleteDataset(id);
      if (selectedDoc?.id === id) setSelectedDoc(null);
      mutate();
    } catch (err: any) {
      alert(`Delete error: ${err.message}`);
    }
  };

  const filtered = (datasets || []).filter((doc) => {
    if (domainFilter !== "ALL" && !doc.domain.toLowerCase().includes(domainFilter.toLowerCase())) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = doc.title.toLowerCase().includes(q);
      const matchTopic = doc.topic.toLowerCase().includes(q);
      const matchSub = (doc.subtopic || "").toLowerCase().includes(q);
      const matchTags = (doc.tags || []).some((t) => t.toLowerCase().includes(q));
      if (!matchTitle && !matchTopic && !matchSub && !matchTags) return false;
    }
    return true;
  });

  return (
    <div className="flex-1 flex flex-col">
      <TopBar title="Reference Datasets & Domain Knowledge" />

      <main className="p-6 md:p-8 space-y-6 max-w-7xl w-full mx-auto">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-600" />
              Agent B Knowledge Store & Reference Datasets
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Enterprise problem scenarios and rubrics retrieved by Agent B to ground question generation in real-world engineering
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={handleSeed}
              disabled={isSeeding}
              className="gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {isSeeding ? "Seeding Scenarios..." : "Seed Pre-Loaded Datasets"}
            </Button>
          </div>
        </div>

        {seedMessage && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{seedMessage}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Cols: Ingested Datasets Table */}
          <div className="lg:col-span-2 space-y-4">
            <Card className="shadow-sm">
              <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-800">
                    <FileText className="w-4 h-4 text-blue-600" />
                    Ingested Reference Scenarios ({filtered.length})
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Indexed by topic, difficulty, and algorithmic tags for hybrid vector/lexical retrieval
                  </CardDescription>
                </div>

                {/* Domain Filter */}
                <select
                  value={domainFilter}
                  onChange={(e) => setDomainFilter(e.target.value)}
                  className="text-xs border border-slate-200 rounded px-2.5 py-1.5 bg-white text-slate-700"
                >
                  <option value="ALL">All Domains</option>
                  <option value="fintech">FinTech</option>
                  <option value="commerce">E-Commerce</option>
                  <option value="embedded">Embedded / Auto</option>
                  <option value="distributed">Distributed Systems</option>
                </select>
              </CardHeader>

              {/* Search Bar */}
              <div className="p-3 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2">
                <Search className="w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter by title, topic, or tag (e.g. hash-table, kafka, sensor)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full text-xs bg-transparent focus:outline-none text-slate-700"
                />
              </div>

              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[35%]">Title & Domain</TableHead>
                      <TableHead>Topic / Subtopic</TableHead>
                      <TableHead>Difficulty</TableHead>
                      <TableHead>Format</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {isLoading ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-8 text-xs text-slate-400">
                          Loading indexed datasets...
                        </TableCell>
                      </TableRow>
                    ) : filtered.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-10 text-xs text-slate-500">
                          No reference datasets found. Click &quot;Seed Pre-Loaded Datasets&quot; or upload a file below.
                        </TableCell>
                      </TableRow>
                    ) : (
                      filtered.map((doc) => (
                        <TableRow
                          key={doc.id}
                          className={selectedDoc?.id === doc.id ? "bg-blue-50/50" : ""}
                        >
                          <TableCell className="font-medium text-slate-800">
                            <div className="font-semibold text-xs text-slate-900">{doc.title}</div>
                            <div className="text-[11px] text-slate-500 truncate max-w-[240px]">
                              {doc.domain || "General Domain"}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-xs font-mono text-slate-700">{doc.topic}</div>
                            {doc.subtopic && (
                              <div className="text-[11px] text-slate-400">{doc.subtopic}</div>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={`text-[10px] font-mono ${
                                doc.difficulty === "HARD"
                                  ? "border-red-200 text-red-700 bg-red-50"
                                  : doc.difficulty === "MEDIUM"
                                  ? "border-amber-200 text-amber-700 bg-amber-50"
                                  : "border-emerald-200 text-emerald-700 bg-emerald-50"
                              }`}
                            >
                              {doc.difficulty}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <span
                              className={`text-[10px] font-mono px-1.5 py-0.5 rounded uppercase font-semibold ${
                                doc.format === "pdf"
                                  ? "bg-red-50 text-red-700 border border-red-200"
                                  : doc.format === "docx"
                                  ? "bg-blue-50 text-blue-700 border border-blue-200"
                                  : doc.format === "json"
                                  ? "bg-amber-50 text-amber-700 border border-amber-200"
                                  : doc.format === "csv"
                                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                  : "bg-slate-100 text-slate-600 border border-slate-200"
                              }`}
                            >
                              {doc.format}
                            </span>
                          </TableCell>
                          <TableCell className="text-right space-x-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 w-7 p-0"
                              onClick={() => setSelectedDoc(doc)}
                              title="Inspect scenario"
                            >
                              <Eye className="w-3.5 h-3.5 text-slate-600" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 w-7 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                              onClick={() => handleDelete(doc.id)}
                              title="Delete scenario"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>

          {/* Right Col: Ingest New Dataset & Detail View */}
          <div className="space-y-4">
            {/* Upload Card */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3 border-b border-slate-100">
                <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-800">
                  <UploadCloud className="w-4 h-4 text-blue-600" />
                  Upload Custom Knowledge
                </CardTitle>
                <CardDescription className="text-xs">
                  Upload Word (.docx), PDF (.pdf), .json, .csv, or .md documents for Agent B
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                <form onSubmit={handleUpload} className="space-y-3">
                  {uploadError && (
                    <div className="p-2.5 bg-red-50 text-red-700 border border-red-200 rounded text-xs">
                      {uploadError}
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Document File (.pdf, .docx, .json, .csv, .md, .txt) *
                    </label>
                    <input
                      type="file"
                      accept=".pdf,.docx,.doc,.json,.jsonl,.csv,.tsv,.md,.txt"
                      onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                      className="block w-full text-xs text-slate-500 file:mr-2 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 border border-slate-200 rounded p-1 cursor-pointer"
                      required
                    />
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      <span className="text-[10px] px-1 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-mono">Word (.docx)</span>
                      <span className="text-[10px] px-1 py-0.5 rounded bg-red-50 text-red-700 border border-red-200 font-mono">PDF (.pdf)</span>
                      <span className="text-[10px] px-1 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-mono">JSON</span>
                      <span className="text-[10px] px-1 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">CSV</span>
                      <span className="text-[10px] px-1 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 font-mono">Markdown</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Document Type
                    </label>
                    <select
                      value={uploadDocType}
                      onChange={(e) => setUploadDocType(e.target.value)}
                      className="w-full text-xs border border-slate-200 rounded p-2 bg-white text-slate-700"
                    >
                      <option value="DOMAIN_SCENARIO">Domain Scenario (e.g. Industry use case)</option>
                      <option value="REFERENCE_QUESTION">Reference Problem (Legacy / Gold standard)</option>
                      <option value="RUBRIC">Evaluation Rubric & Grading Standard</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Extra Tags (Comma separated)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. healthcare, dicom, hl7"
                      value={uploadTags}
                      onChange={(e) => setUploadTags(e.target.value)}
                      className="w-full text-xs border border-slate-200 rounded p-2 text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
                    />
                  </div>

                  <Button
                    type="submit"
                    disabled={isUploading || !uploadFile}
                    className="w-full text-xs bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    {isUploading ? "Ingesting..." : "Ingest & Index Dataset"}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Selected Scenario Preview */}
            {selectedDoc && (
              <Card className="shadow-sm border-blue-200 bg-blue-50/20">
                <CardHeader className="pb-2 border-b border-blue-100">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-bold text-slate-900">
                      Scenario Detail
                    </CardTitle>
                    <button
                      onClick={() => setSelectedDoc(null)}
                      className="text-xs text-slate-400 hover:text-slate-600"
                    >
                      ✕
                    </button>
                  </div>
                  <CardDescription className="text-[11px] text-blue-700 font-semibold">
                    {selectedDoc.title}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-3 space-y-2 text-xs">
                  <div>
                    <span className="font-semibold text-slate-700">Domain:</span>{" "}
                    <span className="text-slate-600">{selectedDoc.domain}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-700">Topic:</span>{" "}
                    <span className="font-mono text-slate-600">
                      {selectedDoc.topic} {selectedDoc.subtopic ? `· ${selectedDoc.subtopic}` : ""}
                    </span>
                  </div>
                  {selectedDoc.tags?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedDoc.tags.map((t) => (
                        <span
                          key={t}
                          className="px-1.5 py-0.5 rounded text-[10px] bg-white border border-slate-200 text-slate-600"
                        >
                          #{t}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="pt-2 border-t border-slate-100">
                    <span className="font-semibold text-slate-700 block mb-1">Raw Context / Scenario:</span>
                    <pre className="p-2.5 bg-white border border-slate-200 rounded text-[11px] text-slate-700 font-mono whitespace-pre-wrap max-h-56 overflow-y-auto">
                      {selectedDoc.raw_content || JSON.stringify(selectedDoc.structured_data, null, 2)}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
