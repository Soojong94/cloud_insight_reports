# Cloud Insight Reports

네이버 클라우드 인사이트의 메트릭 데이터를 활용한 보고서 자동화 시스템

## 소개

이 프로젝트는 KT 클라우드에서 네이버 클라우드 인사이트로 전송된 서버 메트릭 데이터를 조회하고 분석하는 자동화 시스템입니다. 여러 고객사 사이트의 서버 성능 데이터를 효율적으로 모니터링하고 관리할 수 있습니다.

## 기능

- 여러 사이트 및 서버의 메트릭 데이터 일괄 조회
- CPU, 메모리, 디스크, 네트워크 사용량 등 다양한 메트릭 분석
- YAML 기반 설정 관리로 쉬운 사이트 및 서버 추가
- 최근 기간 또는 특정 기간 데이터 조회 지원

## 설치 방법


# 저장소 클론

cd cloud_insight_reports

# 필요한 패키지 설치
pip install -r requirements.txt
```

## 설정 방법

1. config 디렉토리의 예시 파일을 복사하여 실제 파일을 생성합니다:
   
   cp config/settings.yaml.example config/settings.yaml
   cp config/sites.yaml.example config/sites.yaml
   cp config/metrics.yaml.example config/metrics.yaml
   ```

2. 복사한 파일들에 실제 접근 정보와 설정을 입력합니다.
   - `settings.yaml`: 일반 설정, 로깅 레벨, 보고서 형식 등 설정
   - `sites.yaml`: 사이트 및 서버 정보, API 접근 키 설정
   - `metrics.yaml`: 메트릭 정의 및 임계치 설정

## 사용 방법

### 모든 사이트 데이터 조회


python main.py
```

### 특정 사이트만 데이터 조회


python main.py site1
```

### 예약 보고서 생성


python scheduled_reports.py
```

## 프로젝트 구조

- `config/`: 설정 파일 디렉토리
  - `settings.yaml`: 일반 설정
  - `sites.yaml`: 사이트 및 서버 정보
  - `metrics.yaml`: 메트릭 정의
- `modules/`: 모듈 디렉토리
  - `api/`: API 호출 관련 모듈
    - `kt_cloud.py`: KT 클라우드 API 모듈
    - `naver_insight.py`: 네이버 클라우드 인사이트 API 모듈
    - `utils.py`: API 유틸리티 모듈
  - `reports/`: 보고서 관련 모듈
    - `data_processor.py`: 데이터 처리 모듈
    - `visualizer.py`: 시각화 모듈
    - `pdf_generator.py`: PDF 생성 모듈
  - `utils/`: 유틸리티 모듈
    - `logger.py`: 로깅 모듈
    - `config_loader.py`: 설정 로더 모듈
- `templates/`: 보고서 템플릿
- `main.py`: 메인 실행 파일
- `scheduled_reports.py`: 예약 보고서 실행 파일

## 확장 방법

새로운 사이트나 서버를 추가하려면 `sites.yaml` 파일을 수정하면 됩니다. 형식은 다음과 같습니다:

```yaml
sites:
  site_id:
    name: "사이트 이름"
    kt_cloud:
      username: "사용자명"
      password: "비밀번호"
    ncp:
      access_key: "액세스 키"
      secret_key: "시크릿 키"
      cw_key: "CW 키"
    servers:
      - id: "서버 ID"
        name: "서버 이름"
      - id: "서버 ID"
        name: "서버 이름"
```
