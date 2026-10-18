"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { api } from "@/lib/api";
import { Layers, Plus, Trash2, Loader2 } from "lucide-react";

interface BatchItem {
  id: string;
  topic: string;
  difficulty: string;
  target_language: string;
}

export function BatchGenerateForm() {
  const router = useRouter();
  const [items, setItems] = useState<BatchItem[]>([
    { id: "1", topic: "Arrays", difficulty: "MEDIUM", target_language: "python" },
    { id: "2", topic: "Trees", difficulty: "HARD", target_language: "python" },
  ]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addItem = () => {
    if (items.length >= 20) return;
    setItems([
      ...items,
      {
        id: String(Date.now()),
        topic: "Strings",
        difficulty: "MEDIUM",
        target_language: "python",
      },
    ]);
  };

  const removeItem = (id: string) => {
    if (items.length <= 1) return;
    setItems(items.filter((item) => item.id !== id));
  };

  const updateItem = (id: string, field: keyof BatchItem, val: string) => {
    setItems(
      items.map((item) => (item.id === id ? { ...item, [field]: val } : item))
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const payload = items.map((it) => ({
        topic: it.topic,
        difficulty: it.difficulty,
        target_language: it.target_language,
        question_type: "ALGORITHMIC",
        max_solve_time_minutes: 30,
      }));

      await api.generateBatch(payload);
      router.push("/runs");
    } catch (err: any) {
      setError(err.message || "Failed to dispatch batch generation");
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="max-w-3xl mx-auto shadow-sm">
      <form onSubmit={handleSubmit}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-600" />
            <span>Batch Question Generation</span>
          </CardTitle>
          <CardDescription>
            Fan-out generation across multiple topics and difficulty tiers in parallel
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">
              {error}
            </div>
          )}

          <div className="space-y-3">
            {items.map((item, idx) => (
              <div
                key={item.id}
                className="flex items-center gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg"
              >
                <span className="text-xs font-mono font-semibold text-slate-400 w-6">
                  #{idx + 1}
                </span>

                <div className="flex-1 grid grid-cols-3 gap-2">
                  <select
                    value={item.topic}
                    onChange={(e) => updateItem(item.id, "topic", e.target.value)}
                    className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600"
                  >
                    <option value="Arrays">Arrays</option>
                    <option value="Strings">Strings</option>
                    <option value="Hash Maps">Hash Maps</option>
                    <option value="Trees">Trees</option>
                    <option value="Graphs">Graphs</option>
                    <option value="Dynamic Programming">Dynamic Programming</option>
                    <option value="Binary Search">Binary Search</option>
                    <option value="Sorting">Sorting</option>
                  </select>

                  <select
                    value={item.difficulty}
                    onChange={(e) => updateItem(item.id, "difficulty", e.target.value)}
                    className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600 font-medium"
                  >
                    <option value="EASY">EASY</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HARD">HARD</option>
                    <option value="EXPERT">EXPERT</option>
                  </select>

                  <select
                    value={item.target_language}
                    onChange={(e) => updateItem(item.id, "target_language", e.target.value)}
                    className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600"
                  >
                    <option value="python">Python 3</option>
                    <option value="javascript">JavaScript</option>
                    <option value="java">Java</option>
                    <option value="cpp">C++</option>
                  </select>
                </div>

                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  disabled={items.length <= 1}
                  onClick={() => removeItem(item.id)}
                  className="h-8 w-8 text-slate-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>

          <Button
            type="button"
            variant="outline"
            onClick={addItem}
            className="w-full text-xs h-9 gap-1 text-slate-600 border-dashed"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Another Question
          </Button>
        </CardContent>

        <CardFooter className="flex justify-between items-center border-t border-slate-100 pt-4">
          <span className="text-xs text-slate-500">
            {items.length} question{items.length > 1 ? "s" : ""} queued for parallel dispatch
          </span>
          <Button type="submit" disabled={isSubmitting} className="gap-2 px-6">
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Dispatching Batch...
              </>
            ) : (
              <>
                <Layers className="w-4 h-4" />
                Dispatch Batch ({items.length}) →
              </>
            )}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
