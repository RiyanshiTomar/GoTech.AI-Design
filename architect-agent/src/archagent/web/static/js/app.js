import { api } from "./api.js";
import { store } from "./store.js";
import { initChat } from "./chat.js";
import { initPlan } from "./plan.js";
import { initViewer } from "./viewer3d.js";
import { initDebug } from "./debug.js";

const viewer = initViewer();
initPlan();
initDebug();
initChat(() => {});

document.querySelectorAll(".tab").forEach((t) =>
  t.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === t));
    document.querySelectorAll(".pane").forEach((p) => p.classList.toggle("active", p.id === `tab-${t.dataset.tab}`));
    if (t.dataset.tab === "model3d") viewer.resize();
  }));

api.state().then((s) => store.set(s)).catch(() => {});
