# Backup & Restore Usage Guide

## Overview

The Baby Buddy backup and restore system allows you to create complete backups of your database and restore them when needed. This feature is available to staff users only.

## Accessing the Feature

1. Log in as a staff user
2. Click on your username in the top navigation
3. Select "Backup & Restore" from the dropdown menu
4. Or navigate directly to: `/backup/`

## Creating a Backup

### Steps:

1. Navigate to the Backup & Restore page
2. Click the "Download Backup" button in the "Create Backup" section
3. Your browser will download a ZIP file named `backup_MMDDYY_HHMMSS.zip`
   - The filename uses your timezone settings
   - Example: `backup_122023_143022.zip` (December 20, 2023 at 2:30:22 PM)

### What's Included:

- All database records (children, feedings, sleep, diaper changes, etc.)
- User accounts and settings
- Tags and notes
- All timestamps and relationships
- Metadata about the backup

### What's NOT Included:

- Uploaded media files (photos, images)
- Session data
- Cache data
- Migration history

## Restoring from a Backup

### Steps:

1. Navigate to the Backup & Restore page
2. In the "Restore from Backup" section:
   - Click "Choose File" and select your backup ZIP file
   - Optionally check "Clear existing data before restore" if you want to replace all data
   - Click "Upload and Preview"
3. Review the backup information on the confirmation page:
   - Backup version
   - Creation date and time
   - Number of models and records
   - Database engine used
4. Click "Confirm Restore" to proceed or "Cancel" to abort

### Important Notes:

⚠️ **Warning**: Restoring a backup may overwrite existing data!

- **With "Clear existing data" checked**: All current data will be deleted before restoring
- **Without "Clear existing data" checked**: Records with matching IDs will be overwritten

- Always create a current backup before restoring
- The restore process is atomic - if any error occurs, no changes will be made
- You cannot undo a restore operation

## Best Practices

### Regular Backups

- Create backups before major changes
- Schedule regular backups (weekly or monthly)
- Store backups in multiple locations
- Test your backups periodically

### Backup Storage

- Keep backups in a secure location
- Consider cloud storage (Dropbox, Google Drive, etc.)
- Maintain multiple backup versions
- Label backups with descriptive names

### Before Restoring

1. Create a current backup first
2. Verify the backup file is not corrupted
3. Check the backup metadata matches your expectations
4. Ensure you have enough disk space
5. Consider the impact on active users

## Technical Details

### File Format

Backups are ZIP files containing:
```
backup_MMDDYY_HHMMSS.zip
├── metadata.json          # Backup information
├── auth/
│   ├── user.json
│   └── group.json
├── core/
│   ├── child.json
│   ├── feeding.json
│   ├── sleep.json
│   └── ...
└── babybuddy/
    ├── settings.json
    └── tag.json
```

### Compatibility

- Backups are compatible across different database types:
  - SQLite → PostgreSQL ✓
  - PostgreSQL → MySQL ✓
  - MySQL → SQLite ✓
- Backups from different Baby Buddy versions may have compatibility issues
- Always check the "Baby Buddy Version" in the backup metadata

### Filename Format

Format: `backup_MMDDYY_HHMMSS.zip`

- `MM`: Month (01-12)
- `DD`: Day (01-31)
- `YY`: Year (last 2 digits)
- `HH`: Hour (00-23)
- `MM`: Minute (00-59)
- `SS`: Second (00-59)

The timestamp uses your user timezone setting.

## Troubleshooting

### Backup Creation Fails

**Problem**: Error message when downloading backup

**Solutions**:
- Check disk space on the server
- Verify database connectivity
- Check server logs for detailed errors
- Try again after a few minutes

### Restore Fails

**Problem**: Error message during restore

**Solutions**:
- Verify the backup file is not corrupted
- Check the backup file size (max 100MB)
- Ensure the backup is a valid ZIP file
- Check for version compatibility
- Review error messages for specific issues

### File Too Large

**Problem**: "File too large" error when uploading

**Solutions**:
- Current limit is 100MB
- Contact administrator to increase limit
- Consider selective data cleanup before backup

### Version Mismatch

**Problem**: Backup from different Baby Buddy version

**Solutions**:
- Check compatibility notes
- Update Baby Buddy to matching version
- Contact support for migration assistance

## Security Considerations

### Access Control

- Only staff users can create/restore backups
- Backups contain sensitive data
- Protect backup files appropriately
- Use secure transfer methods

### Data Privacy

- Backups contain all user data
- Follow data protection regulations
- Encrypt backups if storing externally
- Delete old backups securely

## API Access

For automated backups, you can use the API:

### Download Backup
```bash
curl -X GET \
  -H "Authorization: Token YOUR_API_TOKEN" \
  -o backup.zip \
  https://your-babybuddy-instance.com/backup/download/
```

### Upload Restore (requires form data)
```bash
curl -X POST \
  -H "Authorization: Token YOUR_API_TOKEN" \
  -F "backup_file=@backup.zip" \
  -F "clear_existing_data=false" \
  https://your-babybuddy-instance.com/backup/restore/confirm/
```

## Support

For issues or questions:
1. Check the error messages
2. Review server logs
3. Consult the main documentation
4. Open an issue on GitHub
5. Contact the Baby Buddy community

## Changelog

### Version 1.0
- Initial implementation
- Support for all database types
- Timezone-aware filenames
- Atomic restore operations
- Validation and error handling
