from app.db.base import Base
import app.models.app_user
import app.models.project
import app.models.order
import app.models.customer
import app.models.glass_type
import app.models.other_material
import app.models.profile
import app.models.system
import app.models.calculation_helper

from fastapi import FastAPI, APIRouter
from app.routes.order import router as order_router
from app.routes.system import router as system_router 
from app.routes.project import router as project_router
from app.routes.catalog import router as catalog_router
from app.routes.system_variant import router as variant_router
from app.routes.auth import router as auth_router
from app.routes.customer import router as customer_router
from app.routes.dealers import router as dealers_router
from app.routes.auth_extra import router as auth_extra_router
from app.routes import color
from app.routes import me_profile_picture as me_pp_routes
from app.routes import me_pdf_titles as me_pdf_titles_routes
from app.routes import me_pdf_brands as me_pdf_brands_routes
from app.routes import me_project_code as me_project_code_routes
from app.routes import me_calculation_helper as me_calc_routes

from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from app.core.config import MEDIA_ROOT
from pathlib import Path
from app.core.config import settings

Path(MEDIA_ROOT).mkdir(parents=True, exist_ok=True)

app = FastAPI()


app.mount("/static", StaticFiles(directory=MEDIA_ROOT), name="static")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://www.tumenaluminyum.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,      # Geliştirme için sadece bu kökenlere izin
    allow_origin_regex=r"^https://(bayi\.)?tumenaluminyum\.com$",
    allow_credentials=True,
    allow_methods=["*"],        # Tüm HTTP metodları
    allow_headers=["*"],
    expose_headers=["*"],        # Tüm başlıklar
)

debug_router = APIRouter()

@debug_router.get("/__cors_debug")
def cors_debug():
    return {
        "BACKEND_CORS_ORIGINS": settings.BACKEND_CORS_ORIGINS,
        "BACKEND_CORS_ORIGINS_RAW": getattr(settings, "BACKEND_CORS_ORIGINS_RAW", None),
        "FRONTEND_URL": settings.FRONTEND_URL,
        "SAMESITE": settings.REFRESH_COOKIE_SAMESITE,
        "DOMAIN": settings.REFRESH_COOKIE_DOMAIN,
    }

# en altta veya router tanımlarının yanında
app.include_router(debug_router, prefix="/api")




# Core resource routes
app.include_router(auth_router)
app.include_router(auth_extra_router)
app.include_router(me_pp_routes.router)
app.include_router(me_pdf_titles_routes.router)
app.include_router(me_pdf_brands_routes.router)
app.include_router(me_project_code_routes.router)
app.include_router(me_calc_routes.router)
app.include_router(dealers_router)
app.include_router(customer_router)
app.include_router(project_router)
app.include_router(system_router)
app.include_router(variant_router)

#app.include_router(order_router)

app.include_router(color.router)
app.include_router(catalog_router)


