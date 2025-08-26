pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        IMAGE_NAME   = "kyumin19/ai"
        IMAGE_TAG    = "${BUILD_NUMBER}"
        DOCKER_IMAGE = "${IMAGE_NAME}:${IMAGE_TAG}"
        DISCORD_WEBHOOK = credentials('discord-webhook')

        // 배포 서버 정보
        DEPLOY_HOST = "ec2-54-180-208-86.ap-northeast-2.compute.amazonaws.com"
        DEPLOY_USER = "ubuntu"
        DEPLOY_PATH = "/srv/app"

        // 헬스체크 설정
        HEALTH_CHECK_TIMEOUT = "60"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/TeamOldYoung/AI.git'
            }
        }

        stage('Build Validation') {
            steps {
                sh '''
                    echo "🔍 빌드 환경 검증 중..."
                    
                    # 필수 파일 확인
                    for file in Dockerfile requirements.txt app.py; do
                        if [ ! -f "$file" ]; then
                            echo "❌ $file이 없습니다!"
                            exit 1
                        fi
                    done
                    
                    echo "✅ 필수 파일 확인 완료"
                    echo "📋 프로젝트 구조:"
                    ls -la
                '''
                
                script {
                    env.COMMIT_INFO = sh(
                        script: "git log -1 --pretty=format:'%h | %an | %s'",
                        returnStdout: true
                    ).trim()
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                }
            }
        }

        stage('Docker Build & Push') {
            steps {
                script {
                    echo "🐳 Docker 이미지 빌드 시작: ${DOCKER_IMAGE}"
                    
                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-credentials') {
                        def image = docker.build("${DOCKER_IMAGE}", "--no-cache --pull .")

                        echo "📤 Docker 이미지 푸시 중..."
                        image.push("${BUILD_NUMBER}")
                        image.push("${env.GIT_COMMIT_SHORT}")
                        image.push("latest")
                        
                        echo "✅ Docker 이미지 푸시 완료: ${IMAGE_NAME}:latest"
                    }
                }
            }
        }

        stage('Pre-Deploy Check') {
            steps {
                script {
                    sshagent(credentials: ['service-server-ssh']) {
                        echo "🔍 배포 전 서버 상태 확인..."
                        
                        def preDeployStatus = sh(
                            script: """
                                ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                                ${DEPLOY_USER}@${DEPLOY_HOST} '
                                cd ${DEPLOY_PATH} &&
                                docker compose ps flask-api || echo "flask-api 서비스 없음"
                                '
                            """,
                            returnStdout: true
                        ).trim()

                        echo "현재 상태: ${preDeployStatus}"
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sshagent(credentials: ['service-server-ssh']) {
                        try {
                            echo "🚀 Flask AI 서비스 배포 시작..."
                            
                            // 1. 새 이미지 Pull & 서비스 재시작
                            sh """
                                ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                                ${DEPLOY_USER}@${DEPLOY_HOST} '
                                cd ${DEPLOY_PATH} &&
                                export FLASK_IMAGE=${IMAGE_NAME} &&
                                export FLASK_TAG=latest &&
                                echo "📥 새 이미지 다운로드 중..." &&
                                docker compose pull flask-api &&
                                echo "🔄 서비스 재시작 중..." &&
                                docker compose up -d flask-api
                                '
                            """

                            // 2. 헬스체크
                            echo "⏳ 헬스체크 시작 (최대 ${HEALTH_CHECK_TIMEOUT}초 대기)..."
                            
                            def healthCheckResult = sh(
                                script: """
                                    ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                                    ${DEPLOY_USER}@${DEPLOY_HOST} '
                                    for i in \$(seq 1 ${HEALTH_CHECK_TIMEOUT}); do
                                        echo "헬스체크 \$i/${HEALTH_CHECK_TIMEOUT}..."
                                        # Python으로 헬스체크 (curl 대신)
                                        if docker exec flask-app python -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:3000/health', timeout=5)
    if response.status == 200:
        exit(0)
    else:
        exit(1)
except:
    exit(1)
" > /dev/null 2>&1; then
                                            echo "✅ 헬스체크 성공!"
                                            exit 0
                                        fi
                                        sleep 1
                                    done
                                    echo "❌ 헬스체크 실패"
                                    exit 1
                                    '
                                """,
                                returnStatus: true
                            )

                            if (healthCheckResult != 0) {
                                error "❌ 헬스체크 실패! 배포 중단"
                            }

                            echo "✅ Flask AI 서비스 배포 성공!"

                        } catch (Exception e) {
                            echo "❌ 배포 실패: ${e.getMessage()}"
                            throw e
                        }
                    }
                }
            }
        }

        stage('Post-Deploy Verification') {
            steps {
                script {
                    sshagent(credentials: ['service-server-ssh']) {
                        sh """
                            ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                            ${DEPLOY_USER}@${DEPLOY_HOST} '
                            echo "🔍 최종 상태 확인..."
                            echo "=== 컨테이너 상태 ==="
                            docker ps --filter "name=flask-app" --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
                            
                            echo "\\n=== 서비스 응답 테스트 ==="
                            curl -s http://localhost:3000/health | head -3 || echo "응답 없음"
                            
                            echo "\\n=== 디스크 사용량 ==="
                            df -h / | tail -1
                            '
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                sendDiscordNotification("✅ Flask AI 배포 성공!\\n이미지: ${DOCKER_IMAGE}\\n서버: ${DEPLOY_HOST}")
            }
        }
        failure {
            script {
                sendDiscordNotification("🚨 Flask AI 배포 실패!\\n빌드: #${BUILD_NUMBER}\\n브랜치: main")
            }
        }
        always {
            script {
                sh '''
                    docker system prune -f || echo "Docker 정리 실패"
                    docker image prune -f || echo "Docker 이미지 정리 실패"
                '''
            }
            cleanWs()
        }
    }
}

def sendDiscordNotification(String message) {
    def commitInfo = (env.COMMIT_INFO ?: "정보 없음").replace('"', '\\"')
    def fullMessage = "${message}\\n커밋: ${commitInfo}\\n시간: ${new Date().format('yyyy-MM-dd HH:mm:ss')}"

    withCredentials([string(credentialsId: 'discord-webhook', variable: 'WEBHOOK_URL')]) {
        sh """
            curl -s -X POST "\${WEBHOOK_URL}" \
            -H "Content-Type: application/json" \
            -d '{"content": "${fullMessage}"}' || echo "Discord 알림 실패"
        """
    }
}