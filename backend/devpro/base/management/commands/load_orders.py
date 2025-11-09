from django.core.management.base import BaseCommand
from pathlib import Path

from devpro.base.order_loader import OrderLoader


class Command(BaseCommand):
    help = 'Carrega pedidos do arquivo orders.json para o banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='orders.json',
            help='Caminho para o arquivo JSON'
        )

    def handle(self, *args, **options):
        file_path = options['file']

        self.stdout.write(f'Carregando pedidos de: {file_path}')

        if not Path(file_path).exists():
            self.stdout.write(
                self.style.ERROR(f'Arquivo não encontrado: {file_path}')
            )
            return

        try:
            loader = OrderLoader()
            result = loader.load_from_file(file_path)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Importação concluída!\n"
                    f"   Criados: {result['created']}\n"
                    f"   Atualizados: {result['updated']}\n"
                    f"   Total: {result['total']}"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao importar: {str(e)}')
            )
            raise