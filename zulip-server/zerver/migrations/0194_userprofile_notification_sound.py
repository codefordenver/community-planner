# Generated by Django 1.11.6 on 2018-03-12 03:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zerver', '0193_realm_email_address_visibility'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='notification_sound',
            field=models.CharField(default='zulip', max_length=20),
        ),
    ]
