# Generated by Django 5.1.6 on 2025-04-04 23:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bustComProj', '0002_trainingplan'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='role',
            field=models.CharField(choices=[('admin', 'Администратор'), ('hr', 'HR-менеджер'), ('teacher', 'Преподаватель'), ('training_manager', 'Менеджер по обучению'), ('employee', 'Сотрудник')], default='employee', max_length=20),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('admin', 'Администратор'), ('hr', 'HR-менеджер'), ('teacher', 'Преподаватель'), ('training_manager', 'Менеджер по обучению'), ('employee', 'Сотрудник')], default='employee', max_length=20),
        ),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('запись', 'Запись на курс'), ('отчислен', 'Отчисление с курса'), ('завершение', 'Завершение курса'), ('прогресс', 'Прогресс по курсу')], max_length=20)),
                ('details', models.TextField(blank=True, null=True)),
                ('log_time', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bustComProj.course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-log_time'],
            },
        ),
    ]
