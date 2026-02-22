# pgAdmin Connection Guide

## Database Information

Your database exists and is accessible:
- **Database Name**: `testbank_db`
- **Database User**: `mohammedalhajri`
- **Database Password**: (empty/blank)
- **Host**: `localhost` or `127.0.0.1`
- **Port**: `5432`

## Connecting pgAdmin to Your Database

### Step 1: Add PostgreSQL Server in pgAdmin

1. Open pgAdmin
2. Right-click on **"Servers"** in the left panel
3. Select **"Create" → "Server..."**

### Step 2: Configure Server Connection

In the **"General"** tab:
- **Name**: `Test Bank Local` (or any name you prefer)

In the **"Connection"** tab:
- **Host name/address**: `localhost` or `127.0.0.1`
- **Port**: `5432`
- **Maintenance database**: `postgres` (default)
- **Username**: `mohammedalhajri`
- **Password**: Leave blank (or enter if you have one set)

### Step 3: Save and Connect

1. Click **"Save"** or **"Save Password"**
2. The server should appear in the left panel
3. Expand the server to see databases
4. You should see `testbank_db` listed

### Step 4: Refresh if Needed

If you don't see `testbank_db`:
1. Right-click on the server name
2. Select **"Refresh"**
3. The database should appear

## Troubleshooting

### If you still don't see the database:

1. **Check PostgreSQL is running**:
   ```bash
   pg_isready -h localhost -p 5432
   ```

2. **Verify database exists**:
   ```bash
   psql -U mohammedalhajri -h localhost -p 5432 -l | grep testbank_db
   ```

3. **Check pgAdmin connection**:
   - Make sure you're connecting to `localhost:5432`
   - Verify the username matches: `mohammedalhajri`
   - Try connecting with password blank first

4. **Check PostgreSQL version**:
   - Your PostgreSQL version: 14.19 (Homebrew)
   - Make sure pgAdmin supports PostgreSQL 14

### Alternative: Connect via psql Command Line

You can also access the database directly via command line:
```bash
psql -U mohammedalhajri -h localhost -p 5432 -d testbank_db
```

## Database Tables

Your database contains the following catalog tables:
- `catalog_category`
- `catalog_certification`
- `catalog_testbank`
- `catalog_question`
- `catalog_answeroption`
- And other Django/app tables

You can verify tables exist by running:
```bash
psql -U mohammedalhajri -h localhost -p 5432 -d testbank_db -c "\dt catalog_*"
```
