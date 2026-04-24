"""
main.py — Falcon + Mangum Serverless Application (PBL0203)
===========================================================
File ini merupakan entry point aplikasi AI Student Analytics.
Menggunakan framework Falcon (WSGI) dan Mangum untuk deployment serverless.

Fitur:
- Membaca data CSV (ai_student.csv) menggunakan pandas
- Mengambil kolom penting: AI Tool, Daily Usage, Purpose, Impact on Grades, Satisfaction
- Mengolah data menjadi statistik ringkasan (summary analytics)
- Menampilkan data dalam template HTML premium via Jinja2

Arsitektur:
- Falcon   : Web framework (WSGI-based)
- Pandas   : Data processing dari CSV
- Jinja2   : Template engine untuk rendering HTML
- Mangum   : Adapter ASGI/WSGI → AWS Lambda handler

Cara menjalankan (lokal):
    pip install falcon jinja2 pandas mangum waitress
    python main.py

Referensi:
- Falcon Docs : https://falcon.readthedocs.io/
- Mangum Docs : https://mangum.io/
"""

# ============================================================
# 1. Import Falcon dan Mangum (untuk serverless)
# ============================================================
import falcon
import falcon.asgi
from mangum import Mangum
import pandas as pd
import jinja2
import json
import os


# ============================================================
# Konfigurasi Jinja2 Template Engine
# ============================================================
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
    autoescape=True
)


# ============================================================
# 2. Buat Class Resource untuk PBL0203
# ============================================================
class PBL0203Resource:
    """
    Resource class untuk endpoint PBL0203 — AI Student Analytics.
    
    Membaca dataset AI Student Life dari file CSV,
    mengolah data menggunakan pandas, dan menampilkan
    hasil analisis dalam template HTML yang interaktif.
    """

    async def on_get(self, req, resp):
        """
        3. Method ON_GET (Read):
           a. Gunakan pandas.read_csv('data/ai_student.csv')
           b. Ambil beberapa kolom penting (AI Tool, Usage, Impact, dll.)
           c. Ubah hasil pandas menjadi format list/dictionary
           d. Masukkan data ke Template HTML (Jinja2)
        """

        # ----------------------------------------------------------
        # 3a. Baca CSV menggunakan pandas
        # ----------------------------------------------------------
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ai_student.csv")
        df = pd.read_csv(csv_path)

        # ----------------------------------------------------------
        # 3b. Ambil beberapa kolom penting
        # ----------------------------------------------------------
        # Kolom utama yang ditampilkan di tabel
        important_columns = [
            "Student_ID", "Age", "Gender", "Education_Level",
            "AI_Tool_Used", "Daily_Usage_Hours", "Purpose",
            "Impact_on_Grades", "Satisfaction_Level"
        ]
        df_selected = df[important_columns]

        # ----------------------------------------------------------
        # 3c. Ubah hasil pandas menjadi format list/dictionary
        # ----------------------------------------------------------
        # Data tabel (list of dict)
        students_data = df_selected.to_dict(orient="records")

        # ----- Summary Statistics (Ringkasan Analitik) -----
        total_students = len(df)
        avg_usage = round(df["Daily_Usage_Hours"].mean(), 1)

        # Distribusi AI Tool yang digunakan
        tool_counts = df["AI_Tool_Used"].value_counts().to_dict()

        # Distribusi Impact on Grades
        impact_counts = df["Impact_on_Grades"].value_counts().to_dict()

        # Distribusi Purpose
        purpose_counts = df["Purpose"].value_counts().to_dict()

        # Distribusi Satisfaction Level
        satisfaction_counts = df["Satisfaction_Level"].value_counts().to_dict()

        # Distribusi Education Level
        education_counts = df["Education_Level"].value_counts().to_dict()

        # Rata-rata usage per tool
        avg_usage_per_tool = df.groupby("AI_Tool_Used")["Daily_Usage_Hours"].mean().round(1).to_dict()

        # Impact per tool (cross-tabulation)
        impact_per_tool = {}
        for tool in df["AI_Tool_Used"].unique():
            tool_df = df[df["AI_Tool_Used"] == tool]
            impact_per_tool[tool] = tool_df["Impact_on_Grades"].value_counts().to_dict()

        # ----------------------------------------------------------
        # 3d. Masukkan data ke Template HTML (Jinja2)
        # ----------------------------------------------------------
        template = jinja_env.get_template("pbl0203.html")
        rendered = template.render(
            students=students_data,
            total_students=total_students,
            avg_usage=avg_usage,
            tool_counts=tool_counts,
            impact_counts=impact_counts,
            purpose_counts=purpose_counts,
            satisfaction_counts=satisfaction_counts,
            education_counts=education_counts,
            avg_usage_per_tool=avg_usage_per_tool,
            impact_per_tool=json.dumps(impact_per_tool),
            tool_counts_json=json.dumps(tool_counts),
            impact_counts_json=json.dumps(impact_counts),
            purpose_counts_json=json.dumps(purpose_counts),
            satisfaction_counts_json=json.dumps(satisfaction_counts),
        )

        resp.status = falcon.HTTP_200
        resp.content_type = "text/html; charset=utf-8"
        resp.text = rendered


class WelcomeResource:
    """Render the simple bright welcome page."""

    async def on_get(self, req, resp):
        template = jinja_env.get_template("welcome.html")
        resp.status = falcon.HTTP_200
        resp.content_type = "text/html; charset=utf-8"
        resp.text = template.render()


class StaticResource:
    """Serve file statis (CSS, JS, gambar) dari folder static/."""

    async def on_get(self, req, resp, filepath):
        file_path = os.path.join(STATIC_DIR, filepath)
        if not os.path.isfile(file_path):
            resp.status = falcon.HTTP_404
            resp.text = "File not found"
            return

        # Tentukan content type
        ext = os.path.splitext(filepath)[1].lower()
        content_types = {
            ".css": "text/css",
            ".js": "application/javascript",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
        }
        resp.content_type = content_types.get(ext, "application/octet-stream")

        # Baca file
        mode = "rb"
        with open(file_path, mode) as f:
            resp.data = f.read()


# ============================================================
# Inisialisasi Aplikasi Falcon (ASGI)
# ============================================================
app = falcon.asgi.App()

# Route registrasi
app.add_route("/", WelcomeResource())
app.add_route("/pbl0203", PBL0203Resource())
app.add_route("/static/{filepath}", StaticResource())


# ============================================================
# 4. Bungkus aplikasi dengan Mangum: handler = Mangum(app)
# ============================================================
handler = Mangum(app)


# ============================================================
# Local Development Server (opsional)
# ============================================================
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  PBL0203 — AI Student Analytics")
    print("  Falcon + Mangum Serverless Application")
    print("  Running on: http://localhost:8000")
    print("=" * 60)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
