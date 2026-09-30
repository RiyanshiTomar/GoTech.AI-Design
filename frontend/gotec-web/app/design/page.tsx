"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Loader2, AlertCircle, Download, Sparkles, Square, Box } from "lucide-react";
import Nav from "@/components/Nav";
import { generateDesign, mediaUrl, GenerateResponse } from "@/lib/api";
import SpecPanel from "@/components/SpecPanel";

const Viewer3D = dynamic(() => import("@/components/Viewer3D"), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center"><Loader2 className="w-6 h-6 text-gold animate-spin" /></div>,
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
    setLoading(true); setError(null); setResult(null);
    try {
      setResult(await generateDesign(prompt)); setTab("2d");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally { setLoading(false); }
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Nav wide />
      <div className="flex-1 min-h-0 flex flex-col lg:flex-row">
        {/* Left: fixed-width control panel, scrolls inside itself */}
        <aside className="lg:w-[380px] lg:shrink-0 lg:h-full overflow-y-auto border-b lg:border-b-0 lg:border-r border-line bg-white p-5 space-y-5">
          <div>
            <h1 className="text-xl font-bold tracking-tight">AI Designer</h1>
            <p className="mt-1 text-sm text-ink/60">Describe your home to get a 2D plan and a 3D model.</p>
          </div>

          <div>
            <label htmlFor="prompt" className="text-sm font-medium">Requirements</label>
            <textarea
              id="prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={5}
              placeholder="e.g. 3BHK, 1200 sqft, north facing, Vastu compliant"
              className="mt-2 w-full border border-line rounded-lg p-3 text-sm resize-none focus:outline-none focus:border-gold"
            />
            <div className="mt-3 flex flex-wrap gap-2">
              {EXAMPLES.map((ex) => (
                <button key={ex} onClick={() => setPrompt(ex)} className="text-xs px-2.5 py-1.5 rounded-md bg-card border border-line hover:border-gold">
                  {ex.split(",")[0]}
                </button>
              ))}
            </div>
            <button onClick={onGenerate} disabled={loading || !prompt.trim()} className="btn-dark w-full mt-4 disabled:opacity-50 disabled:cursor-not-allowed">
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" />Generating…</> : <><Sparkles className="w-4 h-4" />Generate design</>}
            </button>
            {loading && <p className="mt-3 text-xs text-ink/60">Parsing your prompt, rendering the 2D plan and building the 3D model. This can take a minute.</p>}
            {error && (
              <div className="mt-3 flex gap-2 bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-800">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <div className="font-semibold">Could not reach the backend</div>
                  <div className="mt-0.5 opacity-80 break-words">{error}</div>
                </div>
              </div>
            )}
            {result && <p className="mt-3 text-xs text-emerald-700">Generated in {result.processing_time_sec}s. {result.message}</p>}
            {result && !result.model_3d_url && result.model_3d_error && (
              <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 break-words">
                <div className="font-semibold">3D model failed</div>
                {result.model_3d_error}
              </div>
            )}
          </div>

          <SpecPanel spec={result?.spec} />
        </aside>

        {/* Right: viewer fills all remaining space, never resizes */}
        <section className="flex-1 min-w-0 min-h-[420px] lg:min-h-0 flex flex-col bg-card">
          <div className="shrink-0 h-12 flex items-center gap-6 px-5 border-b border-line bg-white">
            {([["2d", "2D floor plan", Square], ["3d", "3D model", Box]] as const).map(([k, label, I]) => (
              <button key={k} onClick={() => setTab(k)} className={`h-full flex items-center gap-2 text-sm border-b-2 ${tab === k ? "border-gold font-medium" : "border-transparent text-ink/60 hover:text-ink"}`}>
                <I className="w-4 h-4" />{label}
              </button>
            ))}
            {result?.image_2d_url && tab === "2d" && (
              <a href={mediaUrl(result.image_2d_url)} download className="ml-auto flex items-center gap-1.5 text-sm text-ink/70 hover:text-ink"><Download className="w-4 h-4" />Download</a>
            )}
          </div>
          <div className="flex-1 min-h-0 relative">
            {tab === "2d" ? (
              result?.image_2d_url ? (
                <img src={mediaUrl(result.image_2d_url)} alt="2D floor plan" className="absolute inset-0 w-full h-full object-contain p-4" />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-6 text-ink/50">
                  {loading ? <Loader2 className="w-7 h-7 animate-spin text-gold" /> : (<><div className="font-medium text-ink/80">No design yet</div><p className="text-sm mt-1">Enter your requirements and click Generate design.</p></>)}
                </div>
              )
            ) : (
              <div className="absolute inset-0"><Viewer3D spec={result?.spec ?? null} imageUrl={result?.image_2d_url} modelUrl={result?.model_3d_url ? mediaUrl(result.model_3d_url) : undefined} /></div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
