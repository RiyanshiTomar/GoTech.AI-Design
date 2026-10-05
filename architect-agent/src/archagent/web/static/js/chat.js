import { api } from "./api.js";
import { store } from "./store.js";

const EXAMPLES = [
  "Create a 20 m x 30 m 3BHK house with a living room, kitchen, two bathrooms and parking.",
  "Make the master bedroom larger.",
  "Move the kitchen beside the living room.",
  "Add a first floor with two bedrooms.",
];

export function initChat(onResult) {
  const messages = document.getElementById("messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const send = document.getElementById("send-btn");
  const chip = document.getElementById("status-chip");
  const ex = document.getElementById("examples");

  EXAMPLES.forEach((t) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "example"; b.textContent = t.length > 46 ? t.slice(0, 44) + "..." : t; b.title = t;
    b.onclick = () => { input.value = t; input.focus(); };
    ex.appendChild(b);
  });

  function add(kind, text, issues) {
    const div = document.createElement("div");
    div.className = `msg ${kind}`;
    div.textContent = text;
    if (issues && issues.length) {
      const ul = document.createElement("ul"); ul.className = "issues";
      issues.slice(0, 8).forEach((i) => {
        const li = document.createElement("li");
        const code = document.createElement("span"); code.className = "code"; code.textContent = i.code;
        li.append(code, document.createTextNode(` ${(i.objects || []).join(", ")} - ${i.details}`));
        ul.appendChild(li);
      });
      div.appendChild(ul);
    }
    messages.appendChild(div); messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function setChip(state) {
    const st = state && state.status;
    chip.className = "chip";
    if (state === "busy") { chip.classList.add("chip-busy"); chip.textContent = "Working..."; return; }
    if (!st || (!st.valid && !(st.report && st.report.errors.length))) { chip.classList.add("chip-idle"); chip.textContent = "No design"; return; }
    if (st.valid) { chip.classList.add("chip-ok"); chip.textContent = "Valid"; }
    else { chip.classList.add("chip-bad"); chip.textContent = `${st.report.errors.length} error${st.report.errors.length > 1 ? "s" : ""}`; }
  }
  store.subscribe((s) => setChip(s));

  add("system", "Describe a building and I will design it, validate the geometry, and draw the plan and 3D model. Later messages edit the same design.");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    input.value = ""; add("user", text);
    send.disabled = true; setChip("busy");
    const pending = add("agent typing", "Designing, validating...");
    const res = await api.chat(text).catch((err) => ({ error: String(err) }));
    pending.remove();
    send.disabled = false;
    if (res.state) store.set(res.state);
    if (res.error) { add("error", res.error); setChip(store.get()); return; }
    if (res.reply) add("agent", res.reply);
    if (res.rolled_back) {
      add("system", "That change could not be made valid, so your previous valid design was kept.",
          (res.rejected && res.rejected.errors) || []);
    } else if (!res.valid) {
      add("system", "The design is not valid yet:", (res.status.report || {}).errors);
    }
    onResult && onResult(res);
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
  });

  document.getElementById("reset-btn").onclick = async () => {
    if (!confirm("Start a new design? The current one will be discarded.")) return;
    const s = await api.reset(); store.set(s); messages.innerHTML = ""; add("system", "New design. Describe your building.");
  };
}
