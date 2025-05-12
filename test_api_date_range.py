# test_api_date_range.py
import os
import sys
from datetime import datetime
from modules.api.naver_insight import query_multiple_data
from modules.utils.config_loader import load_all_configs
from modules.utils.logger import setup_logger

def test_date_range_api(start_date_str, end_date_str, site_name=None):
    """
    특정 날짜 범위의 API 응답을 테스트
    
    Args:
        start_date_str (str): 시작 날짜 (YYYY-MM-DD 형식)
        end_date_str (str): 종료 날짜 (YYYY-MM-DD 형식)
        site_name (str, optional): 특정 사이트 이름
    """
    # 로거 설정
    logger = setup_logger()
    logger.info(f"API 테스트 시작: {start_date_str} ~ {end_date_str}")
    
    # 설정 파일 로드
    configs = load_all_configs()
    
    # 사이트 설정 가져오기
    sites_config = configs.get('sites', {})
    sites = sites_config.get('sites', {})
    
    # 메트릭 정보 로드
    metrics_config = configs.get('metrics', {})
    metrics_info = metrics_config.get('metrics', [])
    
    # 메트릭 키 목록
    metric_keys = [metric.get('key') for metric in metrics_info if metric.get('key')]
    
    # 날짜 문자열을 datetime 객체로 변환
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    end_date = end_date.replace(hour=23, minute=59, second=59)
    
    # Unix timestamp (밀리초 단위)로 변환
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    # 처리할 사이트 목록
    target_sites = {site_name: sites[site_name]} if site_name and site_name in sites else sites
    
    for site_name, site_config in target_sites.items():
        logger.info(f"사이트 '{site_name}' API 테스트")
        
        # 사이트 정보 추출
        ncp_config = site_config.get('ncp', {})
        servers = site_config.get('servers', [])
        
        # NCP 인증 정보
        access_key = ncp_config.get('access_key')
        secret_key = ncp_config.get('secret_key')
        cw_key = ncp_config.get('cw_key')
        
        if not (access_key and secret_key and cw_key):
            logger.error(f"사이트 '{site_name}'의 NCP 인증 정보가 불완전합니다.")
            continue
        
        # 첫 번째 서버에 대해서만 테스트
        if servers:
            server = servers[0]
            server_name = server.get('name')
            
            logger.info(f"서버 '{server_name}' 데이터 요청 중...")
            
            try:
                # API 호출
                result = query_multiple_data(
                    access_key=access_key,
                    secret_key=secret_key,
                    metrics=metric_keys,
                    dimension_key="vm_name",
                    dimension_value=server_name,
                    start_time=start_timestamp,
                    end_time=end_timestamp,
                    cw_key=cw_key,
                    interval="Min5",
                    aggregation="AVG"
                )
                
                if result:
                    logger.info(f"API 응답 성공: {len(result)} 메트릭")
                    
                    # 데이터 포인트 수 확인
                    for metric_data in result:
                        metric_name = metric_data.get('metric', 'unknown')
                        dps = metric_data.get('dps', [])
                        
                        if dps:
                            # 실제 데이터 범위 확인
                            timestamps = [dp[0] for dp in dps]
                            first_ts = min(timestamps)
                            last_ts = max(timestamps)
                            
                            first_date = datetime.fromtimestamp(first_ts/1000).strftime('%Y-%m-%d %H:%M:%S')
                            last_date = datetime.fromtimestamp(last_ts/1000).strftime('%Y-%m-%d %H:%M:%S')
                            
                            logger.info(f"메트릭: {metric_name}, 데이터 포인트: {len(dps)}")
                            logger.info(f"실제 데이터 범위: {first_date} ~ {last_date}")
                            
                            # 요청 범위와 실제 데이터 범위 비교
                            if datetime.fromtimestamp(first_ts/1000).date() > start_date.date() or \
                               datetime.fromtimestamp(last_ts/1000).date() < end_date.date():
                                logger.warning(f"실제 데이터 범위가 요청 범위와 다릅니다!")
                                logger.warning(f"요청 범위: {start_date_str} ~ {end_date_str}")
                        else:
                            logger.warning(f"메트릭 {metric_name}에 데이터가 없습니다.")
                else:
                    logger.error("API 응답이 비어있습니다.")
            
            except Exception as e:
                logger.error(f"API 호출 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    # 날짜 형식: YYYY-MM-DD
    if len(sys.argv) < 3:
        print("사용법: python test_api_date_range.py 시작날짜 종료날짜 [사이트명]")
        print("예: python test_api_date_range.py 2025-01-01 2025-01-31 site1")
        sys.exit(1)
    
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    site_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    test_date_range_api(start_date, end_date, site_name)