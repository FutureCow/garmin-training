import { apiGet, apiPut, apiDelete, clearTokens, requireAuth } from "./api.js";

requireAuth();

const DAYS = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"];

function showAlert(msg, type = "error") {
  const el = document.getElementById("alert");
  el.className = `alert alert-${type}`;
  el.textContent = msg;
  el.style.display = "block";
  setTimeout(() => el.style.display = "none", 4000);
}

// Build day checkboxes
const checkboxContainer = document.getElementById("day-checkboxes");
DAYS.forEach(day => {
  const label = document.createElement("label");
  label.innerHTML = `<input type="checkbox" name="day" value="${day}" /> ${day.charAt(0).toUpperCase() + day.slice(1)}`;
  checkboxContainer.appendChild(label);
});

function getActiveDays() {
  return [...document.querySelectorAll('[name=day]:checked')].map(el => el.value);
}

function updateLongRunOptions() {
  const activeDays = getActiveDays();
  const select = document.getElementById("long-run-day");
  const current = select.value;
  select.innerHTML = activeDays.map(d => `<option value="${d}">${d.charAt(0).toUpperCase() + d.slice(1)}</option>`).join("");
  if (activeDays.includes(current)) select.value = current;
}

document.querySelectorAll('[name=day]').forEach(cb =>
  cb.addEventListener("change", updateLongRunOptions)
);

document.getElementById("goal-distance").addEventListener("change", function () {
  document.getElementById("custom-distance-group").style.display =
    this.value === "custom" ? "block" : "none";
});

document.getElementById("schema-type").addEventListener("change", function () {
  const isFixed = this.value === "fixed";
  document.getElementById("weeks-group").style.display = isFixed ? "block" : "none";
  document.getElementById("startdate-group").style.display = isFixed ? "block" : "none";
});

// Logout
document.getElementById("logout").addEventListener("click", (e) => {
  e.preventDefault();
  clearTokens();
  window.location.href = "/index.html";
});

// Load Garmin status
async function loadGarminStatus() {
  const resp = await apiGet("/preferences/garmin-status");
  if (!resp) return;
  const data = await resp.json();
  const statusEl = document.getElementById("garmin-status");
  statusEl.innerHTML = data.connected
    ? '<span class="badge badge-green">Verbonden ✓</span>'
    : '<span class="badge badge-red">Niet verbonden</span>';
  document.getElementById("remove-garmin").style.display = data.connected ? "inline-block" : "none";
}

// Save Garmin credentials
document.getElementById("save-garmin").addEventListener("click", async () => {
  const garmin_username = document.getElementById("garmin-username").value.trim();
  const garmin_password = document.getElementById("garmin-password").value;
  if (!garmin_username || !garmin_password) { showAlert("Vul beide velden in"); return; }
  const resp = await apiPut("/preferences/garmin-credentials", { garmin_username, garmin_password });
  if (resp && resp.ok) { showAlert("Garmin-account opgeslagen", "success"); loadGarminStatus(); }
  else showAlert("Opslaan mislukt");
});

// Remove Garmin credentials
document.getElementById("remove-garmin").addEventListener("click", async () => {
  const resp = await apiDelete("/preferences/garmin-credentials");
  if (resp && resp.ok) { showAlert("Garmin-account verwijderd", "success"); loadGarminStatus(); }
});

// Load preferences
async function loadPreferences() {
  const resp = await apiGet("/preferences");
  if (!resp || resp.status === 404) return;
  const data = await resp.json();
  (data.active_days || []).forEach(day => {
    const cb = document.querySelector(`[name=day][value="${day}"]`);
    if (cb) cb.checked = true;
  });
  updateLongRunOptions();
  if (data.long_run_day) document.getElementById("long-run-day").value = data.long_run_day;
  if (data.goal_distance) document.getElementById("goal-distance").value = data.goal_distance;
  if (data.goal_distance === "custom") {
    document.getElementById("custom-distance-group").style.display = "block";
    document.getElementById("goal-distance-km").value = data.goal_distance_km || "";
  }
  if (data.goal_pace) document.getElementById("goal-pace").value = data.goal_pace;
  if (data.goal_time) document.getElementById("goal-time").value = data.goal_time;
  if (data.schema_type) {
    document.getElementById("schema-type").value = data.schema_type;
    const isFixed = data.schema_type === "fixed";
    document.getElementById("weeks-group").style.display = isFixed ? "block" : "none";
    document.getElementById("startdate-group").style.display = isFixed ? "block" : "none";
  }
  if (data.schema_weeks) document.getElementById("schema-weeks").value = data.schema_weeks;
  if (data.start_date) document.getElementById("start-date").value = data.start_date;
}

// Save preferences
document.getElementById("save-prefs").addEventListener("click", async () => {
  const active_days = getActiveDays();
  if (active_days.length === 0) { showAlert("Selecteer minstens één trainingsdag"); return; }
  const body = {
    active_days,
    long_run_day: document.getElementById("long-run-day").value,
    goal_distance: document.getElementById("goal-distance").value,
    goal_distance_km: document.getElementById("goal-distance").value === "custom"
      ? parseFloat(document.getElementById("goal-distance-km").value) : null,
    goal_pace: document.getElementById("goal-pace").value || null,
    goal_time: document.getElementById("goal-time").value || null,
    schema_type: document.getElementById("schema-type").value,
    schema_weeks: parseInt(document.getElementById("schema-weeks").value),
    start_date: document.getElementById("start-date").value || null,
  };
  const resp = await apiPut("/preferences", body);
  if (resp && resp.ok) showAlert("Voorkeuren opgeslagen", "success");
  else showAlert("Opslaan mislukt");
});

loadGarminStatus();
loadPreferences();
