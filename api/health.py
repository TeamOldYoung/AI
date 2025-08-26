from flask import jsonify
from flask_restx import Namespace, Resource
import os
from database.db import get_connection

health_ns = Namespace("health", description="헬스체크 API")

@health_ns.route("/")
class HealthCheck(Resource):
    def get(self):
        # 기본 헬스체크 (Jenkins 배포용)
        return {
            "status": "ok",
            "service": "OldYoung AI Service",
            "message": "Service is running"
        }, 200

@health_ns.route("/status")
class StatusCheck(Resource):
    def get(self):
        # 간단한 상태 체크 (문제 진단용)
        status = {
            "status": "healthy",
            "service": "OldYoung AI Service",
            "checks": {
                "flask": {"status": "up", "message": "Flask app running"}
            }
        }
        
        # 데이터베이스 간단 체크 (실패해도 503 반환 안함)
        try:
            conn = get_connection()
            conn.close()
            status["checks"]["database"] = {
                "status": "up",
                "message": "Database accessible"
            }
        except Exception as e:
            status["checks"]["database"] = {
                "status": "warning",
                "message": "Database connection issue"
            }

        return status, 200