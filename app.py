from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = "skfashion_secret_key"

init_db()


def is_logged_in():
    return "user_id" in session


def is_admin():
    return session.get("role") == "admin"


@app.context_processor
def inject_nav_categories():
    db = get_db()
    categories = db.execute("SELECT * FROM categories").fetchall()
    db.close()
    return dict(nav_categories=categories)


@app.route("/")
def index():
    db = get_db()
    products = db.execute("SELECT * FROM products").fetchall()
    db.close()
    return render_template("index.html", products=products)


@app.route("/category/<int:category_id>")
def category(category_id):
    db = get_db()
    products = db.execute("SELECT * FROM products WHERE category_id = ?", (category_id,)).fetchall()
    db.close()
    return render_template("index.html", products=products)


@app.route("/search")
def search():
    keyword = request.args.get("q", "")
    db = get_db()
    products = db.execute(
        "SELECT * FROM products WHERE name LIKE ?", ("%" + keyword + "%",)
    ).fetchall()
    db.close()
    return render_template("index.html", products=products)


# ---------- USER MODULE ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        existing = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("Email already registered. Please login.")
            db.close()
            return redirect(url_for("login"))

        hashed_password = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, hashed_password, "customer"),
        )
        db.commit()
        db.close()
        flash("Registration successful. Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            flash("Logged in successfully.")
            if user["role"] == "admin":
                return redirect(url_for("admin"))
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("index"))


@app.route("/profile")
def profile():
    if not is_logged_in():
        return redirect(url_for("login"))
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    db.close()
    return render_template("profile.html", user=user)


# ---------- PRODUCT MODULE ----------

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    reviews = db.execute(
        "SELECT feedback.*, users.name FROM feedback JOIN users ON feedback.user_id = users.id WHERE product_id = ?",
        (product_id,),
    ).fetchall()
    db.close()
    return render_template("product_detail.html", product=product, reviews=reviews)


@app.route("/product/<int:product_id>/feedback", methods=["POST"])
def add_feedback(product_id):
    if not is_logged_in():
        return redirect(url_for("login"))
    rating = request.form["rating"]
    comment = request.form["comment"]
    db = get_db()
    db.execute(
        "INSERT INTO feedback (product_id, user_id, rating, comment) VALUES (?, ?, ?, ?)",
        (product_id, session["user_id"], rating, comment),
    )
    db.commit()
    db.close()
    flash("Thank you for your feedback.")
    return redirect(url_for("product_detail", product_id=product_id))


# ---------- SHOPPING CART MODULE ----------

@app.route("/cart")
def cart():
    if not is_logged_in():
        return redirect(url_for("login"))
    db = get_db()
    items = db.execute(
        "SELECT cart.id as cart_id, products.*, cart.quantity FROM cart "
        "JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?",
        (session["user_id"],),
    ).fetchall()
    db.close()
    total = sum(item["price"] * item["quantity"] for item in items)
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    if not is_logged_in():
        return redirect(url_for("login"))
    quantity = int(request.form.get("quantity", 1))

    db = get_db()
    existing = db.execute(
        "SELECT * FROM cart WHERE user_id = ? AND product_id = ?",
        (session["user_id"], product_id),
    ).fetchone()

    if existing:
        db.execute(
            "UPDATE cart SET quantity = quantity + ? WHERE id = ?",
            (quantity, existing["id"]),
        )
    else:
        db.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
            (session["user_id"], product_id, quantity),
        )
    db.commit()
    db.close()
    flash("Product added to cart.")
    return redirect(url_for("cart"))


@app.route("/cart/update/<int:cart_id>", methods=["POST"])
def update_cart(cart_id):
    quantity = int(request.form.get("quantity", 1))
    db = get_db()
    db.execute("UPDATE cart SET quantity = ? WHERE id = ?", (quantity, cart_id))
    db.commit()
    db.close()
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:cart_id>")
def remove_from_cart(cart_id):
    db = get_db()
    db.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
    db.commit()
    db.close()
    return redirect(url_for("cart"))


# ---------- ORDER MODULE ----------

