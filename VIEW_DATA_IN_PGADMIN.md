# Viewing Data in pgAdmin

## Current Database Status

Your `catalog_certification` table **DOES contain data**:
- **Total Records**: 3 certifications
- **Table Structure**: Correctly created with `difficulty_level` field

## How to View Data in pgAdmin

### Method 1: View All Rows

1. In pgAdmin, navigate to:
   ```
   Servers → Test Bank Local → Databases → testbank_db → Schemas → public → Tables → catalog_certification
   ```

2. Right-click on `catalog_certification`

3. Select **"View/Edit Data" → "All Rows"**

4. You should see 3 rows with columns:
   - `id`
   - `name`
   - `slug`
   - `description`
   - `order`
   - `created_at`
   - `updated_at`
   - `category_id`
   - `difficulty_level` ← **New field!**

### Method 2: Query Tool

1. Right-click on `catalog_certification`
2. Select **"Query Tool"**
3. Run this query:
   ```sql
   SELECT * FROM catalog_certification;
   ```
4. Click the **Execute** button (▶) or press F5

### Method 3: First 100 Rows

1. Right-click on `catalog_certification`
2. Select **"View/Edit Data" → "First 100 Rows"**

## Troubleshooting: If You Still Don't See Data

### 1. Refresh the Table
- Right-click on `catalog_certification` → **"Refresh"**

### 2. Check You're in the Right Database
- Make sure you're looking at `testbank_db` (not `postgres` or another database)
- The path should be: `Servers → [Your Server] → Databases → testbank_db`

### 3. Check for Filters
- In the "View/Edit Data" window, check if any filters are applied
- Clear any filters and refresh

### 4. Verify Connection
- Make sure pgAdmin is connected to `localhost:5432`
- Check the server status (should be green/connected)

### 5. Check Table Permissions
- Right-click on `catalog_certification` → **"Properties"**
- Go to **"Security"** tab
- Make sure your user has SELECT permissions

## Verify Data via Command Line

You can also verify the data exists using psql:

```bash
psql -U mohammedalhajri -h localhost -p 5432 -d testbank_db -c "SELECT * FROM catalog_certification;"
```

Or using Django shell:

```bash
python manage.py shell
```

Then in the shell:
```python
from catalog.models import Certification
print(Certification.objects.count())  # Should show 3
for c in Certification.objects.all():
    print(f"{c.id}: {c.name} ({c.difficulty_level})")
```

## Expected Data Structure

Your certifications should have:
- `id`: Primary key
- `name`: Certification name (e.g., "PMP", "CompTIA Security+")
- `slug`: URL-friendly version
- `difficulty_level`: "easy", "medium", or "advanced" ← **This is the new field**
- `category_id`: Foreign key to `catalog_category`
- Other standard fields (description, order, timestamps)

## If Table Appears Empty in pgAdmin

1. **Try the Query Tool method** (Method 2 above) - this bypasses any view filters
2. **Check if you're looking at the right schema** - should be `public` schema
3. **Verify the table name** - should be `catalog_certification` (with underscore, not hyphen)
4. **Check pgAdmin version** - older versions might have display issues
