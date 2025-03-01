import pandas as pd
from django.core.management.base import BaseCommand
from main.models import Article

class Command(BaseCommand):
    help = "Load articles from an Excel file into the database."

    def handle(self, *args, **kwargs):
        file_path = "main/static/datasets/Article dataset.xlsx"  # Update this path if needed
        try:
            xlsx = pd.ExcelFile(file_path)
            for sheet_name in xlsx.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                for _, row in df.iterrows():
                    Article.objects.create(
                        title=row['Title'],
                        author=row['Author'],
                        tags=row['Tags'],
                        topic=row['Topic'],
                        read_time=row['Read Time'],
                        claps=row['Claps'],
                        content=row['Content'],
                        url=row['URL'],
                        date_posted=row['Date posted'],
                        subject=sheet_name  # Use sheet name as the subject
                    )
            self.stdout.write(self.style.SUCCESS("Articles loaded successfully!"))
        except Exception as e:
            self.stderr.write(f"Error loading articles: {e}")
