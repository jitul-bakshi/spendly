import os
import sqlite3
from functools import wraps
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]

with app.app_context():
    init_db()
    seed_db()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ------------------------------------------------------------------ #
# Public routes                                                        #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not name:
        flash("Name is required.", "error")
        return render_template("register.html")
    if not email:
        flash("Email is required.", "error")
        return render_template("register.html")
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return render_template("register.html")

    password_hash = generate_password_hash(password)
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        session["user_id"] = user_id
    except sqlite3.IntegrityError:
        flash("An account with that email already exists.", "error")
        return render_template("register.html")
    except Exception as e:
        app.logger.error(e)
        flash("Something went wrong. Please try again.", "error")
        return render_template("register.html")
    finally:
        conn.close()

    flash(f"Welcome to Spendly, {name.split()[0]}!", "success")
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Email and password are required.", "error")
        return render_template("login.html")

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        flash("Invalid email or password.", "error")
        return render_template("login.html")

    session["user_id"] = user["id"]
    flash(f"Welcome back, {user['name'].split()[0]}!", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been signed out.", "success")
    return redirect(url_for("landing"))


# ------------------------------------------------------------------ #
# Authenticated routes                                                 #
# ------------------------------------------------------------------ #

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    try:
        expenses = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC",
            (session["user_id"],)
        ).fetchall()
        user = conn.execute(
            "SELECT name FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
    finally:
        conn.close()

    current_month = date.today().strftime("%Y-%m")
    month_expenses = [e for e in expenses if e["date"].startswith(current_month)]
    month_total = sum(e["amount"] for e in month_expenses)

    cat_totals = {}
    for e in month_expenses:
        cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]

    top_cat = max(cat_totals, key=cat_totals.get) if cat_totals else None

    return render_template("dashboard.html",
        expenses=expenses,
        user=user,
        month_total=month_total,
        month_count=len(month_expenses),
        top_cat=top_cat,
    )


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    today = date.today().isoformat()

    if request.method == "GET":
        return render_template("add_expense.html", categories=CATEGORIES, today=today)

    amount_str = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    expense_date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()
    form_data = {"amount": amount_str, "category": category, "date": expense_date, "description": description}

    if not amount_str:
        flash("Amount is required.", "error")
        return render_template("add_expense.html", categories=CATEGORIES, today=today, form_data=form_data)
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Amount must be a positive number.", "error")
        return render_template("add_expense.html", categories=CATEGORIES, today=today, form_data=form_data)
    if category not in CATEGORIES:
        flash("Please select a valid category.", "error")
        return render_template("add_expense.html", categories=CATEGORIES, today=today, form_data=form_data)
    if not expense_date:
        flash("Date is required.", "error")
        return render_template("add_expense.html", categories=CATEGORIES, today=today, form_data=form_data)

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], amount, category, expense_date, description or None),
        )
        conn.commit()
    except Exception as e:
        app.logger.error(e)
        flash("Could not save expense. Please try again.", "error")
        return render_template("add_expense.html", categories=CATEGORIES, today=today, form_data=form_data)
    finally:
        conn.close()

    flash("Expense added.", "success")
    return redirect(url_for("dashboard"))


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    conn = get_db()
    try:
        expense = conn.execute(
            "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
            (id, session["user_id"])
        ).fetchone()
    finally:
        conn.close()

    if not expense:
        flash("Expense not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "GET":
        return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)

    amount_str = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    expense_date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    if not amount_str:
        flash("Amount is required.", "error")
        return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Amount must be a positive number.", "error")
        return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)
    if category not in CATEGORIES:
        flash("Please select a valid category.", "error")
        return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)
    if not expense_date:
        flash("Date is required.", "error")
        return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)

    conn = get_db()
    try:
        conn.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND user_id = ?",
            (amount, category, expense_date, description or None, id, session["user_id"]),
        )
        conn.commit()
    except Exception as e:
        app.logger.error(e)
        flash("Could not update expense. Please try again.", "error")
        return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)
    finally:
        conn.close()

    flash("Expense updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/expenses/<int:id>/delete", methods=["POST"])
@login_required
def delete_expense(id):
    conn = get_db()
    try:
        result = conn.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (id, session["user_id"]),
        )
        conn.commit()
        if result.rowcount == 0:
            flash("Expense not found.", "error")
        else:
            flash("Expense deleted.", "success")
    except Exception as e:
        app.logger.error(e)
        flash("Could not delete expense. Please try again.", "error")
    finally:
        conn.close()

    return redirect(url_for("dashboard"))


@app.route("/profile")
@login_required
def profile():
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
        stats = conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM expenses WHERE user_id = ?",
            (session["user_id"],)
        ).fetchone()
        top_cat = conn.execute(
            "SELECT category FROM expenses WHERE user_id = ? GROUP BY category ORDER BY COUNT(*) DESC LIMIT 1",
            (session["user_id"],)
        ).fetchone()
    finally:
        conn.close()

    return render_template("profile.html", user=user, stats=stats, top_cat=top_cat)


# ------------------------------------------------------------------ #
# Static pages                                                         #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001)
