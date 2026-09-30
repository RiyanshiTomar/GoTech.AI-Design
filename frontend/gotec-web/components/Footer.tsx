import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-line mt-8">
      <div className="container-x py-10 flex flex-col sm:flex-row gap-4 justify-between text-sm text-ink/60">
        <div>
          <div className="text-ink font-bold text-lg">GoTec<span className="text-gold">.</span>AI</div>
          <p className="mt-1">AI Operating System for India&apos;s housing industry.</p>
        </div>
        <div className="flex gap-6 items-start">
          <Link href="/product" className="hover:text-ink">Product</Link>
          <Link href="/design" className="hover:text-ink">AI Designer</Link>
          <Link href="/#problem" className="hover:text-ink">Problem</Link>
        </div>
        <div>© 2026 GoTec.AI</div>
      </div>
    </footer>
  );
}
