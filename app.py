"""
app.py
------
A minimal but complete Flask + PostgreSQL authentication API.

Endpoints:
    POST /api/register   -> create a new user
    POST /api/login       -> verify credentials, return a JWT token
    GET  /api/profile     -> protected route, requires a valid token
    GET  /api/health      -> simple check that the server + DB are alive

Run it with:
    python app.py

This file is intentionally written with lots of comments so it can
double as a tutorial. Read top to bottom.
"""

import os
import re
import jwt
import datetime
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2 import errors as pg_errors
from dotenv import load_dotenv

from database import get_db_connection

load_dotenv()

app = Flask(__name__)

# CORS lets a frontend running on a different origin (e.g. opening
# frontend/index.html as a file://, or a dev server on localhost:3000/5173)
# actually call this API. Without this, the browser blocks the request
# before it even reaches Flask, and fetch() throws a generic
# "Failed to fetch" / "could not reach" error in the console.
#
# For local development we allow any origin. In production, restrict
# this to your real frontend's domain, e.g.:
#   CORS(app, resources={r"/api/*": {"origins": "https://yourapp.com"}})
CORS(app, resources={r"/api/*": {"origins": "*"}})

# SECRET_KEY is used to *sign* JWT tokens so we can trust they weren't
# tampered with. Never hardcode this in real projects -- keep it in .env.
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --------------------------------------------------------------------------
# Helper: decorator that protects a route by requiring a valid JWT
# --------------------------------------------------------------------------
def token_required(f):
    """
    A decorator we can put on any route to say "you need to be logged in
    to access this". It looks for a header like:

        Authorization: Bearer <token>

    and decodes it. If the token is missing, expired, or invalid, we
    reject the request with a 401 Unauthorized before the real route
    function ever runs.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header. Expected 'Bearer <token>'."}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 401

        # Make the logged-in user's id available to the route function
        request.user_id = payload["user_id"]
        return f(*args, **kwargs)

    return decorated


# --------------------------------------------------------------------------
# Route: health check
# --------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health():
    """Quick way to confirm the API and database are reachable."""
    try:
        conn = get_db_connection()
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    return jsonify({"status": "ok", "database": db_status}), 200


# --------------------------------------------------------------------------
# Route: register a new user
# --------------------------------------------------------------------------
@app.route("/api/register", methods=["POST"])
def register():
    """
    Expects JSON body:
        { "username": "bob", "email": "bob@example.com", "password": "secret123" }

    Steps:
      1. Validate input.
      2. Hash the password (NEVER store plain text passwords).
      3. Insert the new user into PostgreSQL.
      4. Return the created user (without the password hash).
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # --- validation ---
    if not username or len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters."}), 400
    if not EMAIL_REGEX.match(email):
        return jsonify({"error": "A valid email is required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    # Hash the password. This turns "secret123" into something like
    # "pbkdf2:sha256:600000$...$..." which cannot practically be reversed.
    password_hash = generate_password_hash(password)

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id, username, email, created_at;
            """,
            (username, email, password_hash),
        )
        new_user = cur.fetchone()
        conn.commit()
        cur.close()
        return jsonify({"message": "User created successfully.", "user": new_user}), 201

    except pg_errors.UniqueViolation:
        # Raised if username or email already exists (from the UNIQUE constraint)
        if conn:
            conn.rollback()
        return jsonify({"error": "Username or email is already registered."}), 409

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": "Something went wrong.", "details": str(e)}), 500

    finally:
        if conn:
            conn.close()


# --------------------------------------------------------------------------
# Route: log in
# --------------------------------------------------------------------------
@app.route("/api/login", methods=["POST"])
def login():
    """
    Expects JSON body:
        { "email": "bob@example.com", "password": "secret123" }

    Steps:
      1. Look up the user by email.
      2. Compare the submitted password against the stored hash.
      3. If it matches, issue a signed JWT the client will send on
         future requests to prove who they are.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, password_hash FROM users WHERE email = %s;",
            (email,),
        )
        user = cur.fetchone()
        cur.close()

        # Same generic error whether the email doesn't exist or the
        # password is wrong -- this avoids telling attackers which
        # emails are registered ("user enumeration").
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid email or password."}), 401

        # Build the JWT payload. "exp" makes the token expire automatically.
        payload = {
            "user_id": user["id"],
            "username": user["username"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXP_MINUTES),
            "iat": datetime.datetime.utcnow(),
        }
        token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

        return jsonify({
            "message": "Login successful.",
            "token": token,
            "expires_in_minutes": JWT_EXP_MINUTES,
        }), 200

    except Exception as e:
        return jsonify({"error": "Something went wrong.", "details": str(e)}), 500

    finally:
        if conn:
            conn.close()


# --------------------------------------------------------------------------
# Route: protected profile page (requires a valid token)
# --------------------------------------------------------------------------
@app.route("/api/profile", methods=["GET"])
@token_required
def profile():
    """
    A protected route. The @token_required decorator already verified
    the JWT before this code runs, and set request.user_id for us.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = %s;",
            (request.user_id,),
        )
        user = cur.fetchone()
        cur.close()

        if not user:
            return jsonify({"error": "User no longer exists."}), 404

        return jsonify({"user": user}), 200

    except Exception as e:
        return jsonify({"error": "Something went wrong.", "details": str(e)}), 500

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # debug=True auto-reloads the server when you edit code -- turn it
    # off in production.
    app.run(debug=True, host="0.0.0.0", port=5000)