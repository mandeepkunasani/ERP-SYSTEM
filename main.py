import streamlit as st
import mysql.connector
from datetime import date
import matplotlib.pyplot as plt

st.set_page_config(page_title="E-Court Pro", layout="wide")

# ---------- STYLE ----------
st.markdown("""
<style>
.main-title {font-size:40px; font-weight:bold; color:#2E86C1;}
.card {padding:15px; border-radius:10px; background:#f2f2f2; margin:10px;}
</style>
""", unsafe_allow_html=True)

# ---------- DB ----------
def connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root123",
        database="ecourt_final"
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

# ---------- LOGIN ----------
if not st.session_state.login:

    st.markdown('<p class="main-title">⚖️ E-Court System</p>', unsafe_allow_html=True)

    mode = st.radio("Select", ["Login","Signup"])

    if mode == "Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            res = run("SELECT * FROM users WHERE username=%s AND password=%s",(u,p),True)
            if res:
                st.session_state.login = True
                st.session_state.user = u
                st.session_state.role = res[0][4]
                st.rerun()
            else:
                st.error("Invalid Login")

    else:
        name = st.text_input("Name")
        username = st.text_input("Username")
        password = st.text_input("Password")
        role = st.selectbox("Role",["admin","lawyer"])

        if st.button("Signup"):
            run("INSERT INTO users(name,username,password,role) VALUES(%s,%s,%s,%s)",
                (name,username,password,role))
            st.success("Created")

# ---------- MAIN ----------
else:

    st.sidebar.write(f"👤 {st.session_state.user}")

    menu = st.sidebar.radio("Menu",
        ["Dashboard","Lawyers","Judges","Cases","Hearings","Verdicts","Reports","Logout"]
    )

    if menu == "Logout":
        st.session_state.clear()
        st.rerun()

    # ---------- DASHBOARD ----------
    if menu == "Dashboard":
        st.markdown('<p class="main-title">📊 Dashboard</p>', unsafe_allow_html=True)

        total = run("SELECT COUNT(*) FROM cases", fetch=True)[0][0]
        closed = run("SELECT COUNT(*) FROM cases WHERE status='Closed'", fetch=True)[0][0]
        pending = run("SELECT COUNT(*) FROM cases WHERE status='Pending'", fetch=True)[0][0]

        c1,c2,c3 = st.columns(3)
        c1.metric("Total Cases", total)
        c2.metric("Closed Cases", closed)
        c3.metric("Pending Cases", pending)

    # ---------- LAWYERS ----------
    if menu == "Lawyers":
        st.title("👨‍⚖️ Lawyers")

        name = st.text_input("Name")
        phone = st.text_input("Phone")
        email = st.text_input("Email")

        if st.button("Add Lawyer"):
            run("INSERT INTO lawyers(name,phone,email) VALUES(%s,%s,%s)",
                (name,phone,email))
            st.success("Added")

        data = run("SELECT * FROM lawyers", fetch=True)
        st.table(data)

        ids = [d[0] for d in data]
        if ids:
            lid = st.selectbox("Select Lawyer", ids)
            if st.button("Delete Lawyer"):
                run("DELETE FROM lawyers WHERE id=%s",(lid,))
                st.rerun()

    # ---------- JUDGES ----------
    if menu == "Judges":
        st.title("👨‍⚖️ Judges")

        name = st.text_input("Judge Name")
        court = st.text_input("Court No")

        if st.button("Add Judge"):
            run("INSERT INTO judges(name,court_no) VALUES(%s,%s)",
                (name,court))
            st.success("Added")

        data = run("SELECT * FROM judges", fetch=True)
        st.table(data)

    # ---------- CASES ----------
    if menu == "Cases":
        st.title("📂 Cases")

        lawyers = run("SELECT id,name FROM lawyers", fetch=True)
        judges = run("SELECT id,name FROM judges", fetch=True)

        lmap = {x[1]:x[0] for x in lawyers}
        jmap = {x[1]:x[0] for x in judges}

        case_type = st.selectbox("Case Type",["Civil","Criminal"])
        lawyer = st.selectbox("Lawyer", list(lmap.keys()))
        judge = st.selectbox("Judge", list(jmap.keys()))
        status = st.selectbox("Status",["Pending","Ongoing","Closed"])

        if st.button("Create Case"):
            run("""
            INSERT INTO cases(case_type,filing_date,status,lawyer_id,judge_id)
            VALUES(%s,%s,%s,%s,%s)
            """,(case_type,date.today(),status,lmap[lawyer],jmap[judge]))
            st.success("Created")

        data = run("SELECT * FROM cases", fetch=True)
        st.table(data)

        ids = [d[0] for d in data]
        if ids:
            cid = st.selectbox("Edit Case", ids)
            new_status = st.selectbox("Update Status",["Pending","Ongoing","Closed"])

            if st.button("Update Case"):
                run("UPDATE cases SET status=%s WHERE id=%s",(new_status,cid))
                st.success("Updated")

            if st.button("Delete Case"):
                run("DELETE FROM cases WHERE id=%s",(cid,))
                st.warning("Deleted")

    # ---------- HEARINGS ----------
    if menu == "Hearings":
        st.title("📅 Hearings")

        cases = run("SELECT id FROM cases", fetch=True)
        cid = st.selectbox("Case", [c[0] for c in cases])

        d = st.date_input("Date")
        t = st.time_input("Time")

        if st.button("Add Hearing"):
            run("""
            INSERT INTO hearings(case_id,hearing_date,hearing_time,status)
            VALUES(%s,%s,%s,'Scheduled')
            """,(cid,str(d),str(t)))
            st.success("Added")

        st.table(run("SELECT * FROM hearings", fetch=True))

    # ---------- VERDICTS ----------
    if menu == "Verdicts":
        st.title("⚖️ Verdicts")

        cases = run("SELECT id FROM cases", fetch=True)
        cid = st.selectbox("Case", [c[0] for c in cases])

        decision = st.text_area("Decision")

        if st.button("Add Verdict"):
            run("""
            INSERT INTO verdicts(case_id,verdict_date,decision)
            VALUES(%s,%s,%s)
            """,(cid,date.today(),decision))

            run("UPDATE cases SET status='Closed' WHERE id=%s",(cid,))
            st.success("Verdict Added")

        st.table(run("SELECT * FROM verdicts", fetch=True))

    # ---------- REPORTS ----------
    if menu == "Reports":
        st.title("📈 Reports")

        data = run("SELECT filing_date FROM cases", fetch=True)

        if data:
            dates = [str(d[0]) for d in data]

            plt.figure()
            plt.plot(dates)
            plt.xticks(rotation=45)
            st.pyplot(plt)

        st.table(run("SELECT * FROM cases", fetch=True))