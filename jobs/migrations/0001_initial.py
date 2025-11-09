# Generated migration for jobs app

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
            name='JobPosting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(db_index=True, max_length=50)),
                ('external_id', models.CharField(max_length=255)),
                ('hash', models.CharField(db_index=True, max_length=64, unique=True)),
                ('title', models.CharField(max_length=500)),
                ('company', models.CharField(blank=True, max_length=255)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('remote', models.BooleanField(default=False)),
                ('url', models.URLField(max_length=1000)),
                ('description', models.TextField()),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('raw_data', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'ordering': ['-published_at', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserJobPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desired_locations', models.CharField(blank=True, help_text="Comma-separated locations, e.g., 'New York,Remote,San Francisco'", max_length=500)),
                ('remote_only', models.BooleanField(default=False)),
                ('keywords', models.CharField(blank=True, help_text="Comma-separated keywords, e.g., 'python,django,react'", max_length=500)),
                ('min_score_threshold', models.FloatField(default=0.6, help_text='Minimum matching score (0.0 - 1.0) to receive notifications')),
                ('email_enabled', models.BooleanField(default=True)),
                ('max_jobs_per_email', models.IntegerField(default=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='job_preference', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Job Preference',
                'verbose_name_plural': 'User Job Preferences',
            },
        ),
        migrations.CreateModel(
            name='JobDispatchLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(help_text='Matching score for this job-user pair')),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dispatches', to='jobs.jobposting')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_dispatches', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-sent_at'],
            },
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['-published_at'], name='jobs_jobpos_publish_idx'),
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['remote'], name='jobs_jobpos_remote_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='jobposting',
            unique_together={('source', 'external_id')},
        ),
        migrations.AddIndex(
            model_name='jobdispatchlog',
            index=models.Index(fields=['user', '-sent_at'], name='jobs_jobdis_user_id_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='jobdispatchlog',
            unique_together={('user', 'job')},
        ),
    ]
