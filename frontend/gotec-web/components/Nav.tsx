"use client";

import Link from "next/link";
import { useState } from "react";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";

const LINKS = [
  { label: "Home", href: "/" },
  { label: "Product", href: "/product" },
  { label: "Problem", href: "/#problem" },
  { label: "How it works", href: "/#how" },
];

export default function Nav({ wide = false }: { wide?: boolean }) {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-40 bg-background/90 backdrop-blur border-b border-line">
      <div className={`${wide ? "px-6" : "container-x"} h-16 flex items-center justify-between`}>
        <Link href="/" className="text-xl font-bold tracking-tight">GoTec<span className="text-gold">.</span>AI</Link>
        <nav className="hidden md:flex items-center gap-8 text-[15px] text-ink/75">
          {LINKS.map((l) => (
            <Link key={l.label} href={l.href} className={path === l.href ? "text-ink font-medium" : "hover:text-ink"}>{l.label}</Link>
          ))}
        </nav>
        <div className="hidden md:block"><Link href="/design" className="btn-dark">Try AI Designer</Link></div>
        <button className="md:hidden p-2" aria-label="Menu" onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button>
      </div>
      {open && (
        <div className="md:hidden border-t border-line bg-background container-x py-4 flex flex-col gap-3">
          {LINKS.map((l) => <Link key={l.label} href={l.href} onClick={() => setOpen(false)}>{l.label}</Link>)}
          <Link href="/design" className="btn-dark" onClick={() => setOpen(false)}>Try AI Designer</Link>
        </div>
      )}
    </header>
  );
}
