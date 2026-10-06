"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Loader2, Send, Square, Box, Bug, RotateCcw, Download } from "lucide-react";
import Nav from "@/components/Nav";
import {
  DesignState, Issue, PHASE_LABEL, createProject, fileUrl, getProject, issueText, openProject, sendMessage,
} from "@/lib/api";

const Viewer3D = dynamic(() => import("@/components/Viewer3D"), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center"><Loader2 className="w-6 h-6 text-gold animate-spin" /></div>,
});

const EXAMPLES = [
  "Create a 20 m x 30 m 3BHK house with a living room, kitchen, two bathrooms and parking.",
  "Make the master bedroom larger.",
  "Move the kitchen beside the living room.",
  "Add a first floor with two bedrooms.",
];

type Msg = { role: "user" | "agent" | "system" | "error"; text: string; issues?: Issue[] };
type Tab = "2d" | "3d" | "debug";

function IssueList({ issues }: { issues: Issue[] }) {
  return (
    <ul className="mt-2 space-y-1">
      {issues.slice(0, 8).map((i, k) => (
        <li key={k} className="text-xs border-t border-black/10 pt-1">
          <span className="font-mono font-semibold">{i.code}</span> {(i.objects ?? []).join(", ")} – {issueText(i)}
        </li>
      ))}
    </ul>
  );
}

