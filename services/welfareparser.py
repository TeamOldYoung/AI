import xml.etree.ElementTree as ET
import html
import json
import re
from typing import List, Dict, Any

def _txt(elem: ET.Element, tag: str) -> str:
    node = elem.find(tag)
    if node is None or node.text is None:
        return ""
    return html.unescape(node.text).strip()

def _split_csv(s: str) -> list[str]:
    return [t.strip() for t in s.split(",") if t.strip()] if s else []

def _to_iso_yyyymmdd(s: str) -> str:
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if s and re.fullmatch(r"\d{8}", s) else (s or "")

def parse_and_format_cards(xml_text: str) -> List[Dict[str, Any]]:
    """
    LcgvWelfarelist XML -> 카드형 JSON 리스트
    """
    root = ET.fromstring(xml_text)
    cards = []

    for it in root.findall(".//servList"):
        title = _txt(it, "servNm")
        summary = _txt(it, "servDgst")
        link = _txt(it, "servDtlLink")

        # 신청기관: 우선 bizChrDeptNm, 없으면 관할부서/기관명 후보 사용
        apply_agency = (
            _txt(it, "bizChrDeptNm")
            or _txt(it, "jurMnofNm")
            or _txt(it, "jurOrgNm")
        )

        # 접수기간: sprtCycNm → “상시 신청”/“<값> 신청”
        cyc = _txt(it, "sprtCycNm")
        if cyc in ("상시", "수시"):
            application_period = "상시 신청"
        elif cyc:
            application_period = f"{cyc} 신청"
        else:
            application_period = ""

        phone = _txt(it, "inqrTelNo")

        # 지원대상: 배열 우선, 단일 필드 대체
        targets_csv = _txt(it, "trgterIndvdlNmArray")
        eligibility = ", ".join(_split_csv(targets_csv)) or _txt(it, "trgterIndvdlNm")

        # 카드 JSON 한 건
        card = {
            "제목": title,
            "요약": summary,
            "바로가기": link,
            "신청기관": apply_agency,
            "접수기간": application_period,
            "전화문의": phone,
            "지원대상": eligibility,
            # 참고로 지역 정보가 필요하면 추가
            "지역": {
                "시도": _txt(it, "ctpvNm"),
                "시군구": _txt(it, "sggNm"),
            },
            # 필요시 다른 부가 정보도 덧붙일 수 있음
            "마지막수정일": _to_iso_yyyymmdd(_txt(it, "lastModYmd")),
        }
        cards.append(card)

    return cards
