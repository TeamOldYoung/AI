pipeline {
    agent any

    options {
        // 최신 빌드 10개만 보존 (롤백을 위해 증가)
        buildDiscarder(logRotator(numToKeepStr: '5'))
        // 빌드 타임아웃 (30분 이상 걸리면 종료)
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        IMAGE_NAME   = "kyumin19/ai"
        IMAGE_TAG    = "${BUILD_NUMBER}"
        DOCKER_IMAGE = "${IMAGE_NAME}:${IMAGE_TAG}"
        DISCORD_WEBHOOK = credentials('discord-webhook')

        // 배포 서버 정보 (Jenkins Credentials에서 설정)
        DEPLOY_HOST = "ec2-54-180-208-86.ap-northeast-2.compute.amazonaws.com"
        DEPLOY_USER = "ubuntu"
        DEPLOY_PATH = "/srv/oldyoung"

        // 헬스체크 설정 (Flask 앱용)
        HEALTH_CHECK_URL = "http://localhost:3000"
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
                // 빌드 전 검증 (Dockerfile이 있는지 확인)
                sh '''
                    echo "🔍 빌드 환경 검증 중..."
                    ls -la
                    
                    if [ ! -f "Dockerfile" ]; then
                        echo "❌ Dockerfile이 없습니다!"
                        exit 1
                    fi
                    
                    if [ ! -f "requirements.txt" ]; then
                        echo "❌ requirements.txt가 없습니다!"
                        exit 1
                    fi
                    
                    if [ ! -f "app.py" ]; then
                        echo "❌ app.py가 없습니다!"
                        exit 1
                    fi
                    
                    echo "✅ 필수 파일 확인 완료"
                    echo "📋 requirements.txt 내용:"
                    cat requirements.txt
                '''
                
                // 커밋 정보 확보
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
                    try {
                        echo "🐳 Docker 이미지 빌드 시작: ${DOCKER_IMAGE}"
                        
                        docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-credentials') {
                            // Multi-stage Dockerfile로 이미지 빌드
                            def image = docker.build(
                                "${DOCKER_IMAGE}", 
                                "--no-cache --pull ."
                            )

                            // 빌드 번호, 커밋 해시, latest 태그 모두 푸시 (롤백을 위해)
                            echo "📤 Docker 이미지 푸시 중..."
                            image.push("${BUILD_NUMBER}")
                            image.push("${env.GIT_COMMIT_SHORT}")
                            image.push("latest")
                            
                            echo "✅ Docker 이미지 푸시 완료:"
                            echo "   - ${IMAGE_NAME}:${BUILD_NUMBER}"
                            echo "   - ${IMAGE_NAME}:${env.GIT_COMMIT_SHORT}"
                            echo "   - ${IMAGE_NAME}:latest"
                        }
                    } catch (Exception e) {
                        echo "❌ Docker 빌드/푸시 실패: ${e.getMessage()}"
                        throw e
                    }
                }
            }
        }

        stage('Pre-Deploy Check') {
            steps {
                script {
                    sshagent(credentials: ['service-server-ssh']) {
                        // 배포 전 현재 서비스 상태 확인
                        def preDeployStatus = sh(
                            script: """
                                ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                                ${DEPLOY_USER}@${DEPLOY_HOST} '
                                cd ${DEPLOY_PATH} &&
                                docker compose ps --format "table {{.Name}}\\t{{.Status}}" || echo "서비스 없음"
                                '
                            """,
                            returnStdout: true
                        ).trim()

                        echo "🔍 배포 전 서비스 상태:\\n${preDeployStatus}"

                        // 백업용 현재 이미지 태그 저장
                        env.BACKUP_IMAGE_TAG = sh(
                            script: """
                                ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                                ${DEPLOY_USER}@${DEPLOY_HOST} '
                                cd ${DEPLOY_PATH} &&
                                docker compose config | grep "image:" | grep "${IMAGE_NAME}" | cut -d":" -f3 || echo "latest"
                                '
                            """,
                            returnStdout: true
                        ).trim()

                        echo "💾 현재 이미지 태그 (롤백용): ${env.BACKUP_IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sshagent(credentials: ['service-server-ssh']) {
                        try {
                            // 1. 새 이미지 pull
                            sh """
                                ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                                ${DEPLOY_USER}@${DEPLOY_HOST} '
                                cd ${DEPLOY_PATH} &&
                                export FLASK_IMAGE=${IMAGE_NAME} &&
                                export FLASK_TAG=latest &&
                                echo "🚀 새 이미지 다운로드 중..." &&
                                docker compose pull flask-api
                                '
                            """

                            // 2. 서비스 재시작 (무중단 배포)
                            sh """
                                ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                                ${DEPLOY_USER}@${DEPLOY_HOST} '
                                cd ${DEPLOY_PATH} &&
                                export FLASK_IMAGE=${IMAGE_NAME} &&
                                export FLASK_TAG=latest &&
                                echo "🔄 서비스 재시작 중..." &&
                                docker compose up -d flask-api
                                '
                            """

                            // 3. 헬스체크 (최대 60초 대기)
                            echo "⏳ 헬스체크 시작 (최대 ${HEALTH_CHECK_TIMEOUT}초 대기)..."

                            def healthCheckResult = sh(
                                script: """
                                    ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                                    ${DEPLOY_USER}@${DEPLOY_HOST} '
                                    for i in \$(seq 1 ${HEALTH_CHECK_TIMEOUT}); do
                                        echo "헬스체크 시도 \$i/${HEALTH_CHECK_TIMEOUT}..."
                                        if docker exec flask-app curl -f --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
                                            echo "✅ 헬스체크 성공!"
                                            exit 0
                                        fi
                                        sleep 1
                                    done
                                    echo "❌ 헬스체크 실패 - 서비스가 응답하지 않습니다"
                                    exit 1
                                    '
                                """,
                                returnStatus: true
                            )

                            if (healthCheckResult != 0) {
                                error "❌ 배포 후 헬스체크 실패! 롤백이 필요합니다."
                            }

                            // 4. 최종 상태 확인
                            def finalStatus = sh(
                                script: """
                                    ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                                    ${DEPLOY_USER}@${DEPLOY_HOST} '
                                    cd ${DEPLOY_PATH} &&
                                    docker compose ps --format "table {{.Name}}\\t{{.Status}}\\t{{.Ports}}"
                                    '
                                """,
                                returnStdout: true
                            ).trim()

                            echo "✅ 배포 성공! 최종 서비스 상태:\\n${finalStatus}"

                        } catch (Exception e) {
                            echo "❌ 배포 중 오류 발생: ${e.getMessage()}"

                            // 자동 롤백 시도
                            if (env.BACKUP_IMAGE_TAG && env.BACKUP_IMAGE_TAG != "latest") {
                                echo "🔄 이전 버전으로 자동 롤백 시도: ${env.BACKUP_IMAGE_TAG}"

                                sh """
                                    ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                                    ${DEPLOY_USER}@${DEPLOY_HOST} '
                                    cd ${DEPLOY_PATH} &&
                                    export FLASK_IMAGE=${IMAGE_NAME} &&
                                    export FLASK_TAG=${env.BACKUP_IMAGE_TAG} &&
                                    docker compose up -d flask-api
                                    '
                                """
                            }

                            error "배포 실패 - 파이프라인을 중단합니다."
                        }
                    }
                }
            }
        }

        stage('Post-Deploy Verification') {
            steps {
                script {
                    sshagent(credentials: ['service-server-ssh']) {
                        // 배포 후 추가 검증
                        sh """
                            ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
                            ${DEPLOY_USER}@${DEPLOY_HOST} '
                            echo "🔍 최종 검증 중..."
                            echo "현재 실행 중인 컨테이너:"
                            docker ps --filter "name=flask-app" --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"

                            echo "\\n사용 중인 이미지:"
                            docker images ${IMAGE_NAME} --format "table {{.Repository}}\\t{{.Tag}}\\t{{.CreatedSince}}"

                            echo "\\n디스크 사용량:"
                            df -h /
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
                sendDiscordNotification("✅ 배포 성공!\\n이미지: ${DOCKER_IMAGE}\\n서버: ${DEPLOY_HOST}")
            }
        }
        failure {
            script {
                sendDiscordNotification("🚨 배포 실패!\\n빌드: #${BUILD_NUMBER}\\n서버: ${DEPLOY_HOST}")
            }
        }
        always {
            // 정리 작업
            script {
                // 로컬 Docker 이미지 정리 (디스크 공간 확보)
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
