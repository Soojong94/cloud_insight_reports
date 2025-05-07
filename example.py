# 사용 예제: 전체 프로세스를 보여주는 코드
# 아래 코드는 scheduled_reports.py 파일에 추가하거나 별도의 파일로 만들어서 사용할 수 있습니다.

import os
import sys
import argparse
from datetime import datetime

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.api.naver_insight import query_multiple_data, get_recent_timestamps
from modules.reports.visualizer import MetricsVisualizer
from modules.reports.data_processor import MetricsDataProcessor
from modules.reports.pdf_generator import ReportGenerator
from modules.utils.logger import setup_logger
from modules.utils.config_loader import load_all_configs

def generate_comprehensive_report(site_name, site_config, days=7):
    """
    사이트에 대한 종합 보고서 생성 (시각화, 데이터 분석, PDF 생성 포함)
    """
    logger = setup_logger()
    logger.info(f"사이트 '{site_name}' 종합 보고서 생성 시작")
    
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
    interval_config = settings_config.get('interval', {})
    aggregation_config = settings_config.get('aggregation', {})
    
    # 기본값 설정
    interval = interval_config.get('default', 'Min5')
    aggregation = aggregation_config.get('default', 'AVG')
    output_dir = general_config.get('output_dir', 'output')
    
    # 도구 초기화
    visualizer = MetricsVisualizer(output_dir=output_dir)
    data_processor = MetricsDataProcessor()
    report_generator = ReportGenerator(output_dir=output_dir)
    
    # 보고서 생성 시간
    report_time = datetime.now()
    report_timestamp = report_time.strftime('%Y%m%d_%H%M%S')
    
    # 보고서 디렉토리
    report_dir = os.path.join(output_dir, site_name, f"report_{report_timestamp}")
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    # 메트릭 키 목록
    metric_keys = [metric.get('key') for metric in metrics_info if metric.get('key')]
    
    # 최근 일정 기간 시작/종료
    start_time, end_time = get_recent_timestamps(days=days)
    
    # 서버별 데이터 저장
    servers_data = {}
    
    # 각 서버에 대해 처리
    for server in servers:
        server_id = server.get('id')
        server_name = server.get('name')
        
        if not (server_id and server_name):
            logger.warning(f"서버 정보가 불완전합니다: {server}")
            continue
        
        logger.info(f"서버 '{server_name}' 데이터 처리 시작")
        
        try:
            # 1. 데이터 조회
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
            
            if not result:
                logger.error(f"서버 '{server_name}' 데이터 조회 실패")
                continue
                
            logger.info(f"데이터 조회 성공: {len(result)} 메트릭 데이터")
            
            # 서버별 디렉토리 생성
            server_dir = os.path.join(report_dir, server_name.replace(' ', '_'))
            if not os.path.exists(server_dir):
                os.makedirs(server_dir)
            
            # 2. 데이터 분석
            metrics_analysis = data_processor.analyze_multiple_metrics(result, metrics_info)
            logger.info(f"데이터 분석 완료: {len(metrics_analysis)} 메트릭 분석됨")
            
            # 3. 시각화
            # 3.1. 개별 메트릭 그래프
            graph_files = visualizer.visualize_all_metrics(
                site_name=site_display_name,
                server_name=server_name,
                metrics_data=result,
                metrics_info=metrics_info
            )
            logger.info(f"그래프 생성 완료: {len(graph_files)}개")
            
            # 3.2. 대시보드
            dashboard_file = visualizer.create_dashboard(
                site_name=site_display_name,
                server_name=server_name,
                metrics_data=result,
                metrics_info=metrics_info
            )
            if dashboard_file:
                logger.info(f"대시보드 생성 완료: {dashboard_file}")
            
            # 4. 서버별 PDF 보고서 생성
            pdf_file = report_generator.generate_server_report(
                site_name=site_display_name,
                server_name=server_name,
                metrics_data=result,
                metrics_info=metrics_info,
                metrics_analysis=metrics_analysis
            )
            
            if pdf_file:
                logger.info(f"서버 보고서 생성 완료: {pdf_file}")
            
            # 서버 데이터 저장
            servers_data[server_name] = {
                'metrics_data': result,
                'metrics_analysis': metrics_analysis,
                'graph_files': graph_files,
                'dashboard_file': dashboard_file,
                'pdf_file': pdf_file
            }
            
            logger.info(f"서버 '{server_name}' 처리 완료")
        
        except Exception as e:
            logger.error(f"서버 '{server_name}' 처리 중 오류 발생: {str(e)}")
    
    # 5. 사이트 전체 종합 보고서 생성
    if servers_data:
        site_pdf = report_generator.generate_site_report(
            site_name=site_display_name,
            servers_data=servers_data,
            metrics_info=metrics_info
        )
        
        if site_pdf:
            logger.info(f"사이트 종합 보고서 생성 완료: {site_pdf}")
    
    logger.info(f"사이트 '{site_display_name}' 종합 보고서 생성 완료. 처리된 서버: {len(servers_data)}/{len(servers)}")
    return len(servers_data) > 0

if __name__ == "__main__":
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description='네이버 클라우드 인사이트 종합 보고서 생성')
    parser.add_argument('site', help='사이트 ID')
    parser.add_argument('--days', type=int, default=7, help='조회할 일수 (기본값: 7)')
    
    args = parser.parse_args()
    
    # 설정 파일 로드
    configs = load_all_configs()
    
    # 사이트 설정 가져오기
    sites_config = configs.get('sites', {})
    sites = sites_config.get('sites', {})
    
    if args.site not in sites:
        print(f"오류: 사이트 '{args.site}'을(를) 찾을 수 없습니다.")
        sys.exit(1)
    
    # 종합 보고서 생성
    if generate_comprehensive_report(args.site, sites[args.site], days=args.days):
        print(f"사이트 '{args.site}'의 종합 보고서가 성공적으로 생성되었습니다.")
        sys.exit(0)
    else:
        print(f"사이트 '{args.site}'의 종합 보고서 생성에 실패했습니다.")
        sys.exit(1)