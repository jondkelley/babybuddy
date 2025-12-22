# -*- coding: utf-8 -*-
import json
import zipfile
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class BackupFileValidator:
    """Validates uploaded backup files"""

    MAX_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = [".zip"]
    REQUIRED_FILES = ["metadata.json"]

    @classmethod
    def validate(cls, file):
        """
        Validate backup file
        :param file: UploadedFile object
        :raises ValidationError: If validation fails
        """
        # Check file size
        if file.size > cls.MAX_SIZE:
            raise ValidationError(
                _("File too large. Maximum size is %(max_size)s MB.")
                % {"max_size": cls.MAX_SIZE // (1024 * 1024)}
            )

        # Check extension
        if not any(file.name.endswith(ext) for ext in cls.ALLOWED_EXTENSIONS):
            raise ValidationError(_("Invalid file type. Please upload a ZIP file."))

        # Check ZIP integrity
        try:
            with zipfile.ZipFile(file, "r") as zf:
                # Test ZIP integrity
                if zf.testzip() is not None:
                    raise ValidationError(_("Corrupted ZIP file."))

                # Check for required files
                namelist = zf.namelist()
                for required_file in cls.REQUIRED_FILES:
                    if required_file not in namelist:
                        raise ValidationError(
                            _("Invalid backup file. Missing %(file)s.")
                            % {"file": required_file}
                        )

                # Check for malicious paths
                for name in namelist:
                    if name.startswith("/") or ".." in name:
                        raise ValidationError(
                            _("Invalid file paths detected in backup.")
                        )

                # Validate metadata
                try:
                    metadata_content = zf.read("metadata.json")
                    metadata = json.loads(metadata_content)

                    # Check required metadata fields
                    required_fields = ["version", "timestamp", "database_engine"]
                    for field in required_fields:
                        if field not in metadata:
                            raise ValidationError(
                                _("Invalid metadata. Missing %(field)s.")
                                % {"field": field}
                            )

                except json.JSONDecodeError:
                    raise ValidationError(_("Invalid metadata format."))

        except zipfile.BadZipFile:
            raise ValidationError(_("Invalid ZIP file."))
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(_("Error validating backup file: %(error)s") % {"error": str(e)})

        # Reset file pointer
        file.seek(0)


class BackupDataValidator:
    """Validates backup data integrity"""

    @staticmethod
    def validate_json_data(data):
        """
        Validate JSON data structure
        :param data: Parsed JSON data
        :raises ValidationError: If validation fails
        """
        if not isinstance(data, list):
            raise ValidationError(_("Invalid data format. Expected a list."))

        for item in data:
            if not isinstance(item, dict):
                raise ValidationError(_("Invalid data format. Expected objects."))

            # Check for required fields
            if "model" not in item:
                raise ValidationError(_("Invalid data format. Missing model field."))

            if "fields" not in item:
                raise ValidationError(_("Invalid data format. Missing fields."))
