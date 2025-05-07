# scheduled_reports.py
import os
import sys
import argparse
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.api.naver_insight import query_multiple_data, get_recent_timestamps
from modules.reports.visualizer import MetricsVisualizer
from modules.utils.logger import setup_logger
from modules.utils.config_loader import load_all_configs

def generate_site_report(site_name, site_config, days=7):
    """
    특정 사이트에 대한 보고서 생성
    
    Args:
        site_name (str): 사이트 ID
        site_config (dict): 사이트 설정 정보
        days (int): 조회할 일수
    
    Returns:
        bool: 성공 여부
    """
    logger = setup_logger()
    logger.info(f"사이트 '{site_name}' 보고서 생성 시작")
    
    # 사이트 정보 추출
    site_display_name = site_config.get('name', site_name)
    ncp_config = site_config.get('ncp', {})
    servers = site_config.get('servers', [])
    
    # NCP 인증 정보
    access_key = ncp_config.get('access_key')
    secret_key = ncp_config.get('secret_key')
    cw_key = ncp_config.get('cw_key')
    
    if not (access_key and secret_key and cw_key):
        logger.error(f"사이트 '{site_display_name}'의 NCP 인증 정보가 불완전합니다.")
        return False
    
    if not servers:
        logger.warning(f"사이트 '{site_display_name}'에 등록된 서버가 없습니다.")
        return False
    
    # 설정 로드
    configs = load_all_configs()
    
    # 메트릭 정보 로드
    metrics_config = configs.get('metrics', {})
    metrics_info = metrics_config.get('metrics', [])
    
    # 일반 설정 로드
    settings_config = configs.get('settings', {})
    general_config = settings_config.get('general', {})
    report_config = settings_config.get('report', {})
    interval_config = settings_config.get('interval', {})
    aggregation_config = settings_config.get('aggregation', {})
    
    # 기본값 설정
    interval = interval_config.get('default', 'Min5')
    aggregation = aggregation_config.get('default', 'AVG')
    
    # 출력 디렉토리
    output_dir = general_config.get('output_dir', 'output')
    
    # 시각화 도구 초기화
    visualizer = MetricsVisualizer(output_dir=output_dir)
    
    # 보고서 생성 시간
    report_time = datetime.now()
    report_timestamp = report_time.strftime('%Y%m%d_%H%M%S')
    
    # 보고서 디렉토리
    report_dir = os.path.join(output_dir, site_name, f"report_{report_timestamp}")
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    # 성공 카운터
    success_count = 0
    
    # 메트릭 키 목록
    metric_keys = [metric.get('key') for metric in metrics_info if metric.get('key')]
    
    # 최근 일정 기간 시작/종료 타임스탬프
    start_time, end_time = get_recent_timestamps(days=days)
    
    # 각 서버에 대해 데이터 가져오기 및 그래프 생성
    for server in servers:
        server_id = server.get('id')
        server_name = server.get('name')
        
        if not (server_id and server_name):
            logger.warning(f"서버 정보가 불완전합니다: {server}")
            continue
        
        logger.info(f"서버 '{server_name}' 데이터 처리 시작")
        
        try:
            # 여러 메트릭 데이터 한 번에 가져오기
            result = query_multiple_data(
                access_key=access_key,
                secret_key=secret_key,
                metrics=metric_keys,
                dimension_key="vm_name",
                dimension_value=server_name,
                start_time=start_time,
                end_time=end_time,
                cw_key=cw_key,
                interval=interval,
                aggregation=aggregation
            )
            
            if result:
                logger.info(f"데이터 조회 성공: {len(result)} 메트릭 데이터")
                
                # 서버별 디렉토리 생성
                server_dir = os.path.join(report_dir, server_name.replace(' ', '_'))
                if not os.path.exists(server_dir):
                    os.makedirs(server_dir)
                
                # 데이터 검증 - 빈 메트릭 제거
                valid_metrics = []
                for metric_data in result:
                    if metric_data and 'dps' in metric_data and metric_data['dps']:
                        valid_metrics.append(metric_data)
                    else:
                        metric_name = metric_data.get('metric', 'unknown')
                        logger.warning(f"서버 '{server_name}'의 '{metric_name}' 메트릭에 데이터가 없습니다.")
                
                if valid_metrics:
                    # 개별 메트릭 그래프 생성
                    for metric_data in valid_metrics:
                        metric_key = metric_data.get('metric', '')
                        
                        # 메트릭 정의 정보 조회
                        metric_info = next((m for m in metrics_info if m.get('key') == metric_key), {})
                        metric_name = metric_info.get('name', metric_key)
                        unit = metric_info.get('unit', '')
                        threshold_warning = metric_info.get('threshold_warning')
                        threshold_critical = metric_info.get('threshold_critical')
                        
                        # 데이터프레임 생성
                        df = visualizer.create_metric_dataframe(metric_data)
                        
                        if df is not None and not df.empty:
                            # 그래프 생성
                            fig = visualizer.plot_metric(df, metric_name, unit, threshold_warning, threshold_critical)
                            
                            # 파일명 생성
                            filename = f"{metric_key}.png"
                            filepath = os.path.join(server_dir, filename)
                            
                            # 그래프 저장
                            if fig:
                                fig.savefig(filepath, dpi=100)
                                plt.close(fig)
                                logger.info(f"그래프 저장 완료: {filepath}")
                    
                    # 대시보드 생성
                    dashboard_file = os.path.join(server_dir, "dashboard.png")
                    dashboard = visualizer.create_dashboard(
                        site_name=site_display_name,
                        server_name=server_name,
                        metrics_data=valid_metrics,
                        metrics_info=metrics_info
                    )
                    
                    if dashboard:
                        logger.info(f"대시보드 생성 완료: {dashboard_file}")
                    
                    success_count += 1
                    logger.info(f"서버 '{server_name}' 보고서 생성 완료")
                else:
                    logger.error(f"서버 '{server_name}'의 모든 메트릭에 데이터가 없습니다.")
            else:
                logger.error(f"서버 '{server_name}' 데이터 조회 실패")
        
        except Exception as e:
            logger.error(f"서버 '{server_name}' 데이터 처리 중 오류 발생: {str(e)}")
    
    # 요약 정보
    summary = {
        "사이트": site_display_name,
        "보고서 생성 시간": report_time.strftime('%Y-%m-%d %H:%M:%S'),
        "조회 기간": f"{days}일",
        "조회 시작": datetime.fromtimestamp(start_time/1000).strftime('%Y-%m-%d %H:%M:%S'),
        "조회 종료": datetime.fromtimestamp(end_time/1000).strftime('%Y-%m-%d %H:%M:%S'),
        "서버 수": len(servers),
        "성공 서버 수": success_count,
        "실패 서버 수": len(servers) - success_count
    }
    
    # 요약 정보 저장
    summary_file = os.path.join(report_dir, "summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")
    
    logger.info(f"사이트 '{site_display_name}' 보고서 생성 완료. 성공: {success_count}, 실패: {len(servers) - success_count}")
    return success_count > 0

