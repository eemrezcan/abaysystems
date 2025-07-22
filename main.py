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

app = FastAPI()

# Authentication routes
app.include_router(auth_router)

# Core resource routes
app.include_router(variant_router)
app.include_router(order_router)
app.include_router(system_router)
app.include_router(project_router)
app.include_router(catalog_router)
