const PROJECT = "default";

async function json(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok && !data.error) data.error = `HTTP ${res.status}`;
  return data;
}

export const api = {
  project: PROJECT,
  state: () => fetch(`/api/state?project=${PROJECT}`).then(json),
  chat: (message) =>
    fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, project: PROJECT }) }).then(json),
  reset: () => fetch(`/api/reset?project=${PROJECT}`, { method: "POST" }).then(json),
  rebuild: () => fetch(`/api/rebuild?project=${PROJECT}`, { method: "POST" }).then(json),
  fileUrl: (rel) => `/api/files/${PROJECT}/${rel}?t=${Date.now()}`,
};
