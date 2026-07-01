# Flask + PostgreSQL Login & Authentication API — Full Tutorial

A beginner-friendly backend project that teaches you how HTTP requests,
Flask, and PostgreSQL fit together by building a real login system.

```
flask-auth-tutorial/
├── app.py                # Flask app: routes (register, login, profile) + CORS
├── database.py            # PostgreSQL connection helper
├── schema.sql              # SQL to create the users table
├── requirements.txt        # Python dependencies
├── .env.example              # Template for your secret config
├── .gitignore                  # Keeps .env, venv, __pycache__ out of git
├── frontend/
│   └── index.html                # Standalone login/signup page (fetch API)
└── README.md                        # You are here
```

---

## 1. Concepts, briefly

**HTTP request/response** — Every time a browser or app talks to a
server, it sends an HTTP *request* (a method like `GET`/`POST`, a URL,
headers, and sometimes a body) and gets back a *response* (a status
code like `200` or `404`, headers, and usually a body). Our API speaks
JSON: the client sends JSON in the request body, and the server
replies with JSON.

**Flask** — A lightweight Python web framework. You define *routes*
(URL + HTTP method) and write a Python function that runs when that
route is hit. Flask handles parsing the request and building the
response for you.

**PostgreSQL** — A relational database. Our Python code doesn't store
data in memory; it sends SQL commands over a connection to Postgres,
which persists the data to disk.

**Password hashing** — We never store passwords as plain text. We
store a one-way hash (`werkzeug.security.generate_password_hash`) so
that even if the database leaked, the real passwords stay unknown.

**JWT (JSON Web Token)** — After a successful login, instead of the
server remembering "this user is logged in" (a session), we hand the
client a signed token. The client includes that token on every future
request (`Authorization: Bearer <token>`), and the server verifies its
signature to know who's asking — no server-side session storage
needed.

**CORS (Cross-Origin Resource Sharing)** — By default, browsers block
JavaScript running on one origin (e.g. a `file://` HTML page or a
frontend on `localhost:3000`) from calling an API on a different
origin (`localhost:5000`), unless the API explicitly allows it. We use
the `Flask-Cors` package to opt in, so our `frontend/index.html` can
actually talk to this API.

---

## 2. Prerequisites

- Python 3.11.9 (or any 3.11+)
- PostgreSQL installed and running locally (or a remote instance)
- `pip` for installing packages
- `curl`, [Postman](https://www.postman.com/), or Thunder Client (VS
  Code extension) to send test requests

---

## 3. Set up PostgreSQL

Create a database (run this once in `psql` or a GUI like pgAdmin):

```sql
CREATE DATABASE auth_demo;
```

Then create the `users` table using the provided schema:

```bash
psql -U postgres -d auth_demo -f schema.sql
```

(Alternatively, `python database.py` will create the table for you —
see step 5.)

---

## 4. Set up the Python project

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# then edit .env with your real DB password and a random SECRET_KEY
```

Generate a strong `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output into `.env` as `SECRET_KEY=...`.

---

## 5. Initialize the database table (if you haven't run schema.sql)

```bash
python database.py
```

You should see: `Database initialized: 'users' table is ready.`

---

## 6. Run the server

```bash
python app.py
```

You should see Flask start on `http://0.0.0.0:5000`. Leave this
terminal running and open a new one for testing.

---

## 7. Test it — full walkthrough

### a) Health check

```bash
curl http://localhost:5000/api/health
```
```json
{"status": "ok", "database": "connected"}
```

### b) Register a new user

```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "supersecret1"}'
```

Response (`201 Created`):
```json
{
  "message": "User created successfully.",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "created_at": "2026-07-01T10:00:00"
  }
}
```

Try it again with the same email → you'll get `409 Conflict`
(`"Username or email is already registered."`). Try a short password →
`400 Bad Request`. This is Flask + PostgreSQL validation working
together.

### c) Log in

```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "supersecret1"}'
```

Response (`200 OK`):
```json
{
  "message": "Login successful.",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in_minutes": 60
}
```

Copy the `token` value — you'll need it next.

### d) Access a protected route

```bash
curl http://localhost:5000/api/profile \
  -H "Authorization: Bearer PASTE_YOUR_TOKEN_HERE"
```

Response (`200 OK`):
```json
{
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "created_at": "2026-07-01T10:00:00"
  }
}
```

Try the same request without the header, or with a garbage token — you
should get `401 Unauthorized`. Wait past `expires_in_minutes` (or set
`JWT_EXP_MINUTES=1` in `.env` to test faster) and you'll get
`"Token has expired."`.

---

## 8. Testing with Postman (instead of curl)

If you prefer a GUI over the command line:

1. **Health check** — New request → `GET` → `http://localhost:5000/api/health` → Send.
2. **Register** — New request → `POST` → `http://localhost:5000/api/register` → **Body** tab → **raw** → dropdown set to **JSON** → paste the same JSON shown above → Send.
3. **Login** — Same as register, but URL is `/api/login` and body only needs `email` + `password`. Copy the `token` from the response.
4. **Profile** — New request → `GET` → `http://localhost:5000/api/profile` → **Authorization** tab → type **Bearer Token** → paste the token → Send.

