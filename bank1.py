from flask import Flask, request, jsonify, send_file
import sqlite3, os

app = Flask(__name__)
DB = "bank.db"

# Database banao - 1 baar
def init_db():
    con = sqlite3.connect(DB)
    con.execute('''CREATE TABLE IF NOT EXISTS accounts
    (acc_no TEXT PRIMARY KEY, name TEXT, father TEXT, dob TEXT, gender TEXT,
    mobile TEXT, email TEXT, aadhar TEXT, pan TEXT, address TEXT,
    type TEXT, nominee TEXT, balance REAL, pin TEXT)''')
    con.execute('''CREATE TABLE IF NOT EXISTS txns
    (id INTEGER PRIMARY KEY AUTOINCREMENT, acc_no TEXT, type TEXT, amount REAL, date TEXT)''')
    con.commit(); con.close()

init_db()

@app.route('/')
def home():
    return send_file('bankindex1.html')

@app.route('/api/create', methods=['POST'])
def create():
    d = request.json
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM accounts")
    acc_no = str(101 + cur.fetchone()[0])
    try:
        cur.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (acc_no, d['name'], d['father'], d['dob'], d['gender'], d['mobile'], d['email'], d['aadhar'], d['pan'], d['address'], d['type'], d['nominee'], d['bal'], d['pin']))
        cur.execute("INSERT INTO txns (acc_no,type,amount,date) VALUES (?,?,?,datetime('now','localtime'))",(acc_no,'Opening',d['bal']))
        con.commit()
        return jsonify({"success":True,"acc_no":acc_no})
    except Exception as e:
        return jsonify({"success":False,"error":str(e)})
    finally:
        con.close()

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM accounts WHERE acc_no=? AND pin=?",(d['acc'],d['pin']))
    row = cur.fetchone()
    if not row: return jsonify({"success":False})
    acc = dict(row)
    cur.execute("SELECT * FROM txns WHERE acc_no=? ORDER BY id DESC",(d['acc'],))
    acc['txns']=[dict(r) for r in cur.fetchall()]
    # Aadhar secure - sirf last 4 dikhao
    acc['aadhar_masked']="XXXX-XXXX-"+acc['aadhar'][-4:]
    con.close()
    return jsonify({"success":True,"data":acc})

@app.route('/api/transaction', methods=['POST'])
def txn():
    d = request.json
    con = sqlite3.connect(DB); cur=con.cursor()
    cur.execute("SELECT balance FROM accounts WHERE acc_no=?",(d['acc'],))
    bal = cur.fetchone()[0]
    if d['type']=='Withdraw' and d['amt']>bal:
        return jsonify({"success":False,"msg":"Insufficient"})
    new_bal = bal + d['amt'] if d['type']=='Deposit' else bal - d['amt']
    cur.execute("UPDATE accounts SET balance=? WHERE acc_no=?",(new_bal,d['acc']))
    cur.execute("INSERT INTO txns (acc_no,type,amount,date) VALUES (?,?,?,datetime('now','localtime'))",(d['acc'],d['type'],d['amt']))
    con.commit(); con.close()
    return jsonify({"success":True,"balance":new_bal})

@app.route('/api/all')
def all_acc():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    rows=con.execute("SELECT acc_no,name,balance FROM accounts").fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])

if __name__=='__main__':
    app.run(debug=True)