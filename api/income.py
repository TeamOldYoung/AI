from flask import request
from flask_restx import Namespace, Resource, fields
from services.incomeLLM import estimate_income_bracket

income_ns = Namespace("income", description="소득분위 측정기 API")

income_request = income_ns.model("IncomeRequest", {
    "message": fields.String(required=True, description="소득 관련 입력")
})

income_response = income_ns.model("IncomeResponse", {
    "input": fields.String,
    "response": fields.String
})



@income_ns.route("/")
class IncomePredictor(Resource):
    @income_ns.expect(income_request)
    @income_ns.marshal_with(income_response)
    def post(self):
        data = request.get_json()

        # 개별 feature 추출
        result = estimate_income_bracket(
            household_size=data["household_size"],
            annual_income=data["annual_income"],
            income_type=data["income_type"],
            housing_type=data["housing_type"],
            asset_value=data["asset_value"],
            debt_amount=data["debt_amount"],
            car_info=data["car_info"],
            has_disability=data["has_disability"],
            region=data["region"],
            employment_status=data["employment_status"],
            receives_pension=data["receives_pension"],
            past_support_recipient=data["past_support_recipient"]
        )

        return {
            "input": data,
            "response": result
        }