Tip: save the token into a Postman **environment variable** in the
Login request's *Post-response Script*:
```javascript
const data = pm.response.json();
pm.environment.set("token", data.token);
```
Then set the Profile request's Bearer Token field to `{{token}}` so it
auto-fills every time you re-run Login.

---

## 9. The frontend (`frontend/index.html`)

A single self-contained HTML/CSS/JS page that exercises the whole API:
sign up, sign in, and view your own profile using the JWT the API
returns.

To run it:

1. Make sure the Flask server is running (`python app.py`).
2. Open `frontend/index.html` directly in your browser (double-click
   it, or drag it into a browser tab).
3. Create an account on the **Create account** tab, then sign in.

The `API_BASE` constant near the top of the `<script>` tag
(`http://localhost:5000` by default) controls where the frontend sends
its requests — change it if your server runs somewhere else.

The token is kept only in a JavaScript variable in memory, not
`localStorage`, so it clears on page refresh. That's a deliberate
starting point: `localStorage` is readable by any script on the page,
which is a real risk if you ever load third-party scripts. Persisting
login across refreshes (via `localStorage` or an httpOnly cookie) is a
good next step once you're comfortable with the basics.

---

## 10. Inspecting the database directly with `psql`

Connect to your database:

```bash
psql -U postgres -d auth_demo
```

Then, from the `auth_demo=#` prompt:

```sql
\dt                          -- list all tables
\d users                       -- show the users table's columns/types
SELECT * FROM users;             -- see every row and column
SELECT id, username, email FROM users ORDER BY id;   -- just the essentials
```

`\x` toggles **expanded display**, which is much easier to read when a
column (like `password_hash`) is long — run it once before a `SELECT *`
and again to turn it off.

One-liners that skip the interactive prompt:
```bash
psql -U postgres -d auth_demo -c "SELECT * FROM users;"
psql -U postgres -d auth_demo -x -c "SELECT * FROM users;"   # expanded
```

If everything's working correctly, `password_hash` should show a long
string starting with something like `pbkdf2:sha256:...` — never your
actual plaintext password.

---

## 11. How a request flows through the code (register example)

1. Client sends `POST /api/register` with a JSON body.
2. Flask routes it to the `register()` function in `app.py`.
3. `request.get_json()` parses the JSON body into a Python dict.
4. We validate the fields (length, email format).
5. `generate_password_hash()` hashes the password.
6. `database.get_db_connection()` opens a connection to PostgreSQL.
7. We run an `INSERT ... RETURNING ...` SQL statement with the hashed
   password — never the raw one.
8. PostgreSQL returns the new row; we send it back as JSON with status
   `201`.
9. The connection is closed in the `finally` block, whether or not an
   error occurred.

This request → validate → query database → respond pattern is the
backbone of almost every backend API you'll ever build.

---

## 12. Status codes used in this project

| Code | Meaning | When it happens |
|------|---------|------------------|
| 200  | OK | Successful login, profile fetch, health check |
| 201  | Created | New user registered |
| 400  | Bad Request | Missing/invalid fields |
| 401  | Unauthorized | Wrong password, missing/expired/invalid token |
| 404  | Not Found | Token valid but user was deleted |
| 409  | Conflict | Username/email already exists |
| 500  | Server Error | Unexpected error (DB down, etc.) |

---

## 13. Security notes for going further

- CORS is currently wide open (`origins: "*"`) for easy local
  development. Before deploying, restrict it to your real frontend's
  domain, e.g. `CORS(app, resources={r"/api/*": {"origins": "https://yourapp.com"}})`.

- This demo uses JWTs with no refresh-token or revocation mechanism —
  fine for learning, not production-hardened.
- Add rate limiting (e.g. `Flask-Limiter`) to slow down brute-force
  login attempts.
- Always run behind HTTPS in production so tokens/passwords aren't
  sent in plain text over the network.
- Consider adding email verification and password-reset flows as a
  next exercise.
- Use a production WSGI server (e.g. `gunicorn`) instead of
  `app.run(debug=True)` when deploying.

---

## 14. Pushing this project to GitHub

A `.gitignore` is included so secrets and local clutter never get
committed. It excludes `.env`, `venv/`, `__pycache__/`, and editor/OS
files, while keeping `.env.example` tracked.

```bash
cd flask-auth-tutorial

git init
git add .
git status          # confirm .env is NOT in the list — only .env.example should be
git commit -m "Initial commit: Flask + PostgreSQL auth API with frontend"

git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

If `.env` was ever committed *before* `.gitignore` existed, adding the
ignore rule now won't remove it from history. In that case, rotate
your `SECRET_KEY` and database password rather than relying on the
old ones staying private.

---

## 15. Suggested next exercises

1. Add a `PUT /api/profile` route to let users update their username.
2. Add a `POST /api/logout` that maintains a token blocklist.
3. Add refresh tokens so users don't have to re-login every hour.
4. Containerize with Docker + `docker-compose` (Flask + Postgres).
5. Persist the frontend's login session (e.g. httpOnly cookie) so
   refreshing the page doesn't sign the user out.
6. Restrict CORS to a specific origin instead of `"*"` once you have
   a real frontend deployment.