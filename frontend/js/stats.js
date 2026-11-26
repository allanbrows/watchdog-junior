const API_URL = "http://127.0.0.1:8000";

// Protège contre l'injection de HTML dans les noms de sites
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Formate un pourcentage (null = aucun ping encore)
function formatPercent(value) {
  return value === null ? "-" : `${value} %`;
}

// Formate des secondes en texte lisible : 125 -> "2 min 5 s"
function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return minutes > 0 ? `${minutes} min ${rest} s` : `${rest} s`;
}

async function loadStats() {
  const message = document.getElementById("message");

  try {
    const response = await fetch(`${API_URL}/stats`);
    if (!response.ok) {
      throw new Error(`Erreur HTTP ${response.status}`);
    }
    const data = await response.json();

    // Cartes globales
    const g = data.global;
    document.getElementById("global-stats").innerHTML = `
      <div class="card"><strong>${formatPercent(g.availability_percent)}</strong><span>Disponibilité</span></div>
      <div class="card"><strong>${formatDuration(g.total_downtime_seconds)}</strong><span>Temps en panne</span></div>
      <div class="card"><strong>${g.outage_count}</strong><span>Interruptions</span></div>
      <div class="card"><strong>${g.total_pings}</strong><span>Pings</span></div>
    `;

    // Tableau par site
    const body = document.getElementById("stats-body");
    body.innerHTML = "";
    for (const site of data.monitors) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(site.name)}</td>
        <td>${formatPercent(site.availability_percent)}</td>
        <td>${site.total_pings}</td>
        <td>${site.outage_count}</td>
        <td>${formatDuration(site.downtime_seconds)}</td>
      `;
      body.appendChild(tr);
    }
  } catch (error) {
    message.textContent = "Impossible de joindre l'API.";
  }
}

loadStats();

setInterval(loadStats, 10000);