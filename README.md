# IT Requisition System (PES)

A self-hosted, internal web application built to manage IT, Conference Room, and Leave requisitions for Pakistan Engineering Services (PES). This app provides a simple user interface for submissions and dedicated, password-protected portals for IT and Manager approval.

## ✨ Features

* **Three Requisition Types:** Users can submit requests for IT issues, Conference Room bookings, and personal Leave.
* **User & Admin Portals:**
    * **IT Portal:** Allows the IT department to view, verify, and manage IT and Conference Room requests.
    * **Manager Portal:** Allows management to approve or decline Leave requests and final-approve IT/CR requests.
* **Request History & Tracking:** All requisitions are tracked with a status (e.g., "Pending", "Approved", "Completed") and a full history is searchable.
* **Sequential IDs:** Generates user-friendly, sequential request IDs (e.g., `RQ001`, `RQ002`) for easy reference.
* **Lightweight Database:** Uses SQLite for simple, file-based data storage.

## 🛠️ Technologies Used

* **Backend:** Python, Flask
* **Database:** SQLite
* **Frontend:** HTML, CSS, Vanilla JavaScript
* **Styling:** Tailwind CSS (via CDN)

## 🚀 How to Run Locally

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/IT_Requisition_App.git](https://github.com/your-username/IT_Requisition_App.git)
    cd IT_Requisition_App
    ```

2.  **Install backend dependencies:**
    ```bash
    # It's recommended to use a virtual environment
    python -m venv .venv
    source .venv/bin/activate 
    
    # Install from requirements.txt
    pip install -r backend/requirements.txt
    ```

3.  **Initialize the database:**
    The app includes a migration script to set up the database schema.
    ```bash
    python migrate_db.py
    ```

4.  **Run the backend server:**
    This will start the Flask API server (usually on port 5000).
    ```bash
    python backend/app.py
    ```

5.  **Run the frontend server:**
    In a **new terminal window**, navigate to the project's root directory and use Python's built-in HTTP server to serve the `index.html` file.
    ```bash
    # This will serve the frontend on port 8000
    python -m http.server 8000
    ```

6.  **Access the app:**
    Open your browser and go to `http://localhost:8000`.