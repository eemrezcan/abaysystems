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
    start_number: Optional[int] = None,
    reset_sequence: Optional[bool] = False,   # ✅ eklendi
) -> ProjectCodeRule:
    """
    - start_number sadece ALT LİMİT mantığıdır.
    - reset_sequence=True ise sayaç (current_number), etkili start_number - 1'e çekilir.
      Ledger TEMİZLENMEZ; dolayısıyla daha önce kullanılmış numaralar yine atlanır.
    """
    if prefix is not None:
        rule.prefix = prefix
    if separator is not None:
        rule.separator = separator
    if start_number is not None:
        rule.start_number = start_number
        # current_number'ı geriye çekmeyiz (default davranış); çok gerideyse ileri alırız
        if rule.current_number < start_number - 1:
            rule.current_number = start_number - 1

    # ✅ İsteğe bağlı sayaç reseti
    if reset_sequence:
        # Etkili alt limit: (gönderilen start_number varsa o, yoksa mevcut rule.start_number)
        effective_start = start_number if start_number is not None else rule.start_number
        # Sayaç, alt limitin 1 eksiğine çekilir
        rule.current_number = max(effective_start - 1, 0)

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
    Ledger'da kullanılan sayıları ve AYNI OWNER'a ait projelerdeki çakışmaları atlayarak
    start_number alt sınırından sonraki ilk boş sayıyı bulur.
    (Race koşullarında sapabilir; yalnızca gösterim içindir.)
    """
    rule = (
        db.query(ProjectCodeRule)
          .filter(ProjectCodeRule.owner_id == owner_id)
          .first()
    )
    if not rule or not rule.is_active:
        raise ValueError("Önce proje kodu kuralınızı oluşturun.")

    candidate_num = max(rule.current_number + 1, rule.start_number)
    sep = getattr(rule, "separator", "-")
    pad = getattr(rule, "padding", 0)  # padding kolonu kaldırılmış olabilir; güvenli oku

    while True:
        candidate_code = _format_code(rule.prefix, candidate_num, sep, pad)

        # 1) Ledger'da bu sayı bu owner için kullanılmış mı?
        exists_in_ledger = (
            db.query(ProjectCodeLedger.number)
              .filter(
                  ProjectCodeLedger.owner_id == owner_id,
                  ProjectCodeLedger.number == candidate_num,
              )
              .first()
        )

        # 2) AYNI OWNER'ın projelerinde bu kod var mı?
        #    Projenizde kiracı/owner kolonu farklı ise burayı uyarlayın (örn. Project.owner_id == owner_id).
        exists_in_project_same_owner = (
            db.query(Project.id)
              .filter(
                  Project.project_kodu == candidate_code,
                  Project.created_by == owner_id,   # <-- gerekirse doğru tenant sütununa çevirin
              )
              .first()
        )

        if not exists_in_ledger and not exists_in_project_same_owner:
            break

        candidate_num += 1

    return candidate_num, candidate_code


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

    pad = getattr(rule, "padding", 0)  # kaldırılmış olabilir; güvenli oku
    sep = getattr(rule, "separator", "-")

    next_number = max(rule.current_number + 1, rule.start_number)

    while True:
        candidate = _format_code(rule.prefix, next_number, sep, pad)

        # 1) Ledger'da aynı (owner, number) kullanılmış mı?
        exists_in_ledger = (
            db.query(ProjectCodeLedger.number)
              .filter(
                  ProjectCodeLedger.owner_id == owner_id,
                  ProjectCodeLedger.number == next_number,
              )
              .first()
        )

        # 2) AYNI SAHİPTE proje tablosunda aynı kod var mı?
        #    NOT: Proje modelinde kiracı/sahip alanınız farklıysa (örn. owner_id),
        #    aşağıdaki 'Project.created_by == owner_id' koşulunu ona göre değiştirin.
        exists_in_project_same_owner = (
            db.query(Project.id)
              .filter(
                  Project.project_kodu == candidate,
                  Project.created_by == owner_id,   # <-- gerekirse owner sütununuza uyarlayın
              )
              .first()
        )

        # Eğer ledger ve aynı owner’ın projeleri açısından boşsa bu numarayı kullan
        if not exists_in_ledger and not exists_in_project_same_owner:
            break

        # Aksi halde bir sonrakine geç
        next_number += 1

    # Sadece rule.current_number'ı ileri al (COMMIT dışarıda)
    rule.current_number = next_number
    db.add(rule)
    return next_number, candidate


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

# app/crud/project_code.py — YENİ yardımcı
def get_or_create_default_rule(db: Session, owner_id: UUID) -> ProjectCodeRule:
    """
    Owner için bir ProjectCodeRule yoksa, varsayılan kuralı oluşturur:
      prefix="PROFORMA", separator="-", start_number=1, current_number=0
    Varsa mevcut kuralı döner.
    """
    rule = get_rule_by_owner(db, owner_id)
    if rule:
        return rule

    # Varsayılan kural: PROFORMA-1'den başlat (current_number = start_number - 1)
    return create_rule(
        db,
        owner_id=owner_id,
        prefix="PROFORMA",
        separator="-",
        start_number=1,
    )
