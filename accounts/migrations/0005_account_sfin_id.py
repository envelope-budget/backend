# Generated by Django 5.0.7 on 2025-03-18 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_simplefinconnection"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="sfin_id",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
