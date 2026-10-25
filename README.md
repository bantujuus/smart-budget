# 🚀 SmartBudget

SmartBudget is a modern, full-stack financial management and budgeting application designed to help users track income, monitor expenses, and manage financial goals with ease.

## 🛠️ Tech Stack

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Lucide Icons, Axios
- **Backend:** Django, Django REST Framework (DRF), PostgreSQL
- **Database / Infrastructure:** Docker & PostgreSQL (Port `5433`)

---

## 📂 Project Structure

```text
smart-budget/
├── backend/            # Django REST Framework API
│   ├── config/         # Django settings & URLs
│   ├── core/           # Custom User model, views & auth
│   └── manage.py       # Django management script
├── frontend/           # React + Vite + Tailwind client
│   ├── src/
│   │   ├── api/        # Axios API service modules
│   │   ├── components/ # Reusable UI components
│   │   ├── views/      # Dashboard, Transactions, Budgets
│   │   └── App.tsx     # Main router & layout
│   └── package.json
└── docker-compose.yml  # PostgreSQL database container configuration

```

---

## ⚙️ Getting Started

### Prerequisites

Make sure you have the following installed on your system:

* **Python** (v3.10+)
* **Node.js** (v18+) & `npm`
* **Docker** & **Docker Compose**

---

### 1. Database Setup (Docker)

Start the PostgreSQL database container in the background:

```bash
docker compose up -d

```

* **Database Name:** `smart_budget`
* **User:** `postgres`
* **Password:** `postgrespassword`
* **Port Mapping:** `5433` (Host) -> `5432` (Container)

---

### 2. Backend Setup (Django)

1. Navigate to the backend directory and create/activate a virtual environment:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

```


2. Install Python dependencies:
```bash
pip install -r requirements.txt
# Or install core packages if requirements.txt is pending:
pip install django djangorestframework psycopg2-binary django-cors-headers

```


3. Run database migrations:
```bash
python3 manage.py makemigrations
python3 manage.py migrate

```


4. Create a superuser (for admin access):
```bash
python3 manage.py createsuperuser

```


5. Start the Django development server:
```bash
python3 manage.py runserver

```


* The backend API will be available at **`http://127.0.0.1:8000/api/v1/`**



---

### 3. Frontend Setup (React + Vite)

1. Open a new terminal window and navigate to the frontend directory:
```bash
cd frontend

```


2. Install dependencies:
```bash
npm install

```


3. Start the Vite development server:
```bash
npm run dev

```


* The frontend client will be available at **`http://localhost:5173`** (Vite proxies API requests to backend port `8000`).



---

## 🔑 API Endpoints Overview

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/auth/login/` | `POST` | Authenticate user & return Auth Token |
| `/api/v1/auth/register/` | `POST` | Register a new user account |
| `/api/v1/categories/` | `GET / POST` | List or create transaction categories |
| `/api/v1/transactions/` | `GET / POST` | Manage user transactions |
| `/api/v1/reports/summary/` | `GET` | Get dashboard cash flow totals |

