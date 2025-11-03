import sqlite3
import os
import json

# Define the path to your data directory and SQLite database file
# This assumes migrate_db.py is in the root IT_Requisition_App/ folder
current_script_dir = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(current_script_dir, 'backend', 'data')
DATABASE_FILE = os.path.join(DATA_DIR, 'requisitions.db')

def get_db_connection():
    """Establishes and returns a SQLite database connection."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def run_migrations():
    """
    Performs database migrations:
    1. Adds 'display_id' column to 'requisitions' table if it doesn't exist.
    2. Ensures 'counters' table exists and 'requisition_seq' is initialized.
    3. Populates 'display_id' for existing records that are NULL, assigning sequential IDs.
    4. Updates the 'requisition_seq' counter to reflect the highest assigned display_id.
    """
    # Ensure the data directory exists before trying to connect
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created data directory: {DATA_DIR}")
        # If the directory was just created, the DB will be new, so no migration needed beyond initial setup
        print("Data directory was just created. Database will be initialized on first app run. No explicit migration needed now.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("Starting database migration...")

        # --- 1. Add display_id column to requisitions table if it doesn't exist ---
        # Check if requisitions table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='requisitions'")
        if cursor.fetchone(): # If requisitions table exists
            cursor.execute("PRAGMA table_info(requisitions)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'display_id' not in columns:
                print("Adding 'display_id' column to 'requisitions' table...")
                cursor.execute("ALTER TABLE requisitions ADD COLUMN display_id TEXT")
                print("'display_id' column added.")
            else:
                print("'display_id' column already exists in 'requisitions' table.")
        else:
            print("'requisitions' table does not exist. It will be created on app startup.")


        # --- 2. Create counters table if it doesn't exist and initialize counter ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS counters (
                name TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            )
        ''')
        print("'counters' table ensured.")

        cursor.execute("INSERT OR IGNORE INTO counters (name, value) VALUES ('requisition_seq', 0)")
        conn.commit() # Commit the initial counter value
        print("'requisition_seq' counter ensured and initialized if new.")

        # --- 3. Populate display_id for existing records that are NULL ---
        # Get the current highest sequence number for new records
        cursor.execute("SELECT value FROM counters WHERE name = 'requisition_seq'")
        current_seq_value = cursor.fetchone()['value']
        next_seq_to_assign = current_seq_value + 1

        print("Checking for existing requisitions without 'display_id'...")
        # Select records where display_id is NULL, ordered by their creation timestamp (first changelog entry)
        # This assumes changelog is always present and its first entry's timestamp is reliable for ordering.
        cursor.execute("SELECT id, changelog FROM requisitions WHERE display_id IS NULL ORDER BY json_extract(changelog, '$[0].timestamp') ASC")
        records_to_update = cursor.fetchall()

        if records_to_update:
            print(f"Found {len(records_to_update)} existing requisitions without 'display_id'. Populating...")
            for record in records_to_update:
                req_id = record['id']
                # Generate new display_id
                new_display_id = f"RQ{next_seq_to_assign:03d}"
                
                cursor.execute("UPDATE requisitions SET display_id = ? WHERE id = ?", (new_display_id, req_id))
                print(f"  - Assigned display_id '{new_display_id}' to requisition '{req_id}'")
                next_seq_to_assign += 1
            
            # Update the main counter to reflect the highest assigned value
            cursor.execute("UPDATE counters SET value = ? WHERE name = 'requisition_seq'", (next_seq_to_assign - 1,))
            conn.commit()
            print("Finished populating 'display_id' for existing records and updated sequence counter.")
        else:
            print("No existing requisitions found without 'display_id' or already populated.")

        print("Database migration completed successfully!")

    except sqlite3.Error as e:
        print(f"SQLite error during migration: {e}")
        conn.rollback() # Rollback changes if an error occurs
    except Exception as e:
        print(f"An unexpected error occurred during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    run_migrations()
