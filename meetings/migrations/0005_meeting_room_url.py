# Generated by Django 5.1.6 on 2025-03-15 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0004_meeting_is_started'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='room_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