@app.route("/checkout", methods=["POST"])
def checkout():
    if not is_logged_in():
        return redirect(url_for("login"))

    db = get_db()
    items = db.execute(
        "SELECT cart.*, products.price, products.stock FROM cart "
        "JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?",
        (session["user_id"],),
    ).fetchall()

    if not items:
        flash("Your cart is empty.")
        db.close()
        return redirect(url_for("cart"))

    total = sum(item["price"] * item["quantity"] for item in items)
    order_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    cur = db.execute(
        "INSERT INTO orders (user_id, order_date, total, status) VALUES (?, ?, ?, ?)",
        (session["user_id"], order_date, total, "Placed"),
    )
    order_id = cur.lastrowid

    for item in items:
        db.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
            (order_id, item["product_id"], item["quantity"], item["price"]),
        )
        db.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (item["quantity"], item["product_id"]),
        )

    db.execute("DELETE FROM cart WHERE user_id = ?", (session["user_id"],))
    db.commit()
    db.close()

    flash("Order placed successfully.")
    return redirect(url_for("orders"))


@app.route("/orders")
def orders():
    if not is_logged_in():
        return redirect(url_for("login"))
    db = get_db()
    user_orders = db.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (session["user_id"],)
    ).fetchall()
    db.close()
    return render_template("orders.html", orders=user_orders)


@app.route("/orders/<int:order_id>")
def order_detail(order_id):
    if not is_logged_in():
        return redirect(url_for("login"))
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    items = db.execute(
        "SELECT order_items.*, products.name FROM order_items "
        "JOIN products ON order_items.product_id = products.id WHERE order_id = ?",
        (order_id,),
    ).fetchall()
    db.close()
    return render_template("order_detail.html", order=order, items=items)


# ---------- ADMIN MODULE ----------

@app.route("/admin")
def admin():
    if not is_admin():
        return redirect(url_for("login"))
    db = get_db()
    products = db.execute("SELECT * FROM products").fetchall()
    customers = db.execute("SELECT * FROM users WHERE role = 'customer'").fetchall()
    all_orders = db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    db.close()
    return render_template("admin.html", products=products, customers=customers, orders=all_orders)


@app.route("/admin/product/add", methods=["GET", "POST"])
def admin_add_product():
    if not is_admin():
        return redirect(url_for("login"))

    db = get_db()
    if request.method == "POST":
        name = request.form["name"]
        category_id = request.form["category_id"]
        price = request.form["price"]
        description = request.form["description"]
        stock = request.form["stock"]
        image = request.form.get("image") or "https://images.pexels.com/photos/19852754/pexels-photo-19852754.jpeg?auto=compress&cs=tinysrgb&w=600"

        db.execute(
            "INSERT INTO products (name, category_id, price, description, image, stock) VALUES (?, ?, ?, ?, ?, ?)",
            (name, category_id, price, description, image, stock),
        )
        db.commit()
        db.close()
        flash("Product added successfully.")
        return redirect(url_for("admin"))

    categories = db.execute("SELECT * FROM categories").fetchall()
    db.close()
    return render_template("admin_add_product.html", categories=categories)


@app.route("/admin/product/edit/<int:product_id>", methods=["GET", "POST"])
def admin_edit_product(product_id):
    if not is_admin():
        return redirect(url_for("login"))

    db = get_db()
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        stock = request.form["stock"]
        description = request.form["description"]

        db.execute(
            "UPDATE products SET name = ?, price = ?, stock = ?, description = ? WHERE id = ?",
            (name, price, stock, description, product_id),
        )
        db.commit()
        db.close()
        flash("Product updated successfully.")
        return redirect(url_for("admin"))

    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    db.close()
    return render_template("admin_edit_product.html", product=product)


@app.route("/admin/product/delete/<int:product_id>")
def admin_delete_product(product_id):
    if not is_admin():
        return redirect(url_for("login"))
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    db.close()
    flash("Product deleted.")
    return redirect(url_for("admin"))


@app.route("/admin/order/status/<int:order_id>", methods=["POST"])
def admin_update_order_status(order_id):
    if not is_admin():
        return redirect(url_for("login"))
    status = request.form["status"]
    db = get_db()
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    db.commit()
    db.close()
    flash("Order status updated.")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)
