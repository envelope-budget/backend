# Generated by Django 5.0.7 on 2024-08-02 00:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_account_slug"),
        ("budgets", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="account",
            name="slug",
            field=models.SlugField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name="account",
            unique_together={("budget", "slug")},
        ),
    ]