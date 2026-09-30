import Link from "next/link";
import { Sparkles, Box, Layers, Zap, ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
      </div>

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center font-bold text-slate-900">
            G
          </div>
          <span className="text-xl font-bold tracking-tight">GoTec.AI</span>
        </div>
        <div className="flex items-center gap-6 text-sm text-slate-300">
          <Link href="/design" className="hover:text-amber-400 transition">Try Demo</Link>
          <a href="#features" className="hover:text-amber-400 transition">Features</a>
          <a href="#how" className="hover:text-amber-400 transition">How it Works</a>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 max-w-7xl mx-auto px-8 pt-16 pb-24 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm mb-8">
          <Sparkles className="w-4 h-4" />
          AI for Indian Real Estate Design
        </div>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-tight">
          From a single prompt to
          <br />
          <span className="bg-gradient-to-r from-amber-400 via-orange-400 to-emerald-400 bg-clip-text text-transparent">
            2D plans & 3D walkthroughs
          </span>
        </h1>
        <p className="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto mb-10">
          Describe your dream home in plain English. Get Vastu-aware floor plans,
          photorealistic renders, and interactive 3D models in seconds.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/design"
            className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 rounded-xl font-semibold text-slate-900 transition shadow-lg shadow-amber-500/20"
          >
            Try the Demo <ArrowRight className="w-5 h-5" />
          </Link>
          <a
            href="#how"
            className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl font-semibold transition"
          >
            See How it Works
          </a>
        </div>
        <p className="mt-6 text-sm text-slate-500">
          Built for builders, architects, and home buyers across India
        </p>
      </section>

      {/* Features */}
      <section id="features" className="relative z-10 max-w-7xl mx-auto px-8 py-20">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">
          One prompt. Three deliverables.
        </h2>
        <p className="text-center text-slate-400 mb-16 max-w-2xl mx-auto">
          Built on open-source AI models. Trained on Indian housing typologies.
        </p>
        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard
            icon={<Layers className="w-7 h-7" />}
            title="Text to 2D Plan"
            desc="LLM parses your prompt. SDXL renders a clean architectural floor plan with rooms, doors, and windows."
            accent="amber"
          />
          <FeatureCard
            icon={<Box className="w-7 h-7" />}
            title="2D to 3D Model"
            desc="TripoSR converts the plan into a 3D mesh. View it in your browser with Three.js — rotate, zoom, walk through."
            accent="emerald"
          />
          <FeatureCard
            icon={<Zap className="w-7 h-7" />}
            title="Vastu + Bylaws"
            desc="Indian-first design: Vastu zone compliance, city-specific FAR and setback checks baked into the spec."
            accent="rose"
          />
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="relative z-10 max-w-5xl mx-auto px-8 py-20">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">
          How it works
        </h2>
        <div className="space-y-6">
          <Step n={1} title="Describe your home"
            desc="3BHK in Mumbai, 1200 sqft, north facing, Vastu compliant, with pooja room" />
          <Step n={2} title="AI extracts structured spec"
            desc="Mistral LLM converts your prompt into rooms, areas, orientation, and constraints." />
          <Step n={3} title="2D blueprint generated"
            desc="Stable Diffusion XL renders a top-down architectural floor plan from the spec." />
          <Step n={4} title="3D model built & displayed"
            desc="TripoSR reconstructs the 3D geometry. View interactively in your browser." />
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 max-w-4xl mx-auto px-8 py-20 text-center">
        <div className="bg-gradient-to-br from-amber-500/10 to-emerald-500/10 border border-white/10 rounded-3xl p-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to see it in action?
          </h2>
          <p className="text-slate-300 mb-8">
            Type your dream home. Get plans + 3D in under a minute.
          </p>
          <Link
            href="/design"
            className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 rounded-xl font-semibold text-slate-900 transition"
          >
            Launch Demo <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      <footer className="relative z-10 text-center text-slate-500 text-sm py-10 border-t border-white/5">
        © 2026 GoTec.AI · Building the future of Indian real estate
      </footer>
    </main>
  );
}

function FeatureCard({
  icon, title, desc, accent,
}: { icon: React.ReactNode; title: string; desc: string; accent: string }) {
  const colorMap: Record<string, string> = {
    amber: "from-amber-400/20 to-orange-500/10 text-amber-300",
    emerald: "from-emerald-400/20 to-teal-500/10 text-emerald-300",
    rose: "from-rose-400/20 to-pink-500/10 text-rose-300",
  };
  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-7 hover:bg-white/[0.07] transition">
      <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${colorMap[accent]} mb-4`}>
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}

function Step({ n, title, desc }: { n: number; title: string; desc: string }) {
  return (
    <div className="flex gap-5 items-start bg-white/5 border border-white/10 rounded-2xl p-6">
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center font-bold text-slate-900">
        {n}
      </div>
      <div>
        <h3 className="text-lg font-semibold mb-1">{title}</h3>
        <p className="text-slate-400 text-sm">{desc}</p>
      </div>
    </div>
  );
}
