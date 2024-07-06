from flask import Flask, request, make_response, render_template_string
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.csrf import CSRFProtect
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'an_toan_thong_tin'  
csrf = CSRFProtect(app)

# Simulate a database
user_accounts = {
    'alice': {'balance': 10000, 'password': 'alice'},
    'attacker': {'balance': 0, 'password': '12345'},
    'bob': {'balance': 10000, 'password': 'bob'},
}

@app.route('/')
def home():
    return "Welcome to the Bank"

@app.route('/login', methods=['GET', 'POST'])
@csrf.exempt  # Exempt CSRF for the login route (since it is not typically needed)
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in user_accounts and user_accounts[username]['password'] == password:
            resp = make_response(f"Logged in as {username}")
            resp.set_cookie('user_session', json.dumps({'username': username}))
            return resp
        else:
            return "Invalid credentials", 401
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Log In">
        </form>
    '''

@app.route('/logout')
def logout():
    resp = make_response("Logged out")
    resp.set_cookie('user_session', '', expires=0)
    return resp

@app.route('/balance')
def balance():
    session_data = get_session_data()
    if not session_data:
        return "Please log in first", 401
    username = session_data['username']
    balance = user_accounts[username]['balance']
    return f"Your balance is ${balance}"

class TransferForm(FlaskForm):
    to = StringField('To account', validators=[DataRequired()])
    amount = IntegerField('Amount', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Transfer')

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    session_data = get_session_data()
    if not session_data:
        return "Please log in first", 401

    form = TransferForm()
    if form.validate_on_submit():
        from_account = session_data['username']
        to_account = form.to.data
        amount = form.amount.data

        if to_account not in user_accounts:
            return "Recipient account does not exist", 400
        if user_accounts[from_account]['balance'] < amount:
            return "Insufficient funds", 400

        # Perform transfer
        user_accounts[from_account]['balance'] -= amount
        user_accounts[to_account]['balance'] += amount

        return f"Transferred ${amount} to account {to_account}"

    return render_template_string('''
        <form method="post">
            {{ form.hidden_tag() }}
            {{ form.to.label }} {{ form.to(size=20) }}<br>
            {{ form.amount.label }} {{ form.amount() }}<br>
            {{ form.submit() }}
        </form>
    ''', form=form)

def get_session_data():
    session_cookie = request.cookies.get('user_session')
    if session_cookie:
        return json.loads(session_cookie)
    return None

if __name__ == '__main__':
    app.run(debug=True)