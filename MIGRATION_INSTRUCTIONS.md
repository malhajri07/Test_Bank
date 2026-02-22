# Migration Instructions for Certification Difficulty Level

## Issue
The model references `difficulty_level` in indexes and unique_together before the field exists in the database, causing validation errors during migration.

## Solution
The migrations are set up correctly, but Django validates models before running migrations. Follow these steps:

### Step 1: Ensure PostgreSQL is Running
Make sure your PostgreSQL database server is running and accessible.

### Step 2: Run Migrations
```bash
python manage.py migrate catalog
```

This will:
1. Run migration `0013_add_difficulty_to_certification.py` - Adds the `difficulty_level` field
2. Run migration `0014_update_certification_unique_constraint.py` - Adds the index and updates unique_together

### Step 3: After Migrations Complete
After migrations complete successfully, update the model to restore the full configuration:

1. **Update `catalog/models.py`** - In the `Certification` model's `Meta` class:
   - Change `unique_together` from `[['category', 'slug']]` to `[['category', 'slug', 'difficulty_level']]`
   - Uncomment the index line: `models.Index(fields=['category', 'difficulty_level'])`

The admin interface and other code are already configured correctly and will work once migrations complete.

## What Changed

1. **Certification Model**: Added `difficulty_level` field that allows the same certification name to exist with different difficulty levels under the same category.

2. **Unique Constraint**: Updated from `[['category', 'slug']]` to `[['category', 'slug', 'difficulty_level']]`

3. **Slug Generation**: Slugs now automatically include difficulty level (e.g., `pmp-easy`, `pmp-medium`, `pmp-advanced`)

4. **JSON Import**: When uploading test banks, the certification is created/found based on name, category, AND difficulty level.

## Testing
After migrations complete, you can:
- Create multiple "PMP" certifications under the same category with different difficulty levels
- Upload JSON files with the same certification name but different difficulty levels
- The system will automatically create separate certification entries for each difficulty level
