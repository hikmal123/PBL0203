"""
build.py — Netlify Static Site Generator for PBL0203
=====================================================
Script ini dijalankan saat build di Netlify (bukan npm).
Ia membaca CSV, merender template Jinja2, dan menghasilkan
file HTML statis ke folder `public/` sebagai output build.

Kenapa static generation?
- Netlify adalah platform untuk static sites / serverless functions
- Proyek ini tidak memerlukan server yang terus berjalan
- Data CSV tidak berubah saat runtime → cocok untuk pre-render
- Lebih cepat, lebih murah, lebih mudah di-deploy

Output struktur:
  public/
  ├── index.html             ← welcome page
  ├── pbl0203/
  │   └── index.html         ← analytics dashboard
  └── static/
      └── style.css          ← aset CSS
"""

import os
import shutil
import json

import pandas as pd
import jinja2

# ── 1. Setup folder output ──────────────────────────────────
BUILD_DIR = "public"
os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(os.path.join(BUILD_DIR, "pbl0203"), exist_ok=True)
print(f"[OK] Build dir ready: {BUILD_DIR}/")

# ── 2. Copy aset statis (CSS, JS, dll) ─────────────────────
static_src  = "static"
static_dest = os.path.join(BUILD_DIR, "static")
if os.path.exists(static_dest):
    shutil.rmtree(static_dest)
shutil.copytree(static_src, static_dest)
print(f"[OK] Static assets copied -> {static_dest}/")

# ── 3. Setup Jinja2 ─────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
    autoescape=True
)

# ── 4. Baca dan proses CSV ──────────────────────────────────
csv_path = os.path.join(BASE_DIR, "data", "ai_student.csv")
df = pd.read_csv(csv_path)

important_columns = [
    "Student_ID", "Age", "Gender", "Education_Level",
    "AI_Tool_Used", "Daily_Usage_Hours", "Purpose",
    "Impact_on_Grades", "Satisfaction_Level"
]
df_selected = df[important_columns]
students_data = df_selected.to_dict(orient="records")

total_students      = len(df)
avg_usage           = round(df["Daily_Usage_Hours"].mean(), 1)
tool_counts         = df["AI_Tool_Used"].value_counts().to_dict()
impact_counts       = df["Impact_on_Grades"].value_counts().to_dict()
purpose_counts      = df["Purpose"].value_counts().to_dict()
satisfaction_counts = df["Satisfaction_Level"].value_counts().to_dict()
education_counts    = df["Education_Level"].value_counts().to_dict()
avg_usage_per_tool  = (
    df.groupby("AI_Tool_Used")["Daily_Usage_Hours"]
    .mean().round(1).to_dict()
)

impact_per_tool = {}
for tool in df["AI_Tool_Used"].unique():
    tool_df = df[df["AI_Tool_Used"] == tool]
    impact_per_tool[tool] = tool_df["Impact_on_Grades"].value_counts().to_dict()

print(f"[OK] CSV processed: {total_students} students, {len(tool_counts)} AI tools")

# ── 5. Render welcome page -> public/index.html ─────────────
tmpl = jinja_env.get_template("welcome.html")
html = tmpl.render()
out_path = os.path.join(BUILD_DIR, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"[OK] Rendered -> {out_path}")

# ── 6. Render dashboard -> public/pbl0203.html ───────────────
tmpl = jinja_env.get_template("pbl0203.html")
html = tmpl.render(
    students            = students_data,
    total_students      = total_students,
    avg_usage           = avg_usage,
    tool_counts         = tool_counts,
    impact_counts       = impact_counts,
    purpose_counts      = purpose_counts,
    satisfaction_counts = satisfaction_counts,
    education_counts    = education_counts,
    avg_usage_per_tool  = avg_usage_per_tool,
    impact_per_tool     = json.dumps(impact_per_tool),
    tool_counts_json    = json.dumps(tool_counts),
    impact_counts_json  = json.dumps(impact_counts),
    purpose_counts_json = json.dumps(purpose_counts),
    satisfaction_counts_json = json.dumps(satisfaction_counts),
)
out_path = os.path.join(BUILD_DIR, "pbl0203.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"[OK] Rendered -> {out_path}")

print("\n>>> Build complete! Output: public/")
