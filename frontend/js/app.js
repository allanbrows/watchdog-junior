const API_URL = "http://127.0.0.1:8000";

const STATUS_ICONS = {
  up: "🟢",
  down: "🔴",
  pending: "⏳",
};

// Protège contre l'injection de HTML : un nom de site contenant <script>
// s'afficherait sinon comme du vrai code.
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

async function loadMonitors() {
  const list = document.getElementById("monitor-list");
  const message = document.getElementById("message");

  try {
    const response = await fetch(`${API_URL}/monitors`);
    if (!response.ok) {
      throw new Error(`Erreur HTTP ${response.status}`);
    }
    const monitors = await response.json();

    list.innerHTML = "";
    message.textContent = monitors.length === 0 ? "Aucun site surveillé pour l'instant." : "";

    for (const monitor of monitors) {
      const li = document.createElement("li");
      const icon = STATUS_ICONS[monitor.status] || "❓";
      // monitor.id est un nombre généré par Django : pas besoin de l'échapper
      li.innerHTML = `
        <span class="status">${icon}</span>
        <div>
          <a href="history.html?id=${monitor.id}">${escapeHtml(monitor.name)}</a>
          <small>${escapeHtml(monitor.url)}</small>
        </div>
      `;
      list.appendChild(li);
    }
  } catch (error) {
    message.textContent = "Impossible de joindre l'API.";
  }
}

// Envoi du formulaire : POST /monitors
document.getElementById("add-form").addEventListener("submit", async (event) => {
  event.preventDefault(); // empêche le rechargement de la page

  const form = event.target;
  const message = document.getElementById("message");

  const payload = {
    name: document.getElementById("name").value.trim(),
    url: document.getElementById("url").value.trim(),
    // l'API refuse un texte : on convertit en nombre
    frequency_seconds: Number(document.getElementById("frequency").value),
  };

  try {
    const response = await fetch(`${API_URL}/monitors`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      form.reset();       // vide le formulaire (la fréquence revient à 60)
      loadMonitors();     // rafraîchit la liste
    } else {
      const data = await response.json();
      message.textContent = data.error || "Erreur lors de l'ajout.";
    }
  } catch (error) {
    message.textContent = "Impossible de joindre l'API.";
  }
});

loadMonitors();

setInterval(loadMonitors, 10000); // rafraîchit la liste toutes les 10 secondes