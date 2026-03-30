import { apiGet, clearTokens, requireAuth } from "./api.js";

requireAuth();

document.getElementById("logout").addEventListener("click", (e) => {
  e.preventDefault(); clearTokens(); window.location.href = "/index.html";
});

const TYPE_LABELS = {
  rust: "Rust", duurloop: "Duurloop", interval: "Interval",
  tempo: "Tempo", lange_duur: "Lange duurloop", herstel: "Herstel",
};
const ALL_DAYS = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"];

const schemaId = new URLSearchParams(location.search).get("id");

async function loadSchema() {
  const resp = await apiGet(schemaId ? `/schemas/${schemaId}` : "/schemas/active");
  if (!resp) return;
  if (!resp.ok) {
    document.getElementById("schema-container").innerHTML =
      '<p>Geen schema gevonden. <a href="/dashboard.html">Ga terug naar dashboard</a>.</p>';
    return;
  }
  const schema = await resp.json();
  const data = schema.schema_data;

  document.getElementById("schema-summary").textContent = data.samenvatting || "";

  const container = document.getElementById("schema-container");
  (data.weken || []).forEach(week => {
    const card = document.createElement("div");
    card.className = "card";
    const dayMap = Object.fromEntries(week.dagen.map(d => [d.dag, d]));

    card.innerHTML = `<h2 style="margin-bottom:.75rem;">Week ${week.week}</h2>`;
    const grid = document.createElement("div");
    grid.className = "week-grid";

    ALL_DAYS.forEach(day => {
      const entry = dayMap[day];
      const cell = document.createElement("div");
      cell.className = `day-cell ${entry ? entry.type : "rust"}`;
      cell.innerHTML = `
        <div class="day-name">${day.slice(0, 2).toUpperCase()}</div>
        <div class="train-type">${entry ? TYPE_LABELS[entry.type] || entry.type : "—"}</div>
        ${entry && entry.afstand_km ? `<div style="font-size:.7rem;margin-top:.3rem;">${entry.afstand_km} km</div>` : ""}
      `;
      if (entry && entry.beschrijving) {
        const desc = document.createElement("p");
        desc.style.cssText = "font-size:.7rem;margin-top:.3rem;color:var(--gray-600);line-height:1.3;";
        desc.textContent = entry.beschrijving;
        cell.appendChild(desc);
      }
      grid.appendChild(cell);
    });

    card.appendChild(grid);
    container.appendChild(card);
  });
}

loadSchema();
