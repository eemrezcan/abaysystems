# app/models/project.py

import uuid
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, UniqueConstraint, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.color import Color
from app.models.app_user import AppUser
from app.db.base import Base


class Project(Base):
    __tablename__ = "project"

    __table_args__ = (
        # Aynı kullanıcının içinde proje kodu tek olsun
        UniqueConstraint('created_by', 'project_kodu', name='uq_project_owner_code'),
        # Listelemelerde hız için
        Index('ix_project_created_by', 'created_by'),
    )

    id             = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_kodu   = Column(String(50), unique=True, nullable=False)
    customer_id    = Column(PGUUID(as_uuid=True), ForeignKey("customer.id"), nullable=False)
    project_name   = Column(String(100), nullable=False)                # 🟢 Yeni eklenen sütun
    created_by     = Column(PGUUID(as_uuid=True), ForeignKey("app_user.id"), nullable=False)

    profile_color_id = Column(PGUUID(as_uuid=True), ForeignKey("color.id"), nullable=True)
    profile_color    = relationship("Color", foreign_keys=[profile_color_id])

    glass_color_id = Column(PGUUID(as_uuid=True), ForeignKey("color.id"), nullable=True)
    glass_color    = relationship("Color", foreign_keys=[glass_color_id])

    created_at     = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at     = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    creator         = relationship("AppUser", back_populates="projects")
    systems         = relationship("ProjectSystem", back_populates="project", cascade="all, delete-orphan")
    extra_materials = relationship("ProjectExtraMaterial", back_populates="project", cascade="all, delete-orphan")
    extra_remotes   = relationship("ProjectExtraRemote", back_populates="project", cascade="all, delete-orphan")


# 🔹 customer_id üzerinde doğrudan index (FK erişimleri için)
Index("ix_project_customer", Project.customer_id)

class ProjectSystem(Base):
    __tablename__ = "project_system"

    id                = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id        = Column(PGUUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    system_variant_id = Column(PGUUID(as_uuid=True), ForeignKey("system_variant.id"), nullable=False)
    width_mm          = Column(Numeric, nullable=False)
    height_mm         = Column(Numeric, nullable=False)
    quantity          = Column(Integer, nullable=False)
    created_at        = Column(TIMESTAMP(timezone=True), server_default=func.now())

    project   = relationship("Project", back_populates="systems")
    profiles  = relationship("ProjectSystemProfile", back_populates="project_system", cascade="all, delete-orphan")
    glasses   = relationship("ProjectSystemGlass", back_populates="project_system", cascade="all, delete-orphan")
    materials = relationship("ProjectSystemMaterial", back_populates="project_system", cascade="all, delete-orphan")
    remotes   = relationship("ProjectSystemRemote", back_populates="project_system", cascade="all, delete-orphan")


class ProjectSystemProfile(Base):
    __tablename__ = "project_system_profile"

    id                 = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_system_id  = Column(PGUUID(as_uuid=True), ForeignKey("project_system.id", ondelete="CASCADE"), nullable=False)
    profile_id         = Column(PGUUID(as_uuid=True), ForeignKey("profile.id"), nullable=False)
    cut_length_mm      = Column(Numeric, nullable=False)
    cut_count          = Column(Integer, nullable=False)
    total_weight_kg    = Column(Numeric, nullable=True)
    unit_price         = Column(Numeric, nullable=True)
    order_index       = Column(Integer, nullable=True)

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    project_system = relationship("ProjectSystem", back_populates="profiles")
    profile        = relationship("Profile")


class ProjectSystemGlass(Base):
    __tablename__ = "project_system_glass"

    id                 = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_system_id  = Column(PGUUID(as_uuid=True), ForeignKey("project_system.id", ondelete="CASCADE"), nullable=False)
    glass_type_id      = Column(PGUUID(as_uuid=True), ForeignKey("glass_type.id"), nullable=False)
    width_mm           = Column(Numeric, nullable=False)
    height_mm          = Column(Numeric, nullable=False)
    count              = Column(Integer, nullable=False)
    area_m2            = Column(Numeric, nullable=True)
    order_index       = Column(Integer, nullable=True)

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    project_system = relationship("ProjectSystem", back_populates="glasses")
    glass_type     = relationship("GlassType")


class ProjectSystemMaterial(Base):
    __tablename__ = "project_system_material"

    id                 = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_system_id  = Column(PGUUID(as_uuid=True), ForeignKey("project_system.id", ondelete="CASCADE"), nullable=False)
    material_id        = Column(PGUUID(as_uuid=True), ForeignKey("other_material.id"), nullable=False)
    cut_length_mm      = Column(Numeric, nullable=True)
    type               = Column(String(50), nullable=True)
    piece_length_mm    = Column(Integer, nullable=True)
    count              = Column(Integer, nullable=False)
    order_index       = Column(Integer, nullable=True)

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    project_system = relationship("ProjectSystem", back_populates="materials")
    material       = relationship("OtherMaterial")

class ProjectSystemRemote(Base):
    __tablename__ = "project_system_remote"

    id                = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_system_id = Column(PGUUID(as_uuid=True), ForeignKey("project_system.id", ondelete="CASCADE"), nullable=False)
    remote_id         = Column(PGUUID(as_uuid=True), ForeignKey("remote.id"), nullable=False)
    count             = Column(Integer, nullable=False)          # kaç adet kumanda
    unit_price        = Column(Numeric, nullable=True)           # opsiyonel: proje anındaki birim fiyatı snapshot
    order_index       = Column(Integer, nullable=True)           # şablondaki sırayı korumak için

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    project_system = relationship("ProjectSystem", back_populates="remotes")
    remote         = relationship("Remote")



class ProjectExtraMaterial(Base):
    __tablename__ = "project_extra_material"

    id            = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id    = Column(PGUUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    material_id   = Column(PGUUID(as_uuid=True), ForeignKey("other_material.id"), nullable=False)
    count         = Column(Integer, nullable=False)
    cut_length_mm = Column(Numeric, nullable=True)
    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    project       = relationship("Project", back_populates="extra_materials")
    material      = relationship("OtherMaterial")

class ProjectExtraProfile(Base):
    __tablename__ = "project_extra_profile"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(PGUUID(as_uuid=True), ForeignKey("profile.id"), nullable=False)
    cut_length_mm = Column(Numeric, nullable=False)
    cut_count = Column(Integer, nullable=False)
    unit_price = Column(Numeric, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    project = relationship("Project", backref="extra_profiles")
    profile = relationship("Profile")


class ProjectExtraGlass(Base):
    __tablename__ = "project_extra_glass"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    glass_type_id = Column(PGUUID(as_uuid=True), ForeignKey("glass_type.id"), nullable=False)
    width_mm = Column(Numeric, nullable=False)
    height_mm = Column(Numeric, nullable=False)
    count = Column(Integer, nullable=False)
    area_m2 = Column(Numeric, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    project = relationship("Project", backref="extra_glasses")
    glass_type = relationship("GlassType")

class ProjectExtraRemote(Base):
    __tablename__ = "project_extra_remote"

    id         = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    remote_id  = Column(PGUUID(as_uuid=True), ForeignKey("remote.id"), nullable=False)
    count      = Column(Integer, nullable=False)
    unit_price = Column(Numeric, nullable=True)                  # opsiyonel snapshot
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    project = relationship("Project", back_populates="extra_remotes")
    remote  = relationship("Remote")

