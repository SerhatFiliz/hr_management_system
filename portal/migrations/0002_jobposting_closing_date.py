# Generated by Django 5.2.3 on 2025-07-16 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobposting',
            name='closing_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
