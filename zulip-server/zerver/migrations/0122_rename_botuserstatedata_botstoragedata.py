# Generated by Django 1.11.6 on 2017-11-24 09:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zerver', '0121_realm_signup_notifications_stream'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='BotUserStateData',
            new_name='BotStorageData',
        ),
    ]
