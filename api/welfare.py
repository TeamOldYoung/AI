from flask import request
from flask_restx import Namespace, Resource, fields
from services.welfareLLM import summarize_welfare_info
from services.welfareAPI import fetch_welfare_info
# namespace 직접 생성
welfare_ns = Namespace("welfare", description="지역 복지 정보 검색 API")

# 요청 모델 정의
welfare_request = welfare_ns.model("WelfareRequest", {
    "age(bool)": fields.Integer(required=True, description="나이 플래그 (0=유아/청소년, 1=노년)", enum=[0, 1]),
    "city": fields.String(required=True, description="지역명 (예: 강남구, 마포구 등)")
})

# 응답 모델 정의
# welfare_response = welfare_ns.model("WelfareResponse", {
#     "info": fields.Raw
# })

welfare_response = welfare_ns.model("WelfareResponse", {
    "info": fields.Raw
})

# 엔드포인트 클래스 정의
@welfare_ns.route("/")
class WelfareSearch(Resource):
    @welfare_ns.expect(welfare_request)
    @welfare_ns.marshal_with(welfare_response)
    def post(self):
        data = request.get_json()
        age = data.get("age")
        city = data.get("city")

        # 복지정보 검색 처리
        info = fetch_welfare_info(age, city)

        return {
            "info": info
        }



