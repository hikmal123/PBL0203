"""
netlify/functions/handler.py — Netlify Serverless Handler
==========================================================
File ini membungkus aplikasi Falcon (ASGI) dengan Mangum
agar dapat berjalan sebagai AWS Lambda / Netlify Function.

Cara kerja:
- Netlify Functions menggunakan AWS Lambda di balik layar
- Mangum bertindak sebagai adapter ASGI → Lambda event/context
- Setiap request HTTP diteruskan ke Falcon app via Mangum
"""

import sys
import os

# Tambahkan root project ke sys.path agar bisa import main.py
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from mangum import Mangum
from main import app  # Falcon ASGI app dari main.py

# Bungkus Falcon ASGI app dengan Mangum adapter
# Ini yang akan dipanggil oleh Netlify Function saat ada request masuk
handler = Mangum(app, lifespan="off")
