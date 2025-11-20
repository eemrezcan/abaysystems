# app/models/project.py

import uuid
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, UniqueConstraint, Index, Boolean,Date
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP
from sqlalchemy.sql import func,expression
from sqlalchemy.orm import relationship
from app.models.color import Color
from app.models.app_user import AppUser
from app.db.base import Base
from sqlalchemy.ext.hybrid import hybrid_property


class Project(Base):
    __tablename__ = "project"

    __table_args__ = (
        UniqueConstraint('created_by', 'project_kodu', name='uq_project_owner_code'),
        Index('ix_project_created_by', 'created_by'),
    )

    id             = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_kodu   = Column(String(50), nullable=False)
    # YENİ
    customer_id    = Column(
        PGUUID(as_uuid=True),
        ForeignKey("customer.id", ondelete="SET NULL"),
        nullable=True
    )
    project_name   = Column(String(100), nullable=False)
    created_by     = Column(PGUUID(as_uuid=True), ForeignKey("app_user.id"), nullable=False)

    # Üst bilgi fiyat alanları (opsiyonel)
    press_price    = Column(Numeric, nullable=True)
    painted_price  = Column(Numeric, nullable=True)

    # 🔹 Yeni sütunlar
    is_teklif          = Column(Boolean, nullable=False, server_default=expression.true())  # yeni proje default: teklif
    paint_status       = Column(String(50), nullable=False, server_default="durum belirtilmedi")
    glass_status       = Column(String(50), nullable=False, server_default="durum belirtilmedi")
    production_status  = Column(String(50), nullable=False, server_default="durum belirtilmedi")
    approval_date      = Column(TIMESTAMP(timezone=True), nullable=True)

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


# 🔹 mevcut index
Index("ix_project_customer", Project.customer_id)

# 🔹 yeni indexler
Index("ix_project_is_teklif", Project.is_teklif)
Index("ix_project_approval_date", Project.approval_date)

# ✅ filtre performansı için ek index'ler
Index("ix_project_paint_status", Project.paint_status)
Index("ix_project_glass_status", Project.glass_status)
Index("ix_project_production_status", Project.production_status)

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
    order_index        = Column(Integer, nullable=True)

    # --- NEW: Şablondaki boyalı/boyasız kararını proje satırına da taşı ---
    is_painted         = Column(Boolean, nullable=False, default=False)  # NEW ✅

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
    order_index        = Column(Integer, nullable=True)
    unit_price        = Column(Numeric, nullable=True)   # 💲 opsiyonel: proje anındaki birim fiyat snapshot


    # 🔁 Çift cam renk alanları (DB kolon adları birebir korunur)
    glass_color_id_1   = Column(PGUUID(as_uuid=True), ForeignKey("color.id"), nullable=True)
    glass_color_text_1 = Column("glass_color_1", String(50), nullable=True)  # serbest metin kolonu (DB adı: glass_color_1)

    glass_color_id_2   = Column(PGUUID(as_uuid=True), ForeignKey("color.id"), nullable=True)
    glass_color_text_2 = Column("glass_color_2", String(50), nullable=True)  # serbest metin kolonu (DB adı: glass_color_2)

    # 🔗 İlişkiler — isim formatı eskiyle uyumlu (cam rengi ilişkisi)
    glass_color_1      = relationship("Color", foreign_keys=[glass_color_id_1])
    glass_color_2      = relationship("Color", foreign_keys=[glass_color_id_2])

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    project_system = relationship("ProjectSystem", back_populates="glasses")
    glass_type     = relationship("GlassType")

    # --- Derived fields from related GlassType (read-only) ---
    @hybrid_property
    def belirtec_1_value(self):
        return self.glass_type.belirtec_1 if self.glass_type else None

    @hybrid_property
    def belirtec_2_value(self):
        return self.glass_type.belirtec_2 if self.glass_type else None



class ProjectSystemMaterial(Base):
    __tablename__ = "project_system_material"

    id                 = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_system_id  = Column(PGUUID(as_uuid=True), ForeignKey("project_system.id", ondelete="CASCADE"), nullable=False)
    material_id        = Column(PGUUID(as_uuid=True), ForeignKey("other_material.id"), nullable=False)
    cut_length_mm      = Column(Numeric, nullable=True)
    type               = Column(String(50), nullable=True)
    piece_length_mm    = Column(Integer, nullable=True)
    count              = Column(Integer, nullable=False)
    unit_price         = Column(Numeric, nullable=True)   # 💲 opsiyonel: proje anındaki birim fiyat snapshot
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
    unit_price    = Column(Numeric, nullable=True)        # 💲 opsiyonel snapshot
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

    is_painted         = Column(Boolean, nullable=False, default=False)  # NEW ✅

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

    id           = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id   = Column(PGUUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    glass_type_id= Column(PGUUID(as_uuid=True), ForeignKey("glass_type.id"), nullable=False)
    width_mm     = Column(Numeric, nullable=False)
    height_mm    = Column(Numeric, nullable=False)
    count        = Column(Integer, nullable=False)
    area_m2      = Column(Numeric, nullable=True)
    unit_price   = Column(Numeric, nullable=True)
    created_at   = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # 🔁 Çift cam renk alanları (DB kolon adları birebir korunur)
    glass_color_id_1   = Column(PGUUID(as_uuid=True), ForeignKey("color.id"), nullable=True)
    glass_color_text_1 = Column("glass_color_1", String(50), nullable=True)  # serbest metin kolonu (DB adı: glass_color_1)

    glass_color_id_2   = Column(PGUUID(as_uuid=True), ForeignKey("color.id"), nullable=True)
    glass_color_text_2 = Column("glass_color_2", String(50), nullable=True)  # serbest metin kolonu (DB adı: glass_color_2)

    # 🔗 İlişkiler — isim formatı eskiyle uyumlu
    glass_color_1      = relationship("Color", foreign_keys=[glass_color_id_1])
    glass_color_2      = relationship("Color", foreign_keys=[glass_color_id_2])

    # --- PDF Flags ---
    cam_ciktisi                   = Column(Boolean, nullable=False, default=True)
    profil_aksesuar_ciktisi       = Column(Boolean, nullable=False, default=True)
    boya_ciktisi                  = Column(Boolean, nullable=False, default=True)
    siparis_ciktisi               = Column(Boolean, nullable=False, default=True)
    optimizasyon_detayli_ciktisi  = Column(Boolean, nullable=False, default=True)
    optimizasyon_detaysiz_ciktisi = Column(Boolean, nullable=False, default=True)

    project    = relationship("Project", backref="extra_glasses")
    glass_type = relationship("GlassType")

    # --- Derived fields from related GlassType (read-only) ---
    @hybrid_property
    def belirtec_1_value(self):
        return self.glass_type.belirtec_1 if self.glass_type else None

    @hybrid_property
    def belirtec_2_value(self):
        return self.glass_type.belirtec_2 if self.glass_type else None


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
