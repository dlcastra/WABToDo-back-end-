# Generated by Django 5.1 on 2024-12-10 16:04

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_remove_team_members_teammember"),
    ]

    operations = [
        migrations.AddField(
            model_name="team",
            name="list_of_members",
            field=models.ManyToManyField(related_name="team_members", to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name="TeamMember",
        ),
    ]
