const BASE = "";

function getTokens() {
  return {
    access: localStorage.getItem("access_token"),
    refresh: localStorage.getItem("refresh_token"),
  };
}

function saveTokens(access, refresh) {
  localStorage.setItem("access_token", access);
  if (refresh) localStorage.setItem("refresh_token", refresh);
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function refreshAccessToken() {
  const { refresh } = getTokens();
  if (!refresh) return false;
  const resp = await fetch(`${BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!resp.ok) { clearTokens(); return false; }
  const data = await resp.json();
  saveTokens(data.access_token, data.refresh_token);
  return true;
}

async function apiFetch(path, options = {}, retry = true) {
  const { access } = getTokens();
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (access) headers["Authorization"] = `Bearer ${access}`;

  const resp = await fetch(`${BASE}${path}`, { ...options, headers });

  if (resp.status === 401 && retry) {
    const ok = await refreshAccessToken();
    if (ok) return apiFetch(path, options, false);
    window.location.href = "/index.html";
    return null;
  }
  return resp;
}

async function apiGet(path) {
  return apiFetch(path);
}

async function apiPost(path, body) {
  return apiFetch(path, { method: "POST", body: JSON.stringify(body) });
}

async function apiPut(path, body) {
  return apiFetch(path, { method: "PUT", body: JSON.stringify(body) });
}

async function apiDelete(path) {
  return apiFetch(path, { method: "DELETE" });
}

function requireAuth() {
  if (!getTokens().access) window.location.href = "/index.html";
}

export { apiFetch, apiGet, apiPost, apiPut, apiDelete, saveTokens, clearTokens, requireAuth };
