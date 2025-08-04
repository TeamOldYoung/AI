from flask import request
from flask_restx import Namespace, Resource, fields
from services.welfareLLM import summarize_welfare_info

# namespace 직접 생성
welfare_ns = Namespace("welfare", description="지역 복지 정보 검색 API")

# 요청 모델 정의
welfare_request = welfare_ns.model("WelfareRequest", {
    "region": fields.String(required=True, description="지역명 (예: 강남구, 마포구 등)")
})

# 응답 모델 정의
welfare_response = welfare_ns.model("WelfareResponse", {
    "region": fields.String,
    "info": fields.String
})

# 엔드포인트 클래스 정의
@welfare_ns.route("/")
class WelfareSearch(Resource):
    @welfare_ns.expect(welfare_request)
    @welfare_ns.marshal_with(welfare_response)
    def post(self):
        data = request.get_json()
        region = data.get("region")

        # 복지정보 검색 처리
        info = f"{region} 지역의 아동 복지센터, 청년 지원사업 정보를 검색했습니다."  # TODO: 웹 검색/RAG로 대체
        info = summarize_welfare_info(region)

        return {
            "region": region,
            "info": info
        }
