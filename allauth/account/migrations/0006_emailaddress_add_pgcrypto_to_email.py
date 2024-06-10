# Generated by Django 4.2.4 on 2023-08-23 18:17

import django.db.models.functions.text
from django.db import migrations, models
import pgcrypto


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0005_emailaddress_add_pgcrypto_to_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailaddress',
            name='email',
            field=pgcrypto.fields.EncryptedEmailField(blank=True, charset='utf-8', check_armor=True, cipher='aes', verbose_name='email address', versioned=False),
        ),
    ]
