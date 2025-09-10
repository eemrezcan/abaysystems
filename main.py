from app.db.base import Base
import app.models.app_user
import app.models.project
import app.models.order
import app.models.customer
import app.models.glass_type
import app.models.other_material
import app.models.profile
import app.models.system

from fastapi import FastAPI
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

from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from app.core.config import MEDIA_ROOT
from pathlib import Path

Path(MEDIA_ROOT).mkdir(parents=True, exist_ok=True)

app = FastAPI()


app.mount("/static", StaticFiles(directory=MEDIA_ROOT), name="static")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Geliştirme için sadece bu kökenlere izin
    allow_credentials=True,
    allow_methods=["*"],        # Tüm HTTP metodları
    allow_headers=["*"],        # Tüm başlıklar
)





# Core resource routes
app.include_router(auth_router)
app.include_router(auth_extra_router)
app.include_router(me_pp_routes.router)
app.include_router(me_pdf_titles_routes.router)
app.include_router(me_pdf_brands_routes.router)
app.include_router(me_project_code_routes.router)
app.include_router(dealers_router)
app.include_router(customer_router)
app.include_router(project_router)
app.include_router(system_router)
app.include_router(variant_router)

#app.include_router(order_router)

app.include_router(color.router)
app.include_router(catalog_router)




