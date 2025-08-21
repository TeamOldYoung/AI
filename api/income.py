from typing import Tuple, Optional, Dict, Any
from psycopg2.extras import Json

from flask import request
from flask_restx import Namespace, Resource, fields
from services.incomeLLM import estimate_income_bracket
from database.db import get_connection

income_ns = Namespace("income", description="소득분위 측정기 API")


income_request = income_ns.model("IncomeRequest", {
    "familyNum": fields.Integer(required=True, description="가구원 수"),
    "Salary": fields.Integer(required=True, description="연봉(세전)"),
    "Pension": fields.Integer(required=True, description="연금 수령액(연)"),
    "housing_type": fields.String(required=True, description="거주 형태"),
    "Asset": fields.Integer(required=True, description="자산액"),
    "Debt": fields.Integer(required=True, description="부채액"),
    "Car_info": fields.String(required=True, description="차량 정보"),
    "Disability": fields.Boolean(required=True, description="장애 여부"),
    "EmploymentStatus": fields.String(required=True, description="고용 상태"),
    "pastSupported": fields.Boolean(required=True, description="과거 지원 이력"),
})


income_response = income_ns.model("IncomeResponse", {
    "response": fields.Raw
})

def _to_int(x):
    if x is None:
        return None
    try:
        return int(x)
    except Exception:
        return None
def persist_income_records(data: Dict[str, Any], result: Dict[str, Any]) -> Tuple[int, int]:
    """
    1) incomebreaket: 입력 저장
    2) incomesnapshot: JSON 없이 개별 수치만 저장
    """
    # 결과가 {"결과 요약": {...}} 이거나 평탄화된 둘 다 지원
    summary = (result or {}).get("결과 요약", result or {})

    income_eval  = _to_int(summary.get("incomeEval"))
    asset_eval   = _to_int(summary.get("assetEval"))
    total_income = _to_int(summary.get("totalIncome"))
    mid_ratio    = _to_int(summary.get("midRatio"))
    exp_bracket  = _to_int(summary.get("expBracket"))

    if total_income is None and income_eval is not None and asset_eval is not None:
        total_income = income_eval + asset_eval

    conn = None
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                # 1) incomebreaket 저장
                cur.execute(
                    """
                    INSERT INTO incomebreaket (
                        family_num, salary, pension, housing_type,
                        asset, debt, car_info, disability,
                        employment_status, past_supported
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                    """,
                    (
                        int(data["familyNum"]),
                        int(data["Salary"]),
                        int(data["Pension"]),
                        data["housing_type"],
                        int(data["Asset"]),
                        int(data["Debt"]),
                        data["Car_info"],
                        bool(data["Disability"]),
                        data["EmploymentStatus"],
                        bool(data["pastSupported"]),
                    )
                )
                incomebreaket_id = cur.fetchone()[0]

                # 2) incomesnapshot 저장 (JSON 없이 개별 수치만)
                cur.execute(
                    """
                    INSERT INTO incomesnapshot (
                        incomebreaket_id,
                        income_eval, asset_eval, total_income, mid_ratio, exp_bracket
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        incomebreaket_id,
                        income_eval,
                        asset_eval,
                        total_income,
                        mid_ratio,
                        exp_bracket,
                    )
                )
                incomesnapshot_id = cur.fetchone()[0]

        return incomebreaket_id, incomesnapshot_id
    finally:
        if conn:
            conn.close()

@income_ns.route("/")
class IncomePredictor(Resource):
    @income_ns.expect(income_request)
    @income_ns.marshal_with(income_response)
    def post(self):
        data = request.get_json()

        # 예측 함수 호출
        result = estimate_income_bracket(
            familyNum=data["familyNum"],
            Salary=data["Salary"],
            Pension=data["Pension"],
            housing_type=data["housing_type"],
            Asset=data["Asset"],
            Debt=data["Debt"],
            Car_info=data["Car_info"],
            Disability=data["Disability"],
            EmploymentStatus=data["EmploymentStatus"],
            pastSupported=data["pastSupported"]
        )

        # 2) DB 저장
        # try:
        #     incomebreaket_id, incomesnapshot_id = persist_income_records(data, result)
        # except Exception as e:
        #     income_ns.abort(500, f"DB 저장 실패: {e}")

        # 3) 응답
        return {
            "response": {
                **result
            }
        }, 200





