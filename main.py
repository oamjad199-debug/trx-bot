import os
from flask import Flask, request
import telebot

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

RENDER_URL = "https://trx-bot-e61j.onrender.com"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تطبيق الأرباح</title>
    <style>
        body { background: #0f172a; color: #fff; font-family: Tahoma, sans-serif; text-align: center; padding-top: 50px; }
        .card { background: #1e293b; padding: 25px; border-radius: 12px; display: inline-block; width: 85%; max-width: 400px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h2 { color: #38bdf8; }
        p { color: #94a3b8; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="card">
        <h2>تطبيق أرباح TRX 🚀</h2>
        <p>أهلاً بك يا عمر! تم التحقق بنجاح، يمكنك الآن متابعة الأرباح.</p>
    </div>
</body>
</html>
"""

@server.route('/')
def home():
    return HTML_TEMPLATE

@server.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        json_str = request.