def main():
    """
    메인 함수
    """
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description='네이버 클라우드 인사이트 보고서 자동화 도구')
    parser.add_argument('--site', help='특정 사이트 ID (입력하지 않으면 모든 사이트 처리)')
    parser.add_argument('--days', type=int, default=7, help='조회할 일수 (기본값: 7)')
    
    args = parser.parse_args()
    
    # 로거 설정
    logger = setup_logger()
    logger.info("예약 보고서 생성 시작")
    
    # 설정 파일 로드
    configs = load_all_configs()
    
    # 사이트 설정 가져오기
    sites_config = configs.get('sites', {})
    sites = sites_config.get('sites', {})
    
    if not sites:
        logger.error("등록된 사이트가 없습니다. sites.yaml 파일을 확인하세요.")
        return 1
    
    success_count = 0
    
    # 특정 사이트만 처리하는 경우
    if args.site:
        if args.site in sites:
            logger.info(f"사이트 '{args.site}' 처리 중...")
            if generate_site_report(args.site, sites[args.site], days=args.days):
                success_count += 1
        else:
            logger.error(f"사이트 '{args.site}'을(를) 찾을 수 없습니다.")
    else:
        # 모든 사이트 처리
        for site_name, site_config in sites.items():
            logger.info(f"사이트 '{site_name}' 처리 중...")
            if generate_site_report(site_name, site_config, days=args.days):
                success_count += 1
    
    logger.info(f"보고서 생성 완료. 성공 사이트: {success_count}, 실패 사이트: {len(sites) - success_count if not args.site else (0 if success_count > 0 else 1)}")
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    # matplotlib 경고 무시
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # matplotlib 설정
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    
    # 실행
    sys.exit(main())