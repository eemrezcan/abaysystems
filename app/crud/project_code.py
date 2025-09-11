# app/crud/project_code.py
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.project_code_rule import ProjectCodeRule
from app.models.project import Project

def _format_code(prefix: str, number: int, sep: str, padding: int) -> str:
    if padding and padding > 0:
        return f"{prefix}{sep}{number:0{padding}d}"
    return f"{prefix}{sep}{number}"

# ---------- Rule CRUD ----------

def get_rule_by_owner(db: Session, owner_id: UUID) -> Optional[ProjectCodeRule]:
    return (
        db.query(ProjectCodeRule)
          .filter(ProjectCodeRule.owner_id == owner_id)
          .first()
    )

def create_rule(
    db: Session,
    *,
    owner_id: UUID,
    prefix: str,
    separator: str = "-",
    padding: int = 0,
    start_number: int = 1
) -> ProjectCodeRule:
    rule = ProjectCodeRule(
        owner_id=owner_id,
        prefix=prefix,
        separator=separator or "-",
        padding=padding or 0,
        start_number=start_number,
        current_number=max(start_number - 1, 0),
        is_active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

def update_rule(
    db: Session,
    rule: ProjectCodeRule,
    *,
    prefix: Optional[str] = None,
    separator: Optional[str] = None,
    padding: Optional[int] = None,
    start_number: Optional[int] = None
) -> ProjectCodeRule:
    if prefix is not None:
        rule.prefix = prefix
    if separator is not None:
        rule.separator = separator
    if padding is not None:
        rule.padding = padding
    if start_number is not None:
        rule.start_number = start_number
        # sonraki verilecek sayı: max(current_number+1, start_number)
        if rule.current_number < start_number - 1:
            rule.current_number = start_number - 1
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


# ---------- Preview (kilitsiz) ----------

def preview_next_code(db: Session, owner_id: UUID) -> Tuple[int, str]:
    rule = get_rule_by_owner(db, owner_id)
    if not rule or not rule.is_active:
        raise ValueError("Önce proje kodu kuralınızı oluşturun.")
    next_number = max(rule.current_number + 1, rule.start_number)
    code = _format_code(rule.prefix, next_number, rule.separator, rule.padding)
    return next_number, code

# ---------- Issue (kilitli, tek transaction) ----------

def issue_next_code_in_tx(db: Session, owner_id: UUID) -> Tuple[int, str]:
    """
    Aynı owner için satırı kilitleyerek bir sonraki kodu verir.
    Burada COMMIT yapılmaz; çağıran tarafta proje kaydıyla birlikte tek commit atılmalıdır.
    """
    rule = (
        db.query(ProjectCodeRule)
          .filter(ProjectCodeRule.owner_id == owner_id)
          .with_for_update(nowait=True)
          .first()
    )
    if not rule or not rule.is_active:
        raise ValueError("Proje kodu kuralı bulunamadı veya pasif.")

    next_number = max(rule.current_number + 1, rule.start_number)

    # Eski verilerden dolayı çakışma riskine karşı kontrollü artış
    while True:
        candidate = _format_code(rule.prefix, next_number, rule.separator, rule.padding)
        exists = db.query(Project.id).filter(Project.project_kodu == candidate).first()
        if not exists:
            break
        next_number += 1

    rule.current_number = next_number
    db.add(rule)
    return next_number, _format_code(rule.prefix, next_number, rule.separator, rule.padding)
