from flask import Flask
from flask_restx import Api
from flask_cors import CORS
from api.income import income_ns
from api.welfare import welfare_ns
from api.health import health_ns

app = Flask(__name__)
CORS(app)
api = Api(app, version="1.0", title="LLM 기반 AI 서비스", description="소득분위 측정 + 지역 복지정보 제공")

api.add_namespace(income_ns, path='/income')
api.add_namespace(welfare_ns, path='/welfare')
api.add_namespace(health_ns, path='/health')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)