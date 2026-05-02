import streamlit as st
import mysql.connector
from datetime import date
import matplotlib.pyplot as plt

st.set_page_config(page_title="ERP PRO", layout="wide")

# ---------- STYLE ----------
st.markdown("""
<style>
.big {font-size:40px;font-weight:bold;color:#4CAF50;}
.card {background:#f8f9fa;padding:15px;border-radius:10px;margin:10px 0;}
</style>
""", unsafe_allow_html=True)

# ---------- DB ----------
def connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root123",
        database="erp_final"
    )

def run(q, p=None, fetch=False):
    conn = connect()
    cur = conn.cursor()
    cur.execute(q, p or ())
    data = cur.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return data

# ---------- SESSION ----------
if "login" not in st.session_state:
    st.session_state.login = False

# ---------- LOGIN / SIGNUP ----------
if not st.session_state.login:

    st.markdown("<p class='big'>🏢 ERP PRO SYSTEM</p>", unsafe_allow_html=True)

    mode = st.radio("Select", ["Login","Signup"])

    if mode == "Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            res = run("SELECT * FROM users WHERE username=%s AND password=%s",(u,p),True)
            if res:
                st.session_state.login = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Invalid Login")

    else:
        st.subheader("Signup")

        name = st.text_input("Name")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        mobile = st.text_input("Mobile")

        if st.button("Signup"):
            try:
                run("INSERT INTO users(name,username,password,role,mobile) VALUES(%s,%s,%s,'staff',%s)",
                    (name,username,password,mobile))
                st.success("Account Created ✅")
            except:
                st.error("Username exists")

# ---------- MAIN ----------
else:

    st.sidebar.write(f"👤 {st.session_state.user}")

    menu = st.sidebar.radio("Menu",
        ["Dashboard","Products","Customers","Orders","Reports","Logout"]
    )

    if menu == "Logout":
        st.session_state.clear()
        st.rerun()

    # ---------- DASHBOARD ----------
    if menu == "Dashboard":
        st.markdown("<p class='big'>📊 Dashboard</p>", unsafe_allow_html=True)

        p = run("SELECT COUNT(*) FROM products", fetch=True)[0][0]
        c = run("SELECT COUNT(*) FROM customers", fetch=True)[0][0]
        o = run("SELECT COUNT(*) FROM orders", fetch=True)[0][0]

        col1,col2,col3 = st.columns(3)
        col1.metric("Products", p)
        col2.metric("Customers", c)
        col3.metric("Orders", o)

    # ---------- PRODUCTS ----------
    if menu == "Products":
        st.title("📦 Products")

        name = st.text_input("Name")
        price = st.number_input("Selling Price")
        cost = st.number_input("Cost Price")
        stock = st.number_input("Stock")

        if st.button("Add Product"):
            try:
                run("INSERT INTO products(name,price,cost,stock) VALUES(%s,%s,%s,%s)",
                    (name,price,cost,stock))
                st.success("Added")
            except:
                st.error("Duplicate Product")

        data = run("SELECT * FROM products", fetch=True)

        st.subheader("Edit / Delete")

        ids = [d[0] for d in data]
        if ids:
            pid = st.selectbox("Select Product", ids)
            prod = [d for d in data if d[0]==pid][0]

            new_name = st.text_input("Edit Name", prod[1])
            new_price = st.number_input("Edit Price", float(prod[2]))
            new_cost = st.number_input("Edit Cost", float(prod[3]))
            new_stock = st.number_input("Edit Stock", int(prod[4]))

            col1,col2 = st.columns(2)

            if col1.button("Update"):
                run("UPDATE products SET name=%s,price=%s,cost=%s,stock=%s WHERE id=%s",
                    (new_name,new_price,new_cost,new_stock,pid))
                st.success("Updated")
                st.rerun()

            if col2.button("Delete"):
                run("DELETE FROM products WHERE id=%s",(pid,))
                st.warning("Deleted")
                st.rerun()

        st.table(data)

    # ---------- CUSTOMERS ----------
    if menu == "Customers":
        st.title("👥 Customers")

        name = st.text_input("Customer Name")
        mobile = st.text_input("Mobile")

        if st.button("Add Customer"):
            run("INSERT INTO customers(name,mobile) VALUES(%s,%s)",(name,mobile))
            st.success("Added")

        data = run("SELECT * FROM customers", fetch=True)

        ids = [d[0] for d in data]
        if ids:
            cid = st.selectbox("Select Customer", ids)
            cust = [d for d in data if d[0]==cid][0]

            new_name = st.text_input("Edit Name", cust[1])
            new_mobile = st.text_input("Edit Mobile", cust[2])

            col1,col2 = st.columns(2)

            if col1.button("Update Customer"):
                run("UPDATE customers SET name=%s,mobile=%s WHERE id=%s",
                    (new_name,new_mobile,cid))
                st.success("Updated")
                st.rerun()

            if col2.button("Delete Customer"):
                run("DELETE FROM customers WHERE id=%s",(cid,))
                st.warning("Deleted")
                st.rerun()

        st.table(data)

    # ---------- ORDERS ----------
    if menu == "Orders":
        st.title("🛒 Orders")

        customers = run("SELECT id,name FROM customers", fetch=True)
        products = run("SELECT id,name,price,cost FROM products", fetch=True)

        c_dict = {c[1]:c[0] for c in customers}
        p_dict = {p[1]:p for p in products}

        customer = st.selectbox("Customer", list(c_dict.keys()))
        product = st.selectbox("Product", list(p_dict.keys()))
        qty = st.number_input("Quantity", min_value=1)

        price = p_dict[product][2]
        cost = p_dict[product][3]

        total = price * qty
        profit = (price - cost) * qty

        st.write(f"💰 Total: ₹{total}")
        st.write(f"📈 Profit: ₹{profit}")

        if st.button("Place Order"):
            run("INSERT INTO orders(customer_id,total,profit,date) VALUES(%s,%s,%s,%s)",
                (c_dict[customer], total, profit, date.today()))

            oid = run("SELECT MAX(id) FROM orders", fetch=True)[0][0]

            run("INSERT INTO order_details(order_id,product_id,quantity,price,cost) VALUES(%s,%s,%s,%s,%s)",
                (oid,p_dict[product][0],qty,price,cost))

            run("UPDATE products SET stock=stock-%s WHERE id=%s",
                (qty,p_dict[product][0]))

            st.success("Order Placed")

        st.table(run("SELECT * FROM orders", fetch=True))

    # ---------- REPORTS ----------
    if menu == "Reports":
        st.title("📈 Reports")

        data = run("SELECT date,total FROM orders", fetch=True)

        if data:
            dates = [str(d[0]) for d in data]
            totals = [float(d[1]) for d in data]

            plt.figure()
            plt.plot(dates, totals, marker='o')
            plt.xticks(rotation=45)
            st.pyplot(plt)

        profit = run("SELECT SUM(profit) FROM orders", fetch=True)[0][0]
        st.success(f"Total Profit: ₹{profit if profit else 0}")