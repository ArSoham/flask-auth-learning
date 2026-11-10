# Flask + PostgreSQL Authentication API

A small backend learning project built with Flask and PostgreSQL to understand how user authentication works in a REST API.

The project implements user registration, password hashing, login, JWT-based authentication, and protected routes.

## What I Learned

- Building REST API endpoints with Flask.
- Handling HTTP requests and JSON responses.
- Connecting Python applications to PostgreSQL.
- Creating and querying database records using SQL.
- Hashing and verifying passwords.
- Generating and validating JWT tokens.
- Protecting API routes using authentication middleware.
- Connecting a frontend to a backend using `fetch()`.

## Tech Stack

- **Backend:** Python, Flask
- **Database:** PostgreSQL
- **Authentication:** JWT (PyJWT)
- **Security:** Werkzeug password hashing
- **Frontend:** HTML, CSS, JavaScript
- **Other:** Flask-CORS, psycopg2, python-dotenv

## Project Structure

```text
flask-postgres-jwt-auth/
├── app.py
├── database.py
├── requirements.txt
├── .gitignore
└── frontend/
    └── index.html
```

## Features

- User registration with input validation.
- Secure password hashing instead of storing plaintext passwords.
- Login using email and password.
- JWT generation after successful authentication.
- Protected profile endpoint.
- Token expiration and validation.
- PostgreSQL database integration.
- Simple frontend for testing authentication flows.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/flask-postgres-jwt-auth.git
cd flask-postgres-jwt-auth
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a database:

```sql
CREATE DATABASE auth_demo;
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=auth_demo
DB_USER=postgres
DB_PASSWORD=your_database_password

SECRET_KEY=your_secret_key
JWT_EXP_MINUTES=60
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 6. Initialize the database

```bash
python database.py
```

### 7. Start the Flask server

```bash
python app.py
```

The API will run at:

`http://localhost:5000`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check API and database status |
| POST | `/api/register` | Register a new user |
| POST | `/api/login` | Authenticate and receive a JWT |
| GET | `/api/profile` | Access the authenticated user's profile |

### Authentication Flow

1. A user registers with a username, email, and password.
2. The backend validates the input and hashes the password.
3. User information is stored in PostgreSQL.
4. The user logs in using their credentials.
5. The backend verifies the password and generates a JWT.
6. The client sends the token in the `Authorization` header.
7. The backend validates the token before granting access to protected routes.

Example:

```http
Authorization: Bearer <your_jwt_token>
```

## Frontend

A simple HTML, CSS, and JavaScript interface is included in `frontend/`.

It allows users to register, log in, view their profile, and sign out while interacting with the Flask API.

Open `frontend/index.html` in a browser while the Flask server is running.

## Learning Goals / Next Steps

- Add automated API tests using pytest.
- Implement logout with token revocation.
- Explore refresh tokens.
- Improve input validation and error handling.
- Restrict CORS to trusted origins.
- Containerize the application using Docker.
- Separate routes, authentication logic, and database operations into modules.

---

**Note:** This project is intended for learning backend development and authentication fundamentals. It is not a production-ready authentication service.
