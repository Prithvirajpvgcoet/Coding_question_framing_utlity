import {
  DashboardStats,
  QuestionState,
  QuestionSummary,
  RunDetails,
  QuestionBankItem,
  ReferenceDocumentItem,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001/api/v1";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "dev-key-00000001";

function defaultHeaders(): Record<string, string> {
  return {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
  };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errMsg = `Request failed: ${res.status} ${res.statusText}`;
    try {
      const errJson = await res.json();
      errMsg = errJson.detail || errMsg;
    } catch {
      // ignore parse error
    }
    throw new Error(errMsg);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // ── Generation ──
  generate: async (payload: {
    topic: string;
    subtopic?: string;
    difficulty?: string;
    question_type?: string;
    target_language?: string;
    max_solve_time_minutes?: number;
    bank_id?: string;
    custom_constraints?: string[];
  }) => {
    const res = await fetch(`${BASE_URL}/generate`, {
      method: "POST",
      headers: defaultHeaders(),
      body: JSON.stringify(payload),
    });
    return handleResponse<{
      request_id: string;
      question_id: string;
      status: string;
      poll_url: string;
      stream_url: string;
    }>(res);
  },

  generateBatch: async (items: Array<any>) => {
    const res = await fetch(`${BASE_URL}/generate/batch`, {
      method: "POST",
      headers: defaultHeaders(),
      body: JSON.stringify({ items }),
    });
    return handleResponse<{
      batch_id: string;
      count: number;
      items: Array<any>;
    }>(res);
  },

  // ── Status & Stream ──
  getStatus: async (id: string) => {
    const res = await fetch(`${BASE_URL}/status/${id}`, {
      headers: defaultHeaders(),
    });
    return handleResponse<any>(res);
  },

  getStreamUrl: (id: string) => {
    return `${BASE_URL}/stream/${id}?api_key=${encodeURIComponent(API_KEY)}`;
  },

  // ── Questions ──
  listQuestions: async (params?: Record<string, string | number>) => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== "") searchParams.append(k, String(v));
      });
    }
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    const res = await fetch(`${BASE_URL}/questions${query}`, {
      headers: defaultHeaders(),
    });
    return handleResponse<QuestionSummary[]>(res);
  },

  getQuestion: async (id: string) => {
    const res = await fetch(`${BASE_URL}/questions/${id}`, {
      headers: defaultHeaders(),
    });
    return handleResponse<{
      question_id: string;
      status: string;
      version: number;
      state: QuestionState;
      created_at: string | null;
      updated_at: string | null;
    }>(res);
  },

  getPreview: async (id: string) => {
    const res = await fetch(`${BASE_URL}/questions/${id}/preview`, {
      headers: defaultHeaders(),
    });
    return handleResponse<{
      question_id: string;
      html: string;
      code: string;
      language: string;
    }>(res);
  },

  getVersions: async (id: string) => {
    const res = await fetch(`${BASE_URL}/questions/${id}/versions`, {
      headers: defaultHeaders(),
    });
    return handleResponse<{
      question_id: string;
      versions: Array<{
        version: number;
        triggered_by: string | null;
        re_entry_agent: string | null;
        created_at: string | null;
      }>;
    }>(res);
  },

  getScore: async (id: string) => {
    const res = await fetch(`${BASE_URL}/questions/${id}/score`, {
      headers: defaultHeaders(),
    });
    return handleResponse<any>(res);
  },

  // ── Feedback (Approve/Reject) ──
  submitFeedback: async (payload: {
    question_id: string;
    action: "APPROVE" | "REJECT";
    feedback_text?: string;
  }) => {
    const res = await fetch(`${BASE_URL}/feedback`, {
      method: "POST",
      headers: defaultHeaders(),
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  submitBulkFeedback: async (payload: {
    question_ids: string[];
    action: "APPROVE" | "REJECT";
    feedback_text?: string;
  }) => {
    const res = await fetch(`${BASE_URL}/feedback/bulk`, {
      method: "POST",
      headers: defaultHeaders(),
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  // ── Dashboard Stats ──
  getDashboardStats: async () => {
    const res = await fetch(`${BASE_URL}/dashboard/stats`, {
      headers: defaultHeaders(),
    });
    return handleResponse<DashboardStats>(res);
  },

  // ── Runs ──
  listRuns: async () => {
    const res = await fetch(`${BASE_URL}/runs`, {
      headers: defaultHeaders(),
    });
    return handleResponse<Array<any>>(res);
  },

  getRun: async (runId: string) => {
    const res = await fetch(`${BASE_URL}/runs/${runId}`, {
      headers: defaultHeaders(),
    });
    return handleResponse<RunDetails>(res);
  },

  cancelRun: async (runId: string) => {
    const res = await fetch(`${BASE_URL}/runs/${runId}`, {
      method: "DELETE",
      headers: defaultHeaders(),
    });
    return handleResponse<{ status: string; run_id: string }>(res);
  },

  // ── Question Banks ──
  listBanks: async () => {
    const res = await fetch(`${BASE_URL}/banks`, {
      headers: defaultHeaders(),
    });
    return handleResponse<QuestionBankItem[]>(res);
  },

  createBank: async (data: { name: string; description?: string; imocha_bank_id?: string }) => {
    const res = await fetch(`${BASE_URL}/banks`, {
      method: "POST",
      headers: defaultHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse<QuestionBankItem>(res);
  },

  addQuestionsToBank: async (bankId: string, questionIds: string[]) => {
    const res = await fetch(`${BASE_URL}/banks/${bankId}/questions`, {
      method: "POST",
      headers: defaultHeaders(),
      body: JSON.stringify({ question_ids: questionIds }),
    });
    return handleResponse<{ bank_id: string; updated_questions: number }>(res);
  },

  // ── Uploads ──
  listUploads: async () => {
    const res = await fetch(`${BASE_URL}/uploads`, {
      headers: defaultHeaders(),
    });
    return handleResponse<Array<any>>(res);
  },

  createUpload: async (questionId: string, bankId?: string) => {
    const res = await fetch(`${BASE_URL}/uploads`, {
      method: "POST",
      headers: defaultHeaders(),
      body: JSON.stringify({ question_id: questionId, bank_id: bankId }),
    });
    return handleResponse<{ job_id: string; question_id: string; status: string }>(res);
  },

  createBulkUpload: async (questionIds: string[], bankId?: string) => {
    const res = await fetch(`${BASE_URL}/uploads/bulk`, {
      method: "POST",
      headers: defaultHeaders(),
      body: JSON.stringify({ question_ids: questionIds, bank_id: bankId }),
    });
    return handleResponse<{ queued_count: number; job_ids: string[]; status: string }>(res);
  },

  getUploadDetails: async (jobId: string) => {
    const res = await fetch(`${BASE_URL}/uploads/${jobId}`, {
      headers: defaultHeaders(),
    });
    return handleResponse<any>(res);
  },

  retryUpload: async (jobId: string) => {
    const res = await fetch(`${BASE_URL}/uploads/${jobId}/retry`, {
      method: "POST",
      headers: defaultHeaders(),
    });
    return handleResponse<{ status: string; job_id: string }>(res);
  },

  // ── Datasets ──
  listDatasets: async (params?: Record<string, string | number>) => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== "") searchParams.append(k, String(v));
      });
    }
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    const res = await fetch(`${BASE_URL}/datasets${query}`, {
      headers: defaultHeaders(),
    });
    return handleResponse<ReferenceDocumentItem[]>(res);
  },

  seedDatasets: async () => {
    const res = await fetch(`${BASE_URL}/datasets/seed`, {
      method: "POST",
      headers: defaultHeaders(),
    });
    return handleResponse<{ status: string; count: number; message?: string; seeded?: any[] }>(res);
  },

  uploadDatasetFile: async (
    file: File,
    docType: string = "DOMAIN_SCENARIO",
    tags?: string,
    customTopic?: string,
    customDomain?: string
  ) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("doc_type", docType);
    if (tags) {
      formData.append("tags", tags);
    }
    if (customTopic) {
      formData.append("custom_topic", customTopic);
    }
    if (customDomain) {
      formData.append("custom_domain", customDomain);
    }
    const res = await fetch(`${BASE_URL}/datasets/upload`, {
      method: "POST",
      headers: {
        "X-API-Key": API_KEY,
      },
      body: formData,
    });
    return handleResponse<{ status: string; count: number; items: any[] }>(res);
  },

  deleteDataset: async (id: string) => {
    const res = await fetch(`${BASE_URL}/datasets/${id}`, {
      method: "DELETE",
      headers: defaultHeaders(),
    });
    return handleResponse<{ status: string; id: string }>(res);
  },
};
