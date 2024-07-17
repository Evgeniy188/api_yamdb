import csv

from django.conf import settings
from django.core.management import BaseCommand
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User

TABLES = {
    User: 'users.csv',
    Category: 'category.csv',
    Genre: 'genre.csv',
    Title: 'titles.csv',
    Review: 'review.csv',
    Comment: 'comments.csv',
}


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for model, f_csv in TABLES.items():
            with open(
                f'{settings.BASE_DIR}/static/data/{f_csv}',
                'r',
                encoding='utf-8',
            ) as file_csv:
                reader = csv.DictReader(file_csv)
                model.objects.bulk_create(model(**data) for data in reader)
        self.stdout.write(self.style.SUCCESS('Данные загружены!'))
