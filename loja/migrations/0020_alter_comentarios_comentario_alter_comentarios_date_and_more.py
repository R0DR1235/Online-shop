# Generated by Django 4.0.3 on 2022-06-02 15:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0019_alter_comentarios_comentario_alter_comentarios_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comentarios',
            name='comentario',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='comentarios',
            name='date',
            field=models.DateField(default=datetime.datetime(2022, 6, 2, 16, 25, 34, 480087)),
        ),
        migrations.AlterField(
            model_name='compras',
            name='date',
            field=models.DateField(default=datetime.datetime(2022, 6, 2, 16, 25, 34, 481085)),
        ),
    ]
