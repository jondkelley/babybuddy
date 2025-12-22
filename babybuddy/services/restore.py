# -*- coding: utf-8 -*-
import io
import json
import zipfile
from collections import defaultdict, deque
from django.apps import apps
from django.core import serializers
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .validators import BackupFileValidator, BackupDataValidator


class RestoreService:
    """Service for restoring database from backups"""

    def __init__(self, user):
        """
        Initialize restore service
        :param user: User requesting the restore
        """
        self.user = user
        self.metadata = None

    def restore_from_backup(self, backup_file, clear_existing=False):
        """
        Restore database from backup file
        :param backup_file: UploadedFile object
        :param clear_existing: Whether to clear existing data
        :return: Dictionary with restore results
        """
        # Validate backup file
        BackupFileValidator.validate(backup_file)

        # Extract and parse backup
        data_by_model = self._extract_backup(backup_file)

        # Determine load order based on dependencies
        load_order = self._determine_load_order(data_by_model.keys())

        # Perform restore in transaction
        results = self._perform_restore(data_by_model, load_order, clear_existing)

        return results

    def get_backup_metadata(self, backup_file):
        """
        Extract metadata from backup file without restoring
        :param backup_file: UploadedFile object
        :return: Dictionary with metadata
        """
        BackupFileValidator.validate(backup_file)

        with zipfile.ZipFile(backup_file, "r") as zf:
            metadata_content = zf.read("metadata.json")
            self.metadata = json.loads(metadata_content)

        backup_file.seek(0)
        return self.metadata

    def _extract_backup(self, backup_file):
        """
        Extract and parse backup file
        :param backup_file: UploadedFile object
        :return: Dictionary mapping model labels to data
        """
        data_by_model = {}

        with zipfile.ZipFile(backup_file, "r") as zf:
            # Read metadata
            metadata_content = zf.read("metadata.json")
            self.metadata = json.loads(metadata_content)

            # Read all JSON files
            for file_info in zf.filelist:
                if file_info.filename.endswith(".json") and file_info.filename != "metadata.json":
                    # Extract app_label and model_name from path
                    parts = file_info.filename.split("/")
                    if len(parts) == 2:
                        app_label = parts[0]
                        model_name = parts[1].replace(".json", "")
                        model_label = f"{app_label}.{model_name}"

                        # Read and parse JSON data
                        json_content = zf.read(file_info.filename)
                        data = json.loads(json_content)

                        # Validate data
                        BackupDataValidator.validate_json_data(data)

                        data_by_model[model_label] = data

        return data_by_model

    def _determine_load_order(self, model_labels):
        """
        Determine the order to load models based on dependencies
        Uses topological sort to handle foreign key relationships
        :param model_labels: List of model labels
        :return: Ordered list of model labels
        """
        # Build dependency graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        model_map = {}

        # Get model classes
        for label in model_labels:
            try:
                model = apps.get_model(label)
                model_map[label] = model
                in_degree[label] = 0
            except LookupError:
                continue

        # Build graph based on foreign key relationships
        for label, model in model_map.items():
            for field in model._meta.get_fields():
                if field.many_to_one and field.related_model:
                    related_label = (
                        f"{field.related_model._meta.app_label}."
                        f"{field.related_model._meta.model_name}"
                    )
                    if related_label in model_map and related_label != label:
                        graph[related_label].append(label)
                        in_degree[label] += 1

        # Topological sort using Kahn's algorithm
        queue = deque([label for label in model_labels if in_degree[label] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for circular dependencies
        if len(result) != len(model_labels):
            # If there are circular dependencies, add remaining models
            remaining = set(model_labels) - set(result)
            result.extend(remaining)

        return result

    @transaction.atomic
    def _perform_restore(self, data_by_model, load_order, clear_existing):
        """
        Perform the actual restore operation
        :param data_by_model: Dictionary mapping model labels to data
        :param load_order: Ordered list of model labels
        :param clear_existing: Whether to clear existing data
        :return: Dictionary with restore results
        """
        results = {
            "success": True,
            "models_restored": 0,
            "records_restored": 0,
            "errors": [],
        }

        try:
            # Clear existing data if requested
            if clear_existing:
                self._clear_existing_data(load_order)

            # Restore data in order
            for model_label in load_order:
                if model_label not in data_by_model:
                    continue

                try:
                    model = apps.get_model(model_label)
                    data = data_by_model[model_label]

                    # Deserialize and save objects
                    objects = serializers.deserialize("json", json.dumps(data))

                    count = 0
                    for obj in objects:
                        obj.save()
                        count += 1

                    results["models_restored"] += 1
                    results["records_restored"] += count

                except Exception as e:
                    error_msg = f"Error restoring {model_label}: {str(e)}"
                    results["errors"].append(error_msg)
                    # Continue with other models instead of failing completely
                    continue

        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Restore failed: {str(e)}")
            raise

        return results

    def _clear_existing_data(self, model_labels):
        """
        Clear existing data from models
        :param model_labels: List of model labels to clear
        """
        # Reverse order for deletion (delete children before parents)
        for model_label in reversed(model_labels):
            try:
                model = apps.get_model(model_label)

                # Skip certain models
                if model_label in [
                    "auth.user",
                    "auth.group",
                    "auth.permission",
                    "contenttypes.contenttype",
                ]:
                    continue

                # Delete all objects
                model.objects.all().delete()

            except Exception as e:
                # Log error but continue
                print(f"Error clearing {model_label}: {e}")
                continue


class DependencyResolver:
    """Helper class for resolving model dependencies"""

    @staticmethod
    def get_dependencies(model):
        """
        Get all models that this model depends on
        :param model: Django model class
        :return: List of model classes
        """
        dependencies = []

        for field in model._meta.get_fields():
            if field.many_to_one and field.related_model:
                if field.related_model != model:
                    dependencies.append(field.related_model)

        return dependencies

    @staticmethod
    def build_dependency_graph(models):
        """
        Build a dependency graph for models
        :param models: List of model classes
        :return: Dictionary mapping models to their dependencies
        """
        graph = {}

        for model in models:
            graph[model] = DependencyResolver.get_dependencies(model)

        return graph
