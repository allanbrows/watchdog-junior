const API_URL = "http://127.0.0.1:8000";

// Protège contre l'injection de HTML dans les messages d'erreur
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

async function loadLogs() {
  const message = document.getElementById("message");
  const body = document.getElementById("logs-body");

  // Lit l'id dans l'URL : history.html?id=3
  const id = new URLSearchParams(window.location.search).get("id");
  if (!id) {
    message.textContent = "Aucun site sélectionné.";
    return;
  }

  try {
    const response = await fetch(`${API_URL}/logs/${id}`);
    if (!response.ok) {
      message.textContent = "Site introuvable.";
      return;
    }
    const logs = await response.json();

    body.innerHTML = "";
    if (logs.length === 0) {
      message.textContent = "Aucun ping enregistré pour l'instant.";
      return;
    }

    for (const log of logs) {
      const tr = document.createElement("tr");
      const date = new Date(log.checked_at).toLocaleString("fr-FR");
      const result = log.is_success ? "✅ OK" : "❌ Échec";
      const code = log.status_code ?? "-";
      const time = log.response_time_ms !== null ? `${log.response_time_ms} ms` : "-";
      const error = log.error_message ? escapeHtml(log.error_message) : "";

      tr.innerHTML = `
        <td>${date}</td>
        <td>${result}</td>
        <td>${code}</td>
        <td>${time}</td>
        <td>${error}</td>
      `;
      body.appendChild(tr);
    }
  } catch (error) {
    message.textContent = "Impossible de joindre l'API.";
  }
}

loadLogs();