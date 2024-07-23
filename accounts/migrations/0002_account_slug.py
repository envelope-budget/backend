from django.db import migrations, models
from django.utils.text import slugify


def generate_slug(apps, schema_editor):
    Account = apps.get_model("accounts", "Account")
    for account in Account.objects.all():
        account.slug = slugify(account.name)
        account.save()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="slug",
            field=models.SlugField(max_length=255, unique=True, null=True),
        ),
        migrations.RunPython(generate_slug),
        migrations.AlterField(
            model_name="account",
            name="slug",
            field=models.SlugField(max_length=255, unique=True),
        ),
    ]
