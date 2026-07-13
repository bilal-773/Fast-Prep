import os

def load_env():
    # Load root .env relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(os.path.dirname(current_dir), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

# Initialize environment
load_env()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://your-project-id.supabase.co")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "your_supabase_service_role_key_here")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "your_supabase_anon_key_here")
SUPABASE_PROJECT_ID = os.environ.get("SUPABASE_PROJECT_ID", "your_supabase_project_id_here")
SUPABASE_DB_PASSWORD = os.environ.get("SUPABASE_DB_PASSWORD", "your_supabase_db_password_here")

# Connection strings dynamically built
DB_CONNECTIONS = [
    f"postgresql://postgres.{SUPABASE_PROJECT_ID}:{SUPABASE_DB_PASSWORD}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require",
    f"postgresql://postgres:{SUPABASE_DB_PASSWORD}@db.{SUPABASE_PROJECT_ID}.supabase.co:5432/postgres",
    f"postgresql://postgres.{SUPABASE_PROJECT_ID}:{SUPABASE_DB_PASSWORD}@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres",
]
