# Generated by Django 4.0.4 on 2022-05-02 10:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0005_alter_categoria_foto'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='produto',
            name='pub_data',
        ),
    ]