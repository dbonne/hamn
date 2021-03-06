# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-05 22:19
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AggregatorLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ts', models.DateTimeField(auto_now=True)),
                ('success', models.BooleanField()),
                ('info', models.TextField()),
            ],
            options={
                'db_table': 'aggregatorlog',
                'ordering': ['-ts'],
            },
        ),
        migrations.CreateModel(
            name='AuditEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logtime', models.DateTimeField(default=datetime.datetime.now)),
                ('user', models.CharField(max_length=32)),
                ('logtxt', models.CharField(max_length=1024)),
            ],
            options={
                'db_table': 'auditlog',
                'ordering': ['logtime'],
            },
        ),
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feedurl', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('blogurl', models.CharField(max_length=255)),
                ('lastget', models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0))),
                ('approved', models.BooleanField(default=False)),
                ('archived', models.BooleanField(default=False)),
                ('authorfilter', models.CharField(blank=True, default='', max_length=255)),
                ('twitteruser', models.CharField(blank=True, default='', max_length=255)),
                ('excludestats', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'feeds',
                'ordering': ['approved', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('guid', models.CharField(max_length=255)),
                ('link', models.CharField(max_length=255)),
                ('txt', models.TextField()),
                ('dat', models.DateTimeField()),
                ('title', models.CharField(max_length=255)),
                ('guidisperma', models.BooleanField(default=False)),
                ('hidden', models.BooleanField(default=False)),
                ('twittered', models.BooleanField(default=False)),
                ('shortlink', models.CharField(max_length=255)),
                ('feed', models.ForeignKey(db_column='feed', on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='register.Blog')),
            ],
            options={
                'db_table': 'posts',
                'ordering': ['-dat'],
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teamurl', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'teams',
            },
        ),
        migrations.AddField(
            model_name='blog',
            name='team',
            field=models.ForeignKey(blank=True, db_column='team', null=True, on_delete=django.db.models.deletion.CASCADE, to='register.Team'),
        ),
        migrations.AddField(
            model_name='blog',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='aggregatorlog',
            name='feed',
            field=models.ForeignKey(db_column='feed', on_delete=django.db.models.deletion.CASCADE, to='register.Blog'),
        ),
        migrations.AlterUniqueTogether(
            name='post',
            unique_together=set([('id', 'guid')]),
        ),
    ]
