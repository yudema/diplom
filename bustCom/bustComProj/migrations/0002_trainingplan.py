# Generated by Django 5.1.7 on 2025-03-21 07:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bustComProj', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('status', models.CharField(choices=[('draft', 'Черновик'), ('active', 'Активный'), ('completed', 'Завершен'), ('cancelled', 'Отменен')], default='draft', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('courses', models.ManyToManyField(related_name='training_plans', to='bustComProj.course')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('employees', models.ManyToManyField(related_name='assigned_training_plans', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
