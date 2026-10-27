import sqlite3

DB_NAME = "fashion.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER,
            price REAL NOT NULL,
            description TEXT,
            image TEXT,
            stock INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Placed',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        categories = ["Men", "Women", "Footwear", "Accessories"]
        for c in categories:
            cur.execute("INSERT INTO categories (name) VALUES (?)", (c,))
        conn.commit()

        # real photos from Pexels (free to use, no attribution required)
        def img(photo_id):
            return f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=600"

        men = [
            ("Men Casual Shirt", 1, 799.0, "Cotton casual shirt for everyday wear", img(9759713), 50),
            ("Men Formal Shirt", 1, 899.0, "Slim fit formal shirt for office wear", img(4443831), 45),
            ("Denim Jacket", 1, 1299.0, "Blue denim jacket with button closure", img(33780926), 25),
            ("Men Polo T-Shirt", 1, 599.0, "Breathable cotton polo t-shirt", img(34233605), 60),
            ("Men Hoodie", 1, 999.0, "Warm fleece hoodie for winters", img(11872747), 35),
            ("Men Blazer", 1, 2499.0, "Slim fit blazer for formal occasions", img(12911511), 20),
            ("Cargo Pants", 1, 1099.0, "Multi-pocket cargo pants", img(37897864), 40),
            ("Men Jeans", 1, 1199.0, "Slim fit stretchable denim jeans", img(19895835), 55),
            ("Men Sweater", 1, 899.0, "Woolen pullover sweater", img(34150926), 30),
            ("Men Track Suit", 1, 1499.0, "Comfortable track suit for workouts", img(32527429), 28),
        ]

        women = [
            ("Women Kurti", 2, 599.0, "Printed cotton kurti for daily wear", img(36311379), 40),
            ("Women Saree", 2, 1799.0, "Elegant silk saree with border work", img(7920188), 20),
            ("Women Dress", 2, 1299.0, "Floral summer dress", img(38374231), 35),
            ("Women Top", 2, 549.0, "Casual sleeveless top", img(30809730), 45),
            ("Palazzo Pants", 2, 699.0, "Flowy palazzo pants", img(14027977), 38),
            ("Women Leggings", 2, 399.0, "Stretchable cotton leggings", img(13178920), 60),
            ("Women Skirt", 2, 749.0, "A-line casual skirt", img(36567501), 30),
            ("Women Blouse", 2, 649.0, "Designer blouse for ethnic wear", img(28213774), 25),
            ("Ethnic Suit Set", 2, 1599.0, "Anarkali ethnic suit set", img(35521738), 22),
            ("Women Jumpsuit", 2, 1399.0, "Trendy party wear jumpsuit", img(14027903), 18),
        ]

        footwear = [
            ("Running Shoes", 3, 1499.0, "Lightweight running shoes with mesh upper", img(1027130), 30),
            ("Casual Sneakers", 3, 1299.0, "Everyday casual sneakers", img(13536939), 40),
            ("Formal Shoes", 3, 1799.0, "Leather formal shoes for office wear", img(12210270), 25),
            ("Women Sandals", 3, 699.0, "Comfortable flat sandals", img(23692992), 35),
            ("Men Loafers", 3, 1399.0, "Slip-on loafers for men", img(17695225), 28),
            ("Flip Flops", 3, 299.0, "Everyday rubber flip flops", img(4996974), 60),
            ("Ankle Boots", 3, 1999.0, "Stylish ankle length boots", img(27658707), 20),
            ("Women Heels", 3, 1299.0, "Party wear block heels", img(27063075), 24),
            ("Sports Shoes", 3, 1599.0, "All purpose sports shoes", img(2529148), 32),
            ("Home Slippers", 3, 349.0, "Soft indoor slippers", img(31451024), 50),
        ]

        accessories = [
            ("Leather Wallet", 4, 399.0, "Genuine leather wallet with card slots", img(27467366), 60),
            ("Women Handbag", 4, 899.0, "Stylish handbag for daily use", img(39873977), 35),
            ("Sunglasses", 4, 599.0, "UV protection stylish sunglasses", img(36557821), 45),
            ("Analog Watch", 4, 1499.0, "Classic analog wrist watch", img(13155693), 30),
            ("Leather Belt", 4, 349.0, "Formal leather belt", img(7679471), 50),
            ("Baseball Cap", 4, 299.0, "Cotton adjustable baseball cap", img(32477146), 55),
            ("Winter Scarf", 4, 349.0, "Warm knitted scarf", img(2986445), 40),
            ("Fashion Necklace", 4, 499.0, "Trendy statement necklace", img(29486063), 33),
            ("Earrings Set", 4, 349.0, "Traditional earrings set", img(38180246), 42),
            ("Travel Backpack", 4, 1299.0, "Durable travel and college backpack", img(9595291), 27),
        ]

        all_products = men + women + footwear + accessories
        cur.executemany(
            "INSERT INTO products (name, category_id, price, description, image, stock) VALUES (?, ?, ?, ?, ?, ?)",
            all_products,
        )
        conn.commit()

    cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cur.fetchone()[0] == 0:
        from werkzeug.security import generate_password_hash
        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ("Admin", "admin@skfashion.com", generate_password_hash("admin123"), "admin"),
        )
        conn.commit()

    conn.close()
