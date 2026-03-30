import { apiPost, saveTokens } from "./api.js";

function showAlert(msg) {
  const el = document.getElementById("alert");
  el.textContent = msg;
  el.style.display = "block";
}

document.getElementById("show-register").addEventListener("click", (e) => {
  e.preventDefault();
  document.getElementById("login-form").style.display = "none";
  document.getElementById("register-form").style.display = "block";
  document.getElementById("alert").style.display = "none";
});

document.getElementById("show-login").addEventListener("click", (e) => {
  e.preventDefault();
  document.getElementById("register-form").style.display = "none";
  document.getElementById("login-form").style.display = "block";
  document.getElementById("alert").style.display = "none";
});

document.getElementById("login-btn").addEventListener("click", async () => {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const resp = await apiPost("/auth/login", { email, password });
  if (!resp.ok) {
    showAlert((await resp.json()).detail || "Inloggen mislukt");
    return;
  }
  const data = await resp.json();
  saveTokens(data.access_token, data.refresh_token);
  window.location.href = "/dashboard.html";
});

document.getElementById("register-btn").addEventListener("click", async () => {
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const resp = await apiPost("/auth/register", { email, password });
  if (!resp.ok) {
    showAlert((await resp.json()).detail || "Registratie mislukt");
    return;
  }
  const data = await resp.json();
  saveTokens(data.access_token, data.refresh_token);
  window.location.href = "/settings.html";
});
