import sys
import os
from dotenv import load_dotenv

# ── Remplacer par ton chemin PythonAnywhere ──────────────────────────────────
# Exemple : /home/tonusername/coursier_bxl
PROJECT_PATH = '/home/TONUSERNAME/coursier_bxl'
# ─────────────────────────────────────────────────────────────────────────────

sys.path.insert(0, PROJECT_PATH)
load_dotenv(os.path.join(PROJECT_PATH, '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
