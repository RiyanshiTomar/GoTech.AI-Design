/** API client for the Architecture Agent backend (architect-agent/). One project = one persistent building model. */
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Phase = "idle" | "understanding" | "planning" | "generating" | "validating" | "repairing" | "rendering" | "ready" | "failed";

export const PHASE_LABEL: Record<string, string> = {
  idle: "Idle", understanding: "Understanding your request", planning: "Planning the layout",
  generating: "Generating the design", validating: "Validating the geometry",
  repairing: "Repairing validation errors", rendering: "Building plan, 3D and IFC", ready: "Ready", failed: "Failed",
};

export interface Issue {
  code: string;
  severity?: "ERROR" | "WARNING" | "HEURISTIC";
  object_ids?: string[];
  objects?: string[];
  message?: string;
  details?: unknown;
  hint?: string;
}

export interface Report {
  valid: boolean;
  errors: Issue[];
  warnings: Issue[];
  summary?: Record<string, number>;
}

export interface Status {
  valid: boolean;
  stale?: boolean;
  built_at?: number;
  report?: Report;
  export_errors?: Issue[];
  artifacts: { svg?: string[]; ifc?: string; glb?: string };
}

export interface DesignState {
  project_id: string;
  phase: Phase;
  design: string;
  model: { floors: { id: string; name: string }[] } | null;
  status: Status;
}

export interface ChatResponse {
  reply?: string;
  valid?: boolean;
  rolled_back?: boolean;
  rejected?: Report | null;
  error?: string;
  state?: DesignState;
}

const KEY = "gotec.project_id";

async function parse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}));
  if (!res.ok && !(data as { error?: string }).error) {
    (data as { error?: string }).error = `API error: ${res.status}`;
  }
  return data as T;
}

const stored = () => { try { return localStorage.getItem(KEY); } catch { return null; } };
const remember = (id: string) => { try { localStorage.setItem(KEY, id); } catch { /* private mode */ } };

export const createProject = async () => {
  const s = await fetch(`${API_BASE}/api/projects`, { method: "POST" }).then(parse<DesignState>);
  remember(s.project_id);
  return s;
};

export const getProject = (id: string) => fetch(`${API_BASE}/api/projects/${id}`, { cache: "no-store" }).then(parse<DesignState>);

/** Re-open the project saved in this browser, or start a new one. The id stays the same across messages. */
let opening: Promise<DesignState> | null = null;   // React dev mode runs effects twice: share one call, make one project
export function openProject(): Promise<DesignState> {
  return (opening ??= open().catch((e) => { opening = null; throw e; }));
}

async function open(): Promise<DesignState> {
  const id = stored();
  if (id) {
    const res = await fetch(`${API_BASE}/api/projects/${id}`, { cache: "no-store" });
    if (res.ok) return res.json();
  }
  return createProject();
}

export const sendMessage = (id: string, message: string) =>
  fetch(`${API_BASE}/api/projects/${id}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  }).then(parse<ChatResponse>);

/** URL of a generated file; `v` busts the browser cache after each rebuild. */
export const fileUrl = (id: string, rel: string, v?: number) =>
  `${API_BASE}/api/projects/${id}/files/${rel}${v ? `?v=${v}` : ""}`;

export const issueText = (i: Issue) => i.message ?? (typeof i.details === "string" ? i.details : "");