export default function DesignPage() {
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState("idle");
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "system", text: "Describe a building. I design it, check the geometry, then draw the plan and the 3D model. Next messages edit the same design." },
  ]);
  const [state, setState] = useState<DesignState | null>(null);
  const [tab, setTab] = useState<Tab>("2d");
  const [floor, setFloor] = useState<string | null>(null);
  const [svg, setSvg] = useState("");
  const [hidden, setHidden] = useState<string[]>([]);
  const [resetKey, setResetKey] = useState(0);
  const [debugSub, setDebugSub] = useState<"validation" | "model" | "design">("validation");
  const endRef = useRef<HTMLDivElement>(null);

  const pid = state?.project_id ?? "";
  const status = state?.status;
  const svgs = status?.artifacts.svg ?? [];
  const v = status?.built_at ? Math.round(status.built_at * 1000) : undefined;
  const floors = (state?.model?.floors ?? []);
  const glb = status?.artifacts.glb;
  const ifc = status?.artifacts.ifc;

  useEffect(() => {
    openProject().then((s) => {
      setState(s);
      if (s.model) setMsgs([{ role: "system", text: "Continuing your saved project. Next messages edit the same design." }]);
    }).catch(() => setMsgs((m) => [...m, { role: "error", text: "Could not reach the backend. Is it running?" }]));
  }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, busy]);

  // keep a valid selected floor and load its SVG (inline, so room ids stay clickable)
  useEffect(() => {
    if (!svgs.length) { setSvg(""); return; }
    const ids = svgs.map((p) => p.match(/floorplan-(.+)\.svg$/)?.[1] ?? "");
    const current = floor && ids.includes(floor) ? floor : ids[0];
    if (current !== floor) setFloor(current);
    const path = svgs[ids.indexOf(current)];
    fetch(fileUrl(pid, path, v)).then((r) => r.text()).then((t) => {
      setSvg(t.replace(/ width="[^"]*" height="[^"]*"/, ""));
    }).catch(() => setSvg(""));
  }, [svgs.join("|"), floor, v]); // eslint-disable-line react-hooks/exhaustive-deps

  const onSend = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput(""); setBusy(true); setPhase("understanding");
    setMsgs((m) => [...m, { role: "user", text }]);
    // the server reports its stage; poll it while the request is running
    const poll = setInterval(() => { getProject(pid).then((s) => setPhase(s.phase)).catch(() => {}); }, 500);
    try {
      const res = await sendMessage(pid, text);
      if (res.state) setState(res.state);
      if (res.error) {
        setMsgs((m) => [...m, { role: "error", text: res.error! }]);
      } else {
        const add: Msg[] = [];
        if (res.reply) add.push({ role: "agent", text: res.reply });
        if (res.rolled_back) add.push({ role: "system", text: "That change could not be made valid, so your previous valid design was kept.", issues: res.rejected?.errors });
        else if (!res.valid) add.push({ role: "system", text: "The design is not valid yet:", issues: res.state?.status.report?.errors });
        setMsgs((m) => [...m, ...add]);
      }
    } catch (e: unknown) {
      setMsgs((m) => [...m, { role: "error", text: e instanceof Error ? e.message : "Could not reach the backend" }]);
    } finally { clearInterval(poll); setBusy(false); setPhase("idle"); }
  };

  const onReset = async () => {
    if (!confirm("Start a new design? The current one will be discarded.")) return;
    setState(await createProject()); setSvg(""); setFloor(null);
    setMsgs([{ role: "system", text: "New design. Describe your building." }]);
  };

  const errCount = status?.report?.errors.length ?? 0;
  const chip = busy ? [PHASE_LABEL[phase] ?? "Working…", "bg-amber-50 text-amber-800 border-amber-200"]
    : status?.valid ? ["Valid", "bg-emerald-50 text-emerald-700 border-emerald-200"]
    : errCount ? [`${errCount} error${errCount > 1 ? "s" : ""}`, "bg-red-50 text-red-700 border-red-200"]
    : ["No design", "text-ink/50 border-line"];

  const tabs: [Tab, string, typeof Square][] = [["2d", "2D plan", Square], ["3d", "3D model", Box], ["debug", "Model / Debug", Bug]];

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Nav wide />
      <div className="flex-1 min-h-0 flex flex-col lg:flex-row">
        {/* Chat */}
        <aside className="lg:w-[380px] lg:shrink-0 lg:h-full min-h-[320px] flex flex-col border-b lg:border-b-0 lg:border-r border-line bg-white">
          <div className="shrink-0 flex items-center justify-between px-5 py-3 border-b border-line">
            <h1 className="font-bold tracking-tight">AI Architect</h1>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2.5 py-0.5 rounded-full border ${chip[1]}`}>{chip[0]}</span>
              <button onClick={onReset} title="New design" className="p-1.5 rounded-md border border-line hover:border-gold"><RotateCcw className="w-3.5 h-3.5" /></button>
            </div>
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-3">
            {msgs.map((m, i) => (
              <div key={i} className={`text-sm rounded-lg px-3 py-2 whitespace-pre-wrap break-words max-w-[94%] ${
                m.role === "user" ? "ml-auto bg-ink text-white"
                : m.role === "agent" ? "bg-card"
                : m.role === "error" ? "bg-red-50 text-red-800 border border-red-200 max-w-full"
                : "border border-dashed border-line text-ink/60 text-xs max-w-full"}`}>
                {m.text}
                {m.issues && <IssueList issues={m.issues} />}
              </div>
            ))}
            {busy && <div className="text-xs text-ink/50 flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />{PHASE_LABEL[phase] ?? "Working"}…</div>}
            <div ref={endRef} />
          </div>
          <div className="shrink-0 px-4 pb-2 flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button key={ex} onClick={() => setInput(ex)} title={ex} className="text-xs px-2.5 py-1 rounded-full border border-line hover:border-gold">
                {ex.length > 40 ? ex.slice(0, 38) + "…" : ex}
              </button>
            ))}
          </div>
          <form onSubmit={(e) => { e.preventDefault(); onSend(); }} className="shrink-0 flex gap-2 p-4 border-t border-line">
            <textarea
              value={input} onChange={(e) => setInput(e.target.value)} rows={2} maxLength={4000}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSend(); } }}
              placeholder="Describe the building, or ask for a change…"
              className="flex-1 border border-line rounded-lg p-2.5 text-sm resize-none focus:outline-none focus:border-gold"
            />
            <button type="submit" disabled={busy || !input.trim()} className="btn-dark px-4 disabled:opacity-50"><Send className="w-4 h-4" /></button>
          </form>
        </aside>

        {/* Preview */}
        <section className="flex-1 min-w-0 min-h-[420px] lg:min-h-0 flex flex-col bg-card">
          <div className="shrink-0 h-12 flex items-center gap-6 px-5 border-b border-line bg-white">
            {tabs.map(([k, label, I]) => (
              <button key={k} onClick={() => setTab(k)} className={`h-full flex items-center gap-2 text-sm border-b-2 ${tab === k ? "border-gold font-medium" : "border-transparent text-ink/60 hover:text-ink"}`}>
                <I className="w-4 h-4" />{label}
              </button>
            ))}
            {status?.stale && svgs.length > 0 && <span className="text-xs text-amber-700">Showing last valid version</span>}
            <div className="ml-auto flex items-center gap-4 text-sm text-ink/70">
              {tab === "3d" && glb && <a className="flex items-center gap-1 hover:text-ink" href={fileUrl(pid, glb, v)} download="building.glb"><Download className="w-4 h-4" />GLB</a>}
              {tab === "3d" && ifc && <a className="flex items-center gap-1 hover:text-ink" href={fileUrl(pid, ifc, v)} download="building.ifc"><Download className="w-4 h-4" />IFC</a>}
              {tab === "2d" && svgs.length > 0 && floor && <a className="flex items-center gap-1 hover:text-ink" href={fileUrl(pid, svgs.find((p) => p.includes(`floorplan-${floor}.svg`)) ?? svgs[0], v)} download={`floorplan-${floor}.svg`}><Download className="w-4 h-4" />SVG</a>}
            </div>
          </div>

          {tab === "2d" && svgs.length > 1 && (
            <div className="shrink-0 flex gap-2 px-5 py-2 border-b border-line bg-white">
              {floors.map((f) => (
                <button key={f.id} onClick={() => setFloor(f.id)} className={`text-xs px-3 py-1 rounded-md border ${floor === f.id ? "bg-ink text-white border-ink" : "border-line hover:border-gold"}`}>{f.name}</button>
              ))}
            </div>
          )}
          {tab === "3d" && floors.length > 1 && glb && (
            <div className="shrink-0 flex items-center gap-2 px-5 py-2 border-b border-line bg-white">
              {floors.map((f) => {
                const off = hidden.includes(`floor-${f.id}`);
                return <button key={f.id} onClick={() => setHidden((h) => off ? h.filter((x) => x !== `floor-${f.id}`) : [...h, `floor-${f.id}`])} className={`text-xs px-3 py-1 rounded-md border ${off ? "opacity-50 border-line" : "bg-ink text-white border-ink"}`}>{f.name}</button>;
              })}
              <button onClick={() => setResetKey((k) => k + 1)} className="ml-auto text-xs px-3 py-1 rounded-md border border-line hover:border-gold">Reset camera</button>
            </div>
          )}

          <div className="flex-1 min-h-0 relative bg-white">
            {tab === "2d" && (svg
              ? <div className="absolute inset-0 overflow-auto p-2 [&>svg]:w-full [&>svg]:h-full" dangerouslySetInnerHTML={{ __html: svg }} />
              : <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-6 text-ink/50">
                  <div className="font-medium text-ink/80">No plan yet</div>
                  <p className="text-sm mt-1">Describe a building in the chat. Invalid designs are never drawn.</p>
                </div>)}
            {tab === "3d" && (
              <div className="absolute inset-0">
                <Viewer3D modelUrl={glb ? fileUrl(pid, glb, v) : undefined} hiddenFloors={hidden} resetKey={resetKey} />
              </div>
            )}
            {tab === "debug" && (
              <div className="absolute inset-0 flex flex-col">
                <div className="shrink-0 flex gap-2 px-5 py-2 border-b border-line">
                  {(["validation", "model", "design"] as const).map((s) => (
                    <button key={s} onClick={() => setDebugSub(s)} className={`text-xs px-3 py-1 rounded-md border ${debugSub === s ? "bg-ink text-white border-ink" : "border-line"}`}>{s === "model" ? "model.json" : s === "design" ? "design.py" : "Validation"}</button>
                  ))}
                </div>
                <div className="flex-1 overflow-auto p-5 text-sm">
                  {debugSub === "validation" && (
                    <div className="space-y-2">
                      {status?.report?.valid && <div className="rounded-md border border-emerald-200 bg-emerald-50 text-emerald-700 px-3 py-2">VALID – all hard rules passed.</div>}
                      {!status?.report && <div className="text-ink/50">Nothing validated yet.</div>}
                      {[...(status?.report?.errors ?? []).map((i) => [i, "border-l-red-500"] as const), ...(status?.report?.warnings ?? []).map((i) => [i, "border-l-amber-500"] as const), ...(status?.export_errors ?? []).map((i) => [i, "border-l-red-500"] as const)].map(([i, c], k) => (
                        <div key={k} className={`border border-line border-l-4 ${c} rounded-md px-3 py-2`}>
                          <span className="font-mono font-semibold text-xs">{i.code}</span> <span className="text-ink/50 text-xs">{(i.objects ?? []).join(", ")}</span>
                          <div>{issueText(i)}</div>
                          {i.hint && <div className="text-xs text-ink/50 mt-0.5">{i.hint}</div>}
                        </div>
                      ))}
                    </div>
                  )}
                  {debugSub === "model" && <pre className="font-mono text-xs whitespace-pre-wrap break-words">{state?.model ? JSON.stringify(state.model, null, 2) : "No model yet."}</pre>}
                  {debugSub === "design" && <pre className="font-mono text-xs whitespace-pre-wrap break-words">{state?.design ?? ""}</pre>}
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
