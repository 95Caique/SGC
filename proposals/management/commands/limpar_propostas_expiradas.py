from django.core.management.base import BaseCommand

from proposals.services import ServicoProposta


class Command(BaseCommand):
    help = "Marca propostas vencidas como expiradas."

    def handle(self, *args, **options):
        total = ServicoProposta.limpar_propostas_expiradas()
        self.stdout.write(self.style.SUCCESS(f"{total} proposta(s) expirada(s)."))
