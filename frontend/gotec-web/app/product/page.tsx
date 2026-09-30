import Link from "next/link";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { ArrowRight, LayoutGrid, FileSpreadsheet, Glasses, MonitorPlay, Building2 } from "lucide-react";

const CAPS = [
  { icon: LayoutGrid, t: "AI plan generator", d: "Generate optimized 2D floor plans from text prompts." },
  { icon: FileSpreadsheet, t: "AI BOQ generator", d: "Auto-generate BOQs with quantities and cost estimates." },
  { icon: Glasses, t: "VR walkthroughs", d: "Explore immersive 3D walkthroughs with stakeholders." },
  { icon: MonitorPlay, t: "AI site monitoring", d: "Track construction progress from site images." },
  { icon: Building2, t: "Standardized typologies", d: "Pre-built 2 BHK, 2.5 BHK and 3 BHK designs for faster execution." },
];

export default function Product() {
  return (
    <>
      <Nav />
      <main>
        <section className="section !pb-10">
          <div className="container-x grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="eyebrow mb-4">AI design engine</div>
              <h1 className="text-4xl md:text-5xl font-bold tracking-tight leading-[1.1]">From text to <span className="text-gold">2D and 3D designs</span></h1>
              <p className="mt-5 text-lg text-ink/75 leading-relaxed">
                Describe your housing requirements in plain language. GoTec.AI generates floor plans, 3D layouts and renders for MIG housing projects in minutes, not months.
              </p>
              <div className="mt-8"><Link href="/design" className="btn-dark">Try AI Designer <ArrowRight className="w-4 h-4" /></Link></div>
            </div>
            <img src="/img/product-hero.jpg" alt="AI designer on a tablet" className="w-full aspect-[16/9] object-cover rounded-2xl border border-line" />
          </div>
        </section>

        <section className="section !pt-10">
          <div className="container-x grid md:grid-cols-2 gap-6">
            {[["2D plan", "/img/plan2d.jpg"], ["3D render", "/img/plan3d.jpg"]].map(([l, src]) => (
              <figure key={l} className="bg-white border border-line rounded-2xl overflow-hidden">
                <img src={src} alt={l} className="w-full aspect-[4/3] object-cover" />
                <figcaption className="px-5 py-3 text-sm text-ink/70 border-t border-line">{l}</figcaption>
              </figure>
            ))}
          </div>
        </section>

        <section className="section bg-card border-y border-line">
          <div className="container-x">
            <div className="max-w-xl">
              <div className="eyebrow mb-3">Capabilities</div>
              <h2 className="text-3xl font-bold tracking-tight">A design-to-delivery platform for MIG housing</h2>
            </div>
            <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {CAPS.map(({ icon: I, t, d }) => (
                <div key={t} className="bg-white border border-line rounded-xl p-6">
                  <I className="w-6 h-6 text-gold" strokeWidth={1.6} />
                  <h3 className="mt-4 font-semibold">{t}</h3>
                  <p className="mt-2 text-sm text-ink/70 leading-relaxed">{d}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="section">
          <div className="container-x">
            <div className="max-w-xl mb-8">
              <div className="eyebrow mb-3">Gallery</div>
              <h2 className="text-3xl font-bold tracking-tight">From floor plans to living spaces</h2>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((n) => <img key={n} src={`/img/gal${n}.jpg`} alt={`Design ${n}`} className="w-full h-36 object-cover rounded-xl border border-line" />)}
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
