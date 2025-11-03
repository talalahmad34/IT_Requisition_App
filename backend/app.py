# app.py - SQLite Integration with Sequential Display IDs
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Define the path to your data directory and SQLite database file
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DATABASE_FILE = os.path.join(DATA_DIR, 'requisitions.db')

# Ensure the data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"Created data directory: {DATA_DIR}")

def get_db_connection():
    """Establishes and returns a SQLite database connection."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def initialize_db():
    """Initializes the database schema (creates tables if they don't exist).
       Includes 'display_id' for requisitions and a 'counters' table."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create requisitions table
    # Added 'display_id TEXT' column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requisitions (
            id TEXT PRIMARY KEY,
            requisitionType TEXT NOT NULL,
            userName TEXT NOT NULL,
            userDesignation TEXT NOT NULL,
            userPhone TEXT,
            issueType TEXT,
            problemDescription TEXT,
            meetingDate TEXT,
            meetingTime TEXT,
            meetingDescription TEXT,
            numParticipants INTEGER,
            leaveType TEXT,
            startDate TEXT,
            endDate TEXT,
            reason TEXT,
            status TEXT NOT NULL,
            managerApprovalStatus TEXT, -- Specific for Leave requests
            changelog TEXT NOT NULL,
            display_id TEXT UNIQUE -- New column for sequential display ID
        )
    ''')

    # Create counters table for sequential IDs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS counters (
            name TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        )
    ''')

    # Initialize the requisition sequence counter if it doesn't exist
    cursor.execute("INSERT OR IGNORE INTO counters (name, value) VALUES ('requisition_seq', 0)")

    conn.commit()
    conn.close()
    print("Database initialized or schema updated.")

# Initialize the database when the app starts
initialize_db()

