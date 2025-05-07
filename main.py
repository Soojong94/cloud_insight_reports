# main.py
import os
import sys
import json
from datetime import datetime
import pandas as pd

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.api.naver_insight import query_data, query_multiple_data, get_timestamps_for_april_2024, get_recent_timestamps
from modules.utils.logger import setup_logger
from modules.utils.config_loader import load_all_configs

def fetch_recent_data(access_key, secret_key, cw_key, server_id, server_name, days=7):
    """
    최근 데이터 가져오기 테스트 함수
    """
    logger = setup_logger()
    logger.info(f"서버 '{server_name}' ({server_id})의 최근 {days}일 데이터 가져오기 시작")
    
    # 최근 일정 기간 시작/종료 타임스탬프
    start_time, end_time = get_recent_timestamps(days)
    
    # 메트릭 목록 - 정확한 메트릭 이름 사용
    metrics = ["CpuUtilization", "MemoryUsage", "DiskReadBytes", 
               "DiskWriteBytes", "NetworkInbound", "NetworkOutbound"]
    
    try:
        # 메트릭 조회 시도
        logger.info(f"메트릭 데이터 조회: {metrics}")
        
        # 여러 메트릭 데이터 한 번에 가져오기
        result = query_multiple_data(
            access_key=access_key,
            secret_key=secret_key,
            metrics=metrics,
            dimension_key="vm_name",
            dimension_value=server_name,
            start_time=start_time,
            end_time=end_time,
            cw_key=cw_key,
            interval="Min5",
            aggregation="AVG"
        )
        
        logger.info(f"데이터 조회 성공: {len(result) if result else 0} 메트릭 데이터")
        # 전체 응답 로깅 부분 제거
        
        # 데이터 프레임으로 변환하여 출력
        for metric_data in result:
            metric_name = metric_data.get('metric', 'unknown')
            data_points = metric_data.get('dps', [])
            
            if data_points:
                df = pd.DataFrame(data_points, columns=['timestamp', 'value'])
                df['datetime'] = df['timestamp'].apply(lambda x: datetime.fromtimestamp(x/1000))
                
                logger.info(f"메트릭: {metric_name}, 데이터 포인트: {len(data_points)}")
                
                # 마지막 5개 데이터 포인트만 출력
                if len(data_points) > 5:
                    logger.info(f"마지막 5개 데이터 포인트: \n{df.tail().to_string()}")
                else:
                    logger.info(f"데이터 포인트: \n{df.to_string()}")
            else:
                logger.warning(f"메트릭 {metric_name}에 대한 데이터가 없습니다.")
        
        return result
    
    except Exception as e:
        logger.error(f"데이터 조회 중 오류 발생: {str(e)}")
        return None

def process_site(site_config):
    """
    사이트 설정을 처리하여 데이터 가져오기
    """
    logger = setup_logger()
    
    # 사이트 정보 추출
    site_name = site_config.get('name', 'Unknown Site')
    ncp_config = site_config.get('ncp', {})
    servers = site_config.get('servers', [])
    
    # NCP 인증 정보
    access_key = ncp_config.get('access_key')
    secret_key = ncp_config.get('secret_key')
    cw_key = ncp_config.get('cw_key')
    
    if not (access_key and secret_key and cw_key):
        logger.error(f"사이트 '{site_name}'의 NCP 인증 정보가 불완전합니다.")
        return False
    
    if not servers:
        logger.warning(f"사이트 '{site_name}'에 등록된 서버가 없습니다.")
        return False
    
    success_count = 0
    
    # 각 서버에 대해 데이터 가져오기
    for server in servers:
        server_id = server.get('id')
        server_name = server.get('name')
        
        if not (server_id and server_name):
            logger.warning(f"서버 정보가 불완전합니다: {server}")
            continue
        
        logger.info(f"사이트: {site_name}, 서버: {server_name} 데이터 처리 시작")
        
        # 데이터 가져오기 (4월 데이터 대신 최근 데이터로 변경)
        result = fetch_recent_data(access_key, secret_key, cw_key, server_id, server_name, days=7)
        
        if result:
            success_count += 1
            logger.info(f"서버 '{server_name}' 데이터 처리 완료")
        else:
            logger.error(f"서버 '{server_name}' 데이터 처리 실패")
    
    logger.info(f"사이트 '{site_name}' 처리 완료. 성공: {success_count}, 실패: {len(servers) - success_count}")
    return success_count > 0

if __name__ == "__main__":
    # 설정 파일 로드
    configs = load_all_configs()
    
    # 사이트 설정 가져오기
    sites_config = configs.get('sites', {})
    sites = sites_config.get('sites', {})
    
    if not sites:
        print("등록된 사이트가 없습니다. sites.yaml 파일을 확인하세요.")
        sys.exit(1)
    
    # 특정 사이트만 처리하는 경우
    site_name = None
    if len(sys.argv) > 1:
        site_name = sys.argv[1]
    
    success_count = 0
    
    # 모든 사이트 또는 특정 사이트 처리
    if site_name:
        if site_name in sites:
            print(f"사이트 '{site_name}' 처리 중...")
            if process_site(sites[site_name]):
                success_count += 1
        else:
            print(f"사이트 '{site_name}'을(를) 찾을 수 없습니다.")
    else:
        # 모든 사이트 처리
        for site_name, site_config in sites.items():
            print(f"사이트 '{site_name}' 처리 중...")
            if process_site(site_config):
                success_count += 1
    
    print(f"처리 완료. 성공 사이트: {success_count}, 실패 사이트: {len(sites) - success_count if not site_name else (0 if success_count > 0 else 1)}")