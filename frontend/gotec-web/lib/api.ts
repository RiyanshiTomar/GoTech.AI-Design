/** API client for GoTec backend */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface RoomSpec {
  type: string;
  area_sqft?: number;
  attached_bath?: boolean;
  vastu_zone?: string;
}

export interface DesignSpec {
  bhk: number;
  total_area_sqft: number;
  facing: string;
  vastu_compliant: boolean;
  rooms: RoomSpec[];
  floors: number;
  city?: string;
  notes?: string;
}

export interface GenerateResponse {
  success: boolean;
  spec?: DesignSpec;
  image_2d_url?: string;
  model_3d_url?: string;
  model_3d_error?: string;
  processing_time_sec: number;
  message: string;
}

export async function generateDesign(prompt: string): Promise<GenerateResponse> {
  const res = await fetch(`${API_BASE}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error: ${res.status} ${err}`);
  }
  return res.json();
}

export function mediaUrl(path: string | undefined): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}
