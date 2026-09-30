import Link from "next/link";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { ArrowRight, X, FileText, Square, Box } from "lucide-react";

const STATS = [
  ["$310B", "Indian real estate market size (2025)"],
  ["30M", "Affordable housing demand by 2030"],
  ["40%", "MIG EMI-to-income ratio, up from 28% in 2020"],
];
const PROBLEMS = ["Manual processes", "Disconnected tools", "Data errors and delays", "Lack of transparency", "MIG buyers underserved"];
const STEPS = [
  { icon: FileText, t: "Describe your project", d: "Write what you need in plain language, like 3 BHK, 1,200 sq ft, modern design." },
  { icon: Square, t: "Get a 2D plan", d: "An optimized floor plan is generated in minutes, aligned with MIG design standards." },
  { icon: Box, t: "View it in 3D", d: "Turn the plan into a 3D layout you can explore in the browser." },
];

export default function Home() {
  return (
    <>
      <Nav />
      <main>
        <section className="section !pt-16">
          <div className="container-x grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="eyebrow mb-4">AI for Indian housing</div>
              <h1 className="text-4xl md:text-5xl font-bold tracking-tight leading-[1.1]">
                The operating system for <span className="text-gold">India&apos;s housing</span> industry
              </h1>
              <p className="mt-5 text-lg text-ink/75 leading-relaxed max-w-lg">
                GoTec.AI brings planning, design and delivery onto one platform, for an industry that still runs on spreadsheets, phone calls and tribal knowledge.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link href="/design" className="btn-dark">Try AI Designer <ArrowRight className="w-4 h-4" /></Link>
                <Link href="/product" className="btn-light">See the product</Link>
              </div>
            </div>
            <img src="/img/hero-city.jpg" alt="Residential towers at sunset" className="w-full aspect-[4/3] object-cover rounded-2xl border border-line" />
          </div>
        </section>

        <section className="border-y border-line bg-card">
          <div className="container-x py-10 grid sm:grid-cols-3 gap-8">
            {STATS.map(([n, l]) => (
              <div key={n}>
                <div className="text-3xl font-bold">{n}</div>
                <div className="mt-1 text-sm text-ink/65">{l}</div>
              </div>
            ))}
          </div>
        </section>

        <section id="problem" className="section">
          <div className="container-x grid lg:grid-cols-2 gap-12 items-center">
            <img src="/img/construction.jpg" alt="Construction site" className="w-full aspect-[4/3] object-cover rounded-2xl border border-line" />
            <div>
              <div className="eyebrow mb-3">The problem</div>
              <h2 className="text-3xl font-bold tracking-tight">Real estate development is stuck in manual work</h2>
              <p className="mt-4 text-ink/75 leading-relaxed">
                Manual processes, disconnected tools and lack of intelligence create delays and higher costs, leaving millions of MIG buyers underserved.
              </p>
              <ul className="mt-6 space-y-3">
                {PROBLEMS.map((p) => (
                  <li key={p} className="flex items-center gap-3 text-[15px]">
                    <span className="w-5 h-5 rounded-full bg-red-100 text-red-600 flex items-center justify-center"><X className="w-3 h-3" strokeWidth={3} /></span>{p}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section id="how" className="section bg-card border-y border-line">
          <div className="container-x">
            <div className="max-w-xl">
              <div className="eyebrow mb-3">How it works</div>
              <h2 className="text-3xl font-bold tracking-tight">From a simple prompt to a finished design</h2>
            </div>
            <div className="mt-10 grid md:grid-cols-3 gap-6">
              {STEPS.map(({ icon: I, t, d }, i) => (
                <div key={t} className="bg-white border border-line rounded-xl p-6">
                  <div className="flex items-center justify-between">
                    <I className="w-6 h-6 text-gold" strokeWidth={1.6} />
                    <span className="text-sm text-ink/40">0{i + 1}</span>
                  </div>
                  <h3 className="mt-4 font-semibold">{t}</h3>
                  <p className="mt-2 text-sm text-ink/70 leading-relaxed">{d}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="section">
          <div className="container-x">
            <div className="bg-ink text-white rounded-2xl px-8 py-12 md:px-14 flex flex-col md:flex-row gap-6 md:items-center justify-between">
              <div>
                <h2 className="text-2xl md:text-3xl font-bold">Design your next project in minutes</h2>
                <p className="mt-2 text-white/70">Describe it, and get 2D plans and 3D layouts back.</p>
              </div>
              <Link href="/design" className="btn-light shrink-0">Open AI Designer <ArrowRight className="w-4 h-4" /></Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
