# -*- coding: utf-8 -*-
import io
import json
import zipfile
from datetime import datetime
from django.apps import apps
from django.core import serializers
from django.db import connection
from django.utils import timezone
from django.conf import settings
import zoneinfo


class BackupService:
    """Service for creating database backups"""

    # Models to exclude from backup
    EXCLUDED_MODELS = [
        "contenttypes.contenttype",
        "sessions.session",
        "admin.logentry",
        "axes.accessattempt",
        "axes.accesslog",
        "axes.accessfailurelog",
    ]

    def __init__(self, user):
        """
        Initialize backup service
        :param user: User requesting the backup
        """
        self.user = user
        self.user_timezone = self._get_user_timezone()

    def _get_user_timezone(self):
        """Get user's timezone from settings"""
        if hasattr(self.user, "settings") and self.user.settings.timezone:
            return self.user.settings.timezone
        return settings.TIME_ZONE

    def create_backup(self):
        """
        Create a complete database backup
        :return: BytesIO object containing ZIP file
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            zip_buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=6
        ) as zip_file:
            # Add metadata
            metadata = self._create_metadata()
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))

            # Get all models
            models = self._get_all_models()

            # Serialize and add each model's data
            for model in models:
                model_label = f"{model._meta.app_label}.{model._meta.model_name}"

                # Skip excluded models
                if model_label in self.EXCLUDED_MODELS:
                    continue

                # Serialize model data
                data = self._serialize_model(model)

                if data:
                    # Create directory structure: app_label/model_name.json
                    file_path = f"{model._meta.app_label}/{model._meta.model_name}.json"
                    zip_file.writestr(file_path, data)

        zip_buffer.seek(0)
        return zip_buffer

    def _create_metadata(self):
        """Create metadata for the backup"""
        now = timezone.now()
        user_tz = zoneinfo.ZoneInfo(self.user_timezone)
        localized_time = now.astimezone(user_tz)

        # Count total records
        models = self._get_all_models()
        total_records = 0
        models_count = 0

        for model in models:
            model_label = f"{model._meta.app_label}.{model._meta.model_name}"
            if model_label not in self.EXCLUDED_MODELS:
                try:
                    total_records += model.objects.count()
                    models_count += 1
                except Exception:
                    pass

        return {
            "version": "1.0",
            "timestamp": localized_time.isoformat(),
            "database_engine": settings.DATABASES["default"]["ENGINE"],
            "babybuddy_version": self._get_babybuddy_version(),
            "models_count": models_count,
            "total_records": total_records,
            "includes_media": False,
            "created_by": self.user.username,
            "timezone": self.user_timezone,
        }

    def _get_babybuddy_version(self):
        """Get Baby Buddy version"""
        try:
            # Try to get version from package
            import babybuddy

            if hasattr(babybuddy, "__version__"):
                return babybuddy.__version__
        except Exception:
            pass
        return "unknown"

    def _get_all_models(self):
        """Get all models from all installed apps"""
        all_models = []

        for app_config in apps.get_app_configs():
            # Skip Django's internal apps if desired
            if app_config.name.startswith("django.contrib."):
                # Include auth and contenttypes, skip others
                if app_config.name not in [
                    "django.contrib.auth",
                    "django.contrib.contenttypes",
                ]:
                    continue

            all_models.extend(app_config.get_models())

        return all_models

    def _serialize_model(self, model):
        """
        Serialize a model's data to JSON
        :param model: Django model class
        :return: JSON string or None if no data
        """
        try:
            queryset = model.objects.all()

            if not queryset.exists():
                return None

            # Use Django's serialization with natural foreign keys
            data = serializers.serialize(
                "json",
                queryset,
                indent=2,
                use_natural_foreign_keys=True,
                use_natural_primary_keys=False,
            )

            return data

        except Exception as e:
            # Log error but continue with other models
            print(f"Error serializing {model._meta.label}: {e}")
            return None

    def generate_filename(self):
        """
        Generate filename with user's timezone
        Format: backup_MMDDYY_HHMMSS.zip
        """
        user_tz = zoneinfo.ZoneInfo(self.user_timezone)
        now = timezone.now().astimezone(user_tz)
        return f"backup_{now.strftime('%m%d%y_%H%M%S')}.zip"
