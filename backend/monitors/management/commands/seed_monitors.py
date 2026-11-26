from django.core.management.base import BaseCommand

from monitors.models import Monitor


DEFAULT_MONITORS = [
    ("Sepefrei", "https://sepefrei.fr"),
    ("Link", "https://link.sepefrei.fr"),
    ("Étudiant", "https://etudiant.sepefrei.fr"),
    ("Portainer", "https://portainer.sepefrei.fr"),
    ("Plausible", "https://plausible.sepefrei.fr"),
    ("n8n", "https://n8n.sepefrei.fr"),
]


class Command(BaseCommand):
    help = "Ajoute les sites de la Junior-Entreprise s'ils n'existent pas déjà."

    def handle(self, *args, **options):
        for name, url in DEFAULT_MONITORS:
            
            monitor, created = Monitor.objects.get_or_create(
                url=url,
                defaults={"name": name},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Ajouté : {monitor.name}"))
            else:
                self.stdout.write(f"Déjà présent : {monitor.name}")