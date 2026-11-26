# 🐶 Watchdog

Application de supervision de la disponibilité des sites web de la Junior-Entreprise : un gardien visite les sites à intervalles réguliers, enregistre les résultats, et un front affiche statuts, historique et statistiques.

## Stack
- Backend : Django (API JSON), SQLite
- Gardien : commande Django `run_pinger` (bibliothèque `requests`)
- Frontend : HTML, CSS, JavaScript natif
- Tests : `TestCase` de Django

## Lancement

```bash
git clone https://github.com/allanbrows/watchdog-junior.git
cd watchdog-junior
python -m venv venv
.\venv\Scripts\Activate.ps1        # macOS/Linux : source venv/bin/activate
pip install django django-cors-headers requests
cd backend
python manage.py migrate
python manage.py seed_monitors     # ajoute les 6 domaines sepefrei.fr
```

Puis dans **deux terminaux** (venv activé, dossier `backend`) :

```bash
python manage.py runserver         # API : http://127.0.0.1:8000
python manage.py run_pinger        # gardien
```

Ouvrir `frontend/index.html` dans le navigateur.

## Tests

```bash
cd backend
python manage.py test              # 21 tests
```

## API
| Route | Rôle |
|---|---|
| `GET /monitors` | liste des sites avec statut (up / down / pending) |
| `POST /monitors` | ajout d'un site (nom, URL, fréquence >= 10 s) |
| `GET /logs/<id>` | 100 derniers pings d'un site |
| `GET /stats` | disponibilité, interruptions, temps en panne |

## Choix techniques
- Le statut est déduit du dernier ping, pas stocké.
- Le gardien est un processus séparé de l'API.
- Temps en panne = nombre d'échecs × fréquence (approximation).
- Les appels réseau sont simulés dans les tests.

## Avancement
**Terminé** : API, gardien, seed des 6 domaines, front (liste, ajout, historique, stats), 21 tests.
**Non terminé** : Docker, tests front, rafraîchissement automatique, notifications, graphique, `.env.example`.

## Limites connues
- La surveillance n'a lieu que pendant l'exécution du gardien.
- L'URL de l'API est écrite en dur dans le front.
- La `SECRET_KEY` est encore dans `settings.py`.

## Usage de l'IA
J'ai utilisé Claude (Anthropic) comme assistant : proposition d'architecture, aide au débogage.