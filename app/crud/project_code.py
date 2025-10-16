# app/crud/project_code.py
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.models.project_code_rule import ProjectCodeRule
from app.models.project_code_ledger import ProjectCodeLedger
from app.models.project import Project


# -----------------------------
# Yardımcılar
# -----------------------------

def _format_code(prefix: str, number: int, sep: str, padding: int = 0) -> str:
    """
    Kod formatlayıcı.
    padding varsa sıfırla doldurur; yoksa düz sayı yazar.
    """
    if padding and padding > 0:
        return f"{prefix}{sep}{number:0{padding}d}"
    return f"{prefix}{sep}{number}"


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
    start_number: int = 1
) -> ProjectCodeRule:
    rule = ProjectCodeRule(
        owner_id=owner_id,
        prefix=prefix,
        separator=separator or "-",
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
    start_number: Optional[int] = None
) -> ProjectCodeRule:
    if prefix is not None:
        rule.prefix = prefix
    if separator is not None:
        rule.separator = separator
    if start_number is not None:
        # sadece alt limit
        rule.start_number = start_number
        # current_number'ı geri çekmeyiz; sadece çok gerideyse ileri alırız
        if rule.current_number < start_number - 1:
            rule.current_number = start_number - 1
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


# -----------------------------
# Önizleme (kilitsiz)
# -----------------------------

def preview_next_code(db: Session, owner_id: UUID) -> Tuple[int, str]:
    """
    Kilitsiz bir önizleme.
    Ledger'da kullanılan sayıları atlayarak start_number alt sınırından sonraki ilk boş sayıyı bulur.
    (Race koşullarında sapabilir; yalnızca gösterim içindir.)
    """
    rule = get_rule_by_owner(db, owner_id)
    if not rule or not rule.is_active:
        raise ValueError("Önce proje kodu kuralınızı oluşturun.")

    candidate = max(rule.current_number + 1, rule.start_number)

    # Ledger'a bakarak ilk boş sayıyı ara
    while True:
        exists = (
            db.query(ProjectCodeLedger.owner_id)
              .filter(
                  ProjectCodeLedger.owner_id == owner_id,
                  ProjectCodeLedger.number == candidate,
              )
              .first()
        )
        if not exists:
            break
        candidate += 1

    sep = getattr(rule, "separator", "-")
    pad = getattr(rule, "padding", 0)  # padding kolonu DB'de yoksa 0 kabul et
    code = _format_code(rule.prefix, candidate, sep, pad)
    return candidate, code


# -----------------------------
# Dağıtım (kilitli, tek transaction)
# -----------------------------

def issue_next_code_in_tx(db: Session, owner_id: UUID) -> Tuple[int, str]:
    rule = (
        db.query(ProjectCodeRule)
          .filter(ProjectCodeRule.owner_id == owner_id)
          .with_for_update(nowait=True)
          .first()
    )
    if not rule or not rule.is_active:
        raise ValueError("Proje kodu kuralı bulunamadı veya pasif.")

    pad = getattr(rule, "padding", 0)  # 👈 güvenli oku (kolon kaldırılmış olabilir)
    sep = getattr(rule, "separator", "-")

    next_number = max(rule.current_number + 1, rule.start_number)

    while True:
        candidate = _format_code(rule.prefix, next_number, sep, pad)
        # ledger + project kontrolü
        exists_in_ledger = (
            db.query(ProjectCodeLedger.number)
              .filter(
                  ProjectCodeLedger.owner_id == owner_id,
                  ProjectCodeLedger.number == next_number,
              )
              .first()
        )
        exists_in_project = (
            db.query(Project.id)
              .filter(Project.project_kodu == candidate)
              .first()
        )
        if not exists_in_ledger and not exists_in_project:
            break
        next_number += 1

    # Sadece rule.current_number'ı ileri al (ledger yazımını ayrı adımda yapacağız)
    rule.current_number = next_number
    db.add(rule)
    return next_number, _format_code(rule.prefix, next_number, sep, pad)


# -----------------------------
# Yardımcı: varolan bir projeye kod atama (ledger ile)
# -----------------------------

def assign_code_to_project_in_tx(
    db: Session,
    *,
    owner_id: UUID,
    project_id: UUID,
    number: int,
    code: str,
) -> None:
    """
    issue_next_code_in_tx sonrası veya manuel numara değiştirme sırasında,
    ledger kaydını ilgili projeyle eşleştirir (INSERT veya UPDATE).
    COMMIT burada yapılmaz.
    """
    # 1) Ledger'da bu (owner, number) var mı?
    row = (
        db.query(ProjectCodeLedger)
          .filter(
              ProjectCodeLedger.owner_id == owner_id,
              ProjectCodeLedger.number == number,
          )
          .with_for_update(nowait=True)
          .first()
    )

    if row is None:
        # Rezervasyon yapılmadan direkt atama gerekiyorsa: INSERT deneriz
        db.add(ProjectCodeLedger(
            owner_id=owner_id,
            number=number,
            project_id=project_id,
            project_kodu=code,
        ))
    else:
        # Var olan rezervasyonu bu projeye bağla
        row.project_id = project_id
        row.project_kodu = code
        db.add(row)

    # current_number bilgisini ileri almakta sakınca yok
    rule = (
        db.query(ProjectCodeRule)
          .filter(ProjectCodeRule.owner_id == owner_id)
          .with_for_update(nowait=True)
          .first()
    )
    if rule and number > rule.current_number:
        rule.current_number = number
        db.add(rule)
