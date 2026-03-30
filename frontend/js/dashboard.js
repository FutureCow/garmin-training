import { apiGet, apiPost, clearTokens, requireAuth } from "./api.js";

requireAuth();

document.getElementById("logout").addEventListener("click", (e) => {
  e.preventDefault(); clearTokens(); window.location.href = "/index.html";
});

const TYPE_LABELS = {
  rust: "Rust", duurloop: "Duurloop", interval: "Interval",
  tempo: "Tempo", lange_duur: "Lange duurloop", herstel: "Herstel",
};
const ALL_DAYS = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"];

function renderWeek(dagen, weekNr) {
  document.getElementById("week-title").textContent = `Week ${weekNr} — komende 7 dagen`;
  const grid = document.getElementById("week-grid");
  grid.innerHTML = "";
  const dayMap = Object.fromEntries(dagen.map(d => [d.dag, d]));
  ALL_DAYS.forEach(day => {
    const entry = dayMap[day];
    const cell = document.createElement("div");
    cell.className = `day-cell ${entry ? entry.type : "rust"}`;
    cell.innerHTML = `
      <div class="day-name">${day.slice(0, 2).toUpperCase()}</div>
      <div class="train-type">${entry ? TYPE_LABELS[entry.type] || entry.type : "Rust"}</div>
      ${entry && entry.afstand_km ? `<div style="font-size:.7rem;margin-top:.3rem;">${entry.afstand_km} km</div>` : ""}
    `;
    if (entry && entry.beschrijving) cell.title = entry.beschrijving;
    grid.appendChild(cell);
  });
}

async function loadActiveSchema() {
  const resp = await apiGet("/schemas/active");
  if (!resp) return;
  if (resp.status === 404) {
    document.getElementById("no-schema").style.display = "block";
    return;
  }
  const schema = await resp.json();
  const data = schema.schema_data;

  document.getElementById("schema-summary").style.display = "block";
  document.getElementById("week-preview").style.display = "block";
  document.getElementById("schema-type-badge").innerHTML =
    `<span class="badge badge-green">${data.schema_type === "rolling" ? "Rolling" : `${data.weken?.length || "?"} weken`}</span>`;
  document.getElementById("schema-summary-text").textContent =
    data.samenvatting || `Niveau: ${data.niveau || "onbekend"}`;

  if (data.weken && data.weken.length > 0) {
    renderWeek(data.weken[0].dagen, 1);
  }
}

document.getElementById("generate-btn").addEventListener("click", async () => {
  document.getElementById("generating").style.display = "block";
  document.getElementById("generate-btn").disabled = true;
  document.getElementById("alert").style.display = "none";

  const resp = await apiPost("/schemas/generate", {});

  document.getElementById("generating").style.display = "none";
  document.getElementById("generate-btn").disabled = false;

  if (!resp || !resp.ok) {
    const err = resp ? await resp.json() : { detail: "Onbekende fout" };
    const alertEl = document.getElementById("alert");
    alertEl.className = "alert alert-error";
    alertEl.textContent = err.detail || "Schema genereren mislukt";
    alertEl.style.display = "block";
    return;
  }
  loadActiveSchema();
});

loadActiveSchema();