def get_next_requisition_sequence():
    """Fetches and increments the global requisition sequence counter."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT value FROM counters WHERE name = 'requisition_seq'")
        current_value = cursor.fetchone()['value']
        next_value = current_value + 1
        cursor.execute("UPDATE counters SET value = ? WHERE name = 'requisition_seq'", (next_value,))
        conn.commit()
        # Format as RQ followed by a 3-digit padded number (e.g., RQ001, RQ010, RQ100)
        return f"RQ{next_value:03d}"
    except Exception as e:
        print(f"Error getting/updating requisition sequence: {e}")
        return None # Indicate failure
    finally:
        conn.close()

@app.route('/api/requisitions', methods=['GET'])
def get_all_requisitions():
    """API endpoint to get all requisitions."""
    print("GET /api/requisitions request received.")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Select all columns, including the new display_id
        cursor.execute("SELECT id, requisitionType, userName, userDesignation, userPhone, issueType, problemDescription, meetingDate, meetingTime, meetingDescription, numParticipants, leaveType, startDate, endDate, reason, status, managerApprovalStatus, changelog, display_id FROM requisitions")
        requisitions = cursor.fetchall()
        requisitions_list = []
        for req in requisitions:
            req_dict = dict(req)
            # Ensure changelog is parsed from JSON string back to list
            req_dict['changelog'] = json.loads(req_dict['changelog'])
            requisitions_list.append(req_dict)
        print(f"Fetched {len(requisitions_list)} requisitions.")
        return jsonify(requisitions_list), 200
    except Exception as e:
        print(f"Error fetching requisitions from DB: {e}")
        return jsonify({"error": f"Failed to fetch requisitions: {e}"}), 500
    finally:
        conn.close()

@app.route('/api/requisitions', methods=['POST'])
def add_requisition():
    """API endpoint to add a new requisition."""
    new_req_data = request.json
    print(f"POST /api/requisitions request received with data: {new_req_data}")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Generate the sequential display ID
        display_id = get_next_requisition_sequence()
        if display_id is None:
            raise Exception("Failed to generate sequential display ID.")

        new_req_data['display_id'] = display_id # Add display_id to the data

        # Ensure changelog is a JSON string before inserting
        new_req_data['changelog'] = json.dumps(new_req_data.get('changelog', []))

        # Prepare data for insertion, handling optional fields with default NULL
        cursor.execute('''
            INSERT INTO requisitions (
                id, requisitionType, userName, userDesignation, userPhone, issueType,
                problemDescription, meetingDate, meetingTime, meetingDescription,
                numParticipants, leaveType, startDate, endDate, reason, status,
                managerApprovalStatus, changelog, display_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_req_data['id'],
            new_req_data['requisitionType'],
            new_req_data['userName'],
            new_req_data['userDesignation'],
            new_req_data.get('userPhone'),
            new_req_data.get('issueType'),
            new_req_data.get('problemDescription'),
            new_req_data.get('meetingDate'),
            new_req_data.get('meetingTime'),
            new_req_data.get('meetingDescription'),
            new_req_data.get('numParticipants'),
            new_req_data.get('leaveType'),
            new_req_data.get('startDate'),
            new_req_data.get('endDate'),
            new_req_data.get('reason'),
            new_req_data['status'],
            new_req_data.get('managerApprovalStatus'),
            new_req_data['changelog'],
            new_req_data['display_id'] # Insert the new display_id
        ))
        conn.commit()

        # Fetch the newly added requisition to return it with all fields
        cursor.execute("SELECT id, requisitionType, userName, userDesignation, userPhone, issueType, problemDescription, meetingDate, meetingTime, meetingDescription, numParticipants, leaveType, startDate, endDate, reason, status, managerApprovalStatus, changelog, display_id FROM requisitions WHERE id = ?", (new_req_data['id'],))
        added_req = cursor.fetchone()
        added_req_dict = dict(added_req)
        added_req_dict['changelog'] = json.loads(added_req_dict['changelog']) # Parse changelog back for response

        print(f"Added new requisition to DB: {added_req_dict['id']} with display_id: {added_req_dict['display_id']}")
        return jsonify(added_req_dict), 201
    except Exception as e:
        print(f"Error adding requisition to DB: {e}")
        return jsonify({"error": f"Failed to add requisition: {e}"}), 500
    finally:
        conn.close()

@app.route('/api/requisitions/<string:req_id>', methods=['PUT'])
def update_requisition(req_id):
    """API endpoint to update an existing requisition by ID."""
    updated_data = request.json
    print(f"PUT /api/requisitions/{req_id} request received with data: {updated_data}")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Ensure changelog is a JSON string for storage
        updated_data['changelog'] = json.dumps(updated_data.get('changelog', []))

        # Update all relevant fields. display_id is not updated here as it's set on creation.
        cursor.execute('''
            UPDATE requisitions SET
                requisitionType = ?,
                userName = ?,
                userDesignation = ?,
                userPhone = ?,
                issueType = ?,
                problemDescription = ?,
                meetingDate = ?,
                meetingTime = ?,
                meetingDescription = ?,
                numParticipants = ?,
                leaveType = ?,
                startDate = ?,
                endDate = ?,
                reason = ?,
                status = ?,
                managerApprovalStatus = ?,
                changelog = ?
            WHERE id = ?
        ''', (
            updated_data['requisitionType'],
            updated_data['userName'],
            updated_data['userDesignation'],
            updated_data.get('userPhone'),
            updated_data.get('issueType'),
            updated_data.get('problemDescription'),
            updated_data.get('meetingDate'),
            updated_data.get('meetingTime'),
            updated_data.get('meetingDescription'),
            updated_data.get('numParticipants'),
            updated_data.get('leaveType'),
            updated_data.get('startDate'),
            updated_data.get('endDate'),
            updated_data.get('reason'),
            updated_data['status'],
            updated_data.get('managerApprovalStatus'),
            updated_data['changelog'],
            req_id
        ))
        conn.commit()

        if cursor.rowcount == 0:
            print(f"Error: Requisition with ID {req_id} not found for PUT request.")
            return jsonify({"error": "Requisition not found"}), 404

        print(f"Updated requisition in DB: {req_id}")
        return jsonify(updated_data), 200
    except Exception as e:
        print(f"Error updating requisition in DB: {e}")
        return jsonify({"error": f"Failed to update requisition: {e}"}), 500
    finally:
        conn.close()

@app.route('/api/requisitions/<string:req_id>', methods=['DELETE'])
def delete_requisition(req_id):
    """API endpoint to delete a requisition by ID."""
    print(f"DELETE /api/requisitions/{req_id} request received.")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Deleting from requisitions table will automatically delete related changelogs due to ON DELETE CASCADE
        cursor.execute("DELETE FROM requisitions WHERE id = ?", (req_id,))
        conn.commit()

        if cursor.rowcount == 0:
            print(f"Error: Requisition with ID {req_id} not found for DELETE request.")
            return jsonify({"error": "Requisition not found"}), 404
        
        print(f"Deleted requisition from DB: {req_id}")
        return jsonify({"message": f"Requisition {req_id} deleted successfully"}), 200
    except Exception as e:
        print(f"Error deleting requisition from DB: {e}")
        return jsonify({"error": f"Failed to delete requisition: {e}"}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # This block is typically run when app.py is executed directly.
    # For deployment with `python -m http.server` and Flask's built-in server,
    # you might not need `app.run()` here if `start_it_app.bat` handles it.
    # However, it's good practice for local testing.
    app.run(debug=True, host='0.0.0.0', port=5000)
