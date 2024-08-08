from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
from fpdf import FPDF
import os
from dotenv import load_dotenv

load_dotenv('keys.env')

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

product_prices = {
    'A': 20,
    'B': 30
}

@app.route("/")
def home():
    return "Nothing to show here"

@app.route("/sms", methods=['POST'])
def sms_reply():
    msg = request.form.get('Body')
    resp = MessagingResponse()

    if msg.lower() == 'hi':
        session.clear()
        session['step'] = 'menu'
        session['products'] = {}
        resp.message("Welcome! How can I assist you?\n 1. Create new estimate\n 2. Tweak prices")
    else:
        if 'step' not in session:
            session['step'] = 'start'
            session['products'] = {}

        if session['step'] == 'start':
            resp.message("Invalid, please type 'Hi' to start over.")
        elif session['step'] == 'menu':
            if msg == '1':
                session['step'] = 'create_estimate'
                session['products'] = {}
                resp.message("Please enter the product and quantity in this format: 'A 2'.")
            elif msg == '2':
                session['step'] = 'tweak_prices'
                resp.message("For what products do you wanna tweak the prices?")
            else:
                resp.message("Invalid input, please enter either 1 or 2")
        elif session['step'] == 'create_estimate':
            create_new_estimate(msg, resp)
        elif session['step'] == 'add_more':
            if msg.lower() == 'yes':
                session['step'] = 'create_estimate'
                resp.message("Please enter the product and quantity in this format: 'A 2'.")
            elif msg.lower() == 'no':
                generate_pdf()
                resp.message("Your invoice has been created.")
                session['step'] = 'start'
                session['products'] = {}
            else:
                resp.message("Invalid input, reply with either 'yes' or 'no'.")
        elif session['step'] == 'tweak_prices':
            tweak_prices(msg, resp)
        elif session['step'] == 'update_price':
            update_price(msg, resp)


    return str(resp), 200, {'Content-Type': 'application/xml'}

def create_new_estimate(msg, resp):
    product, quantity = msg.split()
    quantity = int(quantity)
    if product in product_prices:
        session['products'][product] = session['products'].get(product, 0) + quantity
        resp.message("Added. Do you wanna to add more? (yes/no)")
        session['step'] = 'add_more'
    else:
        resp.message("Invalid product. Please enter a valid product and quantity. For example, 'A 2'.")

def tweak_prices(msg, resp):
    if msg in product_prices:
        session['current_product'] = msg
        session['step'] = 'update_price'
        resp.message(f"Enter the new price for Product {msg}:")
    else:
        resp.message("Invalid, enter A or B.")

def update_price(msg, resp):
    new_price = float(msg)
    product_prices[session['current_product']] = new_price
    resp.message(f"The prices have been updated.")
    session['step'] = 'start'

def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=18)
    pdf.cell(200, 10, txt="Final Invoice", ln=True, align='C')
    total = 0
    for product, quantity in session['products'].items():
        price = product_prices[product] * quantity
        total += price
        pdf.cell(200, 10, txt=f"Product {product}: {quantity} units x {product_prices[product]} = {price}", ln=True)
    pdf.cell(200, 10, txt=f"Total: {total}", ln=True)
    pdf.output("estimate.pdf")

if __name__ == "__main__":
    app.run(debug=True)
