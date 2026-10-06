import { store } from "./store.js";

export function initDebug() {
  const body = document.getElementById("debug-body");
  const tabs = document.getElementById("debug-tabs");
  let sub = "validation";

  tabs.addEventListener("click", (e) => {
    const b = e.target.closest("[data-sub]"); if (!b) return;
    sub = b.dataset.sub; tabs.querySelectorAll(".seg-btn").forEach((x) => x.classList.toggle("active", x === b)); render(store.get());
  });

  function issue(i, cls) {
    const d = document.createElement("div"); d.className = `issue ${cls}`;
    d.innerHTML = `<div><span class="code"></span> <span class="objs"></span></div><div class="det"></div>`;
    d.querySelector(".code").textContent = i.code; d.querySelector(".objs").textContent = (i.objects || []).join(", ");
    d.querySelector(".det").textContent = i.details;
    if (i.hint) { const h = document.createElement("div"); h.className = "hint"; h.textContent = i.hint; d.appendChild(h); }
    return d;
  }

  function render(s) {
    body.innerHTML = "";
    if (sub === "validation") {
      const rep = s.status && s.status.report;
      if (!rep) { body.textContent = "Nothing validated yet."; return; }
      if (rep.valid) { const ok = document.createElement("div"); ok.className = "ok-box"; ok.textContent = "VALID - all hard rules passed."; body.appendChild(ok); }
      (rep.errors || []).forEach((i) => body.appendChild(issue(i, "error")));
      (rep.warnings || []).forEach((i) => body.appendChild(issue(i, "warning")));
      (s.status.export_errors || []).forEach((i) => body.appendChild(issue(i, "error")));
      if (rep.summary && rep.summary.rooms !== undefined) {
        const p = document.createElement("pre"); p.textContent = "\n" + JSON.stringify(rep.summary); body.appendChild(p);
      }
    } else {
      const pre = document.createElement("pre");
      pre.textContent = sub === "model" ? (s.model ? JSON.stringify(s.model, null, 2) : "No model yet.") : s.design || "";
      body.appendChild(pre);
    }
  }
  store.subscribe(render);
}
