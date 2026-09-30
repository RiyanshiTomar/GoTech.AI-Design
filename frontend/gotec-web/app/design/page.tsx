"use client";

import { useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  Sparkles,
  Loader2,
  ArrowLeft,
  Download,
  AlertCircle,
} from "lucide-react";
import { generateDesign, mediaUrl, GenerateResponse } from "@/lib/api";
import SpecPanel from "@/components/SpecPanel";

const Viewer3D = dynamic(() => import("@/components/Viewer3D"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-slate-900 rounded-2xl">
      <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
    </div>
  ),
});

const EXAMPLES = [
  "3BHK in Mumbai, 1200 sqft, north facing, Vastu compliant, with pooja room",
  "2BHK compact flat, 850 sqft, east facing, modern design",
  "4BHK luxury villa, 2500 sqft, south facing, with study and store room",
  "1BHK studio, 500 sqft, north facing, simple layout",
];

export default function DesignPage() {
  const [prompt, setPrompt] = useState(EXAMPLES[0]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"2d" | "3d">("2d");

  const onGenerate = async () => {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await generateDesign(prompt);
      setResult(res);
      setTab("2d");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-white/5">
        <Link href="/" className="flex items-center gap-2 text-slate-300 hover:text-amber-400 transition">
          <ArrowLeft className="w-4 h-4" />
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center font-bold text-slate-900 text-sm">
            G
          </div>
          <span className="font-semibold">GoTec.AI</span>
        </Link>
        <div className="text-sm text-slate-400">Design Studio · POC</div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8 grid lg:grid-cols-[380px_1fr] gap-6">
        {/* Left: Input panel */}
        <div className="space-y-4">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <h2 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              Describe your home
            </h2>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={4}
              className="w-full bg-slate-950/60 border border-white/10 rounded-xl p-3 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-500/50 resize-none"
              placeholder="e.g. 3BHK, 1200 sqft, north facing, Vastu..."
            />

            <div className="mt-3">
              <div className="text-xs text-slate-500 mb-2">Try examples:</div>
              <div className="flex flex-wrap gap-2">
                {EXAMPLES.map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => setPrompt(ex)}
                    className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 border border-white/5 transition"
                  >
                    {ex.split(",")[0]}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={onGenerate}
              disabled={loading || !prompt.trim()}
              className="mt-4 w-full flex items-center justify-center gap-2 px-5 py-3 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-semibold text-slate-900 transition shadow-lg shadow-amber-500/20"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Generate Design
                </>
              )}
            </button>

            {loading && (
              <div className="mt-3 text-xs text-slate-400 space-y-1">
                <Stage n={1} label="Parsing prompt with LLM" />
                <Stage n={2} label="Rendering 2D plan with SDXL" />
                <Stage n={3} label="Reconstructing 3D with TripoSR" />
              </div>
            )}

            {error && (
              <div className="mt-3 flex items-start gap-2 bg-rose-500/10 border border-rose-500/30 rounded-lg p-3 text-xs text-rose-200">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold mb-1">Backend not reachable</div>
                  <div className="opacity-80">{error}</div>
                  <div className="opacity-80 mt-1">
                    Start backend: <code className="bg-slate-900 px-1 rounded">cd backend && uvicorn app.main:app --reload</code>
                  </div>
                </div>
              </div>
            )}

            {result && (
              <div className="mt-3 text-xs text-emerald-300 bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3">
                ✓ Generated in {result.processing_time_sec}s · {result.message}
              </div>
            )}
          </div>

          <SpecPanel spec={result?.spec} />
        </div>

        {/* Right: Output viewer */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTab("2d")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                tab === "2d"
                  ? "bg-amber-500 text-slate-900"
                  : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              2D Plan
            </button>
            <button
              onClick={() => setTab("3d")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                tab === "3d"
                  ? "bg-amber-500 text-slate-900"
                  : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              3D Model
            </button>

            {result?.image_2d_url && tab === "2d" && (
              <a
                href={mediaUrl(result.image_2d_url)}
                download
                className="ml-auto flex items-center gap-1.5 px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs text-slate-300"
              >
                <Download className="w-3.5 h-3.5" /> Download
              </a>
            )}
          </div>

          <div className="h-[640px]">
            {tab === "2d" ? (
              <div className="w-full h-full bg-slate-900 rounded-2xl border border-white/10 overflow-hidden flex items-center justify-center relative">
                {result?.image_2d_url ? (
                  <img
                    src={mediaUrl(result.image_2d_url)}
                    alt="2D Floor Plan"
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <EmptyState
                    title="No 2D plan yet"
                    subtitle="Enter a prompt and click Generate to see your floor plan."
                  />
                )}
              </div>
            ) : (
              <Viewer3D spec={result?.spec ?? null} imageUrl={result?.image_2d_url} />
            )}
          </div>

          {result?.model_3d_url && (
            <div className="text-xs text-slate-500 text-center">
              3D mesh: <code className="text-slate-400">{result.model_3d_url}</code>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

function Stage({ n, label }: { n: number; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-5 h-5 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-[10px] text-amber-300">
        {n}
      </div>
      <div className="flex-1 flex items-center gap-2">
        <Loader2 className="w-3 h-3 animate-spin text-amber-400" />
        {label}...
      </div>
    </div>
  );
}

function EmptyState({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="text-center px-6">
      <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-amber-500/20 to-orange-500/10 border border-amber-500/20 flex items-center justify-center">
        <Sparkles className="w-7 h-7 text-amber-400" />
      </div>
      <div className="text-lg font-semibold text-white mb-1">{title}</div>
      <div className="text-sm text-slate-400">{subtitle}</div>
    </div>
  );
}
