# save_welfare.py
from typing import Optional, Dict, Any, Tuple, List
from AI.database.db import get_connection

def _clean(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None

def _current_columns(conn, table: str) -> List[str]:
    q = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = %s
    ORDER BY ordinal_position
    """
    with conn.cursor() as cur:
        cur.execute(q, (table,))
        return [r[0] for r in cur.fetchall()]

def save_welfare_item(city: str, item: Dict[str, Any], table: str = "welfare_item") -> int:
    """
    item 예:
    {
      "제목": "돌발영세민 보호 및 행려자 지원",
      "요약": "…",
      "바로가기": "https://…",
      "신청기관": "충청북도 증평군 행정복지국 복지지원과",
      "접수기간": "1회성 신청",
      "전화문의": "",
      "지원대상": ""
    }
    """
    # 1) 한국어 키 → 컬럼명 매핑 (부족/오타 대비해서 대체 키도 함께 체크)
    mapped = {
        "title":     _clean(item.get("제목") or item.get("title")),
        "subscript": _clean(item.get("요약") or item.get("subscript")),
        # '접수기관' 오타 대비: period에 매핑
        "period":    _clean(item.get("접수기간") or item.get("접수기관") or item.get("period")),
        "agency":    _clean(item.get("신청기관") or item.get("agency")),
        "contact":   _clean(item.get("전화문의") or item.get("contact")),
        "applicant": _clean(item.get("지원대상") or item.get("applicant")),
        "link":      _clean(item.get("바로가기") or item.get("link") or item.get("url")),
        "city": city,
    }

    if not mapped["title"]:
        raise ValueError("title(제목)은 반드시 필요합니다.")

    conn = get_connection()
    try:
        with conn:
            cols_in_db = set(_current_columns(conn, table))
            # 2) 실제 테이블에 존재하는 컬럼만 골라 INSERT
            desired_order = ["title", "subscript", "period", "agency", "contact", "applicant", "link", "city"]
            use_cols = [c for c in desired_order if c in cols_in_db]
            placeholders = ", ".join(["%s"] * len(use_cols))
            col_list = ", ".join(use_cols)

            sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) RETURNING id"
            values = [mapped[c] for c in use_cols]

            with conn.cursor() as cur:
                cur.execute(sql, values)
                new_id = cur.fetchone()[0]
                return new_id
    finally:
        conn.close()

