import { apiGet, clearTokens, requireAuth } from "./api.js";

requireAuth();

document.getElementById("logout").addEventListener("click", (e) => {
  e.preventDefault(); clearTokens(); window.location.href = "/index.html";
});

async function loadHistory() {
  const resp = await apiGet("/schemas");
  if (!resp || !resp.ok) return;
  const schemas = await resp.json();
  const container = document.getElementById("list-container");

  if (schemas.length === 0) {
    container.innerHTML = "<p>Nog geen schema's gegenereerd.</p>";
    return;
  }

  schemas.forEach(schema => {
    const data = schema.schema_data;
    const date = new Date(schema.created_at).toLocaleDateString("nl-NL", {
      day: "numeric", month: "long", year: "numeric",
    });
    const card = document.createElement("div");
    card.className = "card";
    card.style.display = "flex";
    card.style.justifyContent = "space-between";
    card.style.alignItems = "center";
    card.innerHTML = `
      <div>
        <strong>${date}</strong>
        <span style="margin-left:.75rem;" class="badge ${schema.is_active ? "badge-green" : ""}">
          ${schema.is_active ? "Actief" : "Archief"}
        </span>
        <p style="font-size:.85rem;color:var(--gray-600);margin-top:.25rem;">
          ${schema.schema_type === "rolling" ? "Rolling" : `${data.weken?.length || "?"} weken`}
          — ${data.niveau || ""}
        </p>
      </div>
      <a href="/schema.html?id=${schema.id}" class="btn btn-outline">Bekijken →</a>
    `;
    container.appendChild(card);
  });
}

loadHistory();
