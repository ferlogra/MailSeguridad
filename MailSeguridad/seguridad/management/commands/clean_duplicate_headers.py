from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = (
        "Elimina registros duplicados por InternetMessageHeaders, "
        "conservando el de menor ID"
    )

    def handle(self, *args, **options):
        sql = """
        DELETE FROM Mensajes
        WHERE InternetMessageHeaders IS NOT NULL
          AND InternetMessageHeaders != ''
          AND id NOT IN (
            SELECT MIN(id)
            FROM Mensajes
            WHERE InternetMessageHeaders IS NOT NULL
              AND InternetMessageHeaders != ''
            GROUP BY InternetMessageHeaders
          );
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            self.stdout.write(self.style.SUCCESS(
                f"Eliminados {cursor.rowcount} registros duplicados"
            ))
