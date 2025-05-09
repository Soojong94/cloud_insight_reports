# date_range_report.py
import os
import sys
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
from datetime import datetime, timedelta
import numpy as np

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.api.naver_insight import query_multiple_data
from modules.utils.config_loader import load_all_configs
from modules.utils.logger import setup_logger

def get_custom_timestamps(start_date_str, end_date_str):
    """
    사용자 지정 기간의 시작과 끝 타임스탬프 반환 (밀리초 단위)
    
    Args:
        start_date_str (str): 시작 날짜 (YYYYMMDD 형식)
        end_date_str (str): 종료 날짜 (YYYYMMDD 형식)
    
    Returns:
        tuple: (시작 시간, 종료 시간) 밀리초 단위 타임스탬프
    """
    # YYYYMMDD 문자열을 날짜 객체로 변환
    start_date = datetime.strptime(start_date_str, '%Y%m%d')
    end_date = datetime.strptime(end_date_str, '%Y%m%d')
    
    # 종료일은 해당일의 마지막 시간(23:59:59)으로 설정
    end_date = end_date.replace(hour=23, minute=59, second=59)
    
    # Unix timestamp (밀리초 단위)로 변환
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    return start_timestamp, end_timestamp

def set_korean_font():
    """
    한글 폰트 설정 함수
    시스템에 설치된 한글 폰트를 찾아 설정합니다.
    """
    # 폰트 경로 리스트 (여러 시스템에서 가능한 경로)
    font_paths = [
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',  # 리눅스 경로
        'C:/Windows/Fonts/malgun.ttf',  # 윈도우 경로
        '/Library/Fonts/AppleGothic.ttf'  # Mac 경로
    ]
    
    # 폰트 존재 여부 확인 후 설정
    font_found = False
    for font_path in font_paths:
        if os.path.exists(font_path):
            font_prop = fm.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = font_prop.get_name()
            font_found = True
            break
    
    # 직접 경로 검색이 실패한 경우, 시스템 폰트에서 검색
    if not font_found:
        for font in fm.findSystemFonts():
            font_lower = font.lower()
            if any(name in font_lower for name in ['gothic', 'gulim', 'malgun', 'nanum', 'batang']):
                font_prop = fm.FontProperties(fname=font)
                plt.rcParams['font.family'] = font_prop.get_name()
                font_found = True
                break
    
    # 마이너스 기호 깨짐 방지
    plt.rcParams['axes.unicode_minus'] = False

def generate_date_ticks(start_date, end_date):
    """
    시작 날짜부터 종료 날짜까지 일주일 간격으로 날짜 목록 생성
    
    Args:
        start_date (datetime.date): 시작 날짜
        end_date (datetime.date): 종료 날짜
        
    Returns:
        list: 일주일 간격의 날짜 목록
    """
    date_list = []
    
    # 시작 날짜 추가
    date_list.append(start_date)
    
    # 7일 간격으로 날짜 추가
    current = start_date
    while current < end_date:
        # 다음 날짜는 7일 후
        next_date = current + timedelta(days=7)
        if next_date <= end_date:
            date_list.append(next_date)
        current = next_date
    
    # 마지막 날짜가 이미 포함되어 있지 않으면 추가
    if end_date not in date_list:
        date_list.append(end_date)
    
    return date_list

def create_improved_dashboard(site_name, server_name, metrics_data, metrics_info, start_date, end_date, output_dir="output"):
    """
    개선된 대시보드 생성 (모든 메트릭을 한 화면에 표시)
    
    Args:
        site_name (str): 사이트 이름
        server_name (str): 서버 이름
        metrics_data (list): 메트릭 데이터 목록
        metrics_info (list): 메트릭 정의 정보
        start_date (str): 시작 날짜 (YYYYMMDD 형식)
        end_date (str): 종료 날짜 (YYYYMMDD 형식)
        output_dir (str): 출력 디렉토리
        
    Returns:
        str: 저장된 대시보드 파일 경로
    """
    # 한글 폰트 설정
    set_korean_font()
    
    # 로거 설정
    logger = setup_logger()
    logger.info(f"개선된 대시보드 생성 시작: {site_name} - {server_name}")
    
    if not metrics_data:
        logger.warning("대시보드 생성을 위한 메트릭 데이터가 없습니다.")
        return None
    
    # 메트릭 개수
    num_metrics = len(metrics_data)
    if num_metrics == 0:
        return None
    
    # 날짜 형식 변환 (표시용)
    start_date_display = datetime.strptime(start_date, '%Y%m%d').strftime('%Y.%m.%d')
    end_date_display = datetime.strptime(end_date, '%Y%m%d').strftime('%Y.%m.%d')
    
    # 시작 날짜와 종료 날짜 객체
    start_datetime = datetime.strptime(start_date, '%Y%m%d')
    end_datetime = datetime.strptime(end_date, '%Y%m%d')
    
    # 행과 열 계산 (2x3, 3x2, 2x2 등 그리드 형태로 배치)
    cols = min(3, num_metrics)
    rows = (num_metrics + cols - 1) // cols
    
    # 메트릭 정의 정보를 딕셔너리로 변환
    metrics_info_dict = {info.get('key'): info for info in metrics_info} if metrics_info else {}
    
    # 대시보드 생성 - 더 큰 사이즈로
    fig, axes = plt.subplots(rows, cols, figsize=(16, 10 * rows / 3), dpi=100)
    fig.suptitle(f'{site_name} - Proxy-Turn 서버 모니터링\n{start_date_display} ~ {end_date_display}', 
                 fontsize=18, y=0.98)
    
    # 축 객체를 1차원 배열로 변환
    if rows == 1 and cols == 1:
        axes = np.array([axes])
    elif rows == 1 or cols == 1:
        axes = axes.flatten()
    
    # 주간 간격으로 날짜 목록 생성
    date_ticks = generate_date_ticks(start_datetime.date(), end_datetime.date())
    
    # 각 메트릭 데이터에 대해 서브플롯에 그래프 생성
    for i, metric_data in enumerate(metrics_data):
        if i >= rows * cols:
            break  # 그리드보다 메트릭이 많은 경우 초과분 무시
        
        metric_key = metric_data.get('metric', '')
        
        # 메트릭 정의 정보 조회
        metric_info = metrics_info_dict.get(metric_key, {})
        metric_name = metric_info.get('name', metric_key)
        unit = metric_info.get('unit', '')
        
        # 데이터 포인트 추출
        data_points = metric_data.get('dps', [])
        if not data_points:
            logger.warning(f"'{metric_name}' 메트릭의 데이터가 비어있습니다")
            continue
        
        # 데이터프레임 생성 
        df = pd.DataFrame(data_points, columns=['timestamp', 'value'])
        
        # 타임스탬프를 datetime으로 변환 (밀리초 단위)
        df['datetime'] = df['timestamp'].apply(lambda x: datetime.fromtimestamp(x/1000))
        
        # 날짜 범위 확인 - 첫 날짜와 마지막 날짜가 요청한 범위와 일치하는지 확인
        actual_start = df['datetime'].min()
        actual_end = df['datetime'].max()
        
        # 데이터가 요청 범위보다 짧으면 로그 출력
        if actual_start.date() > start_datetime.date() or actual_end.date() < end_datetime.date():
            logger.warning(f"데이터 범위({actual_start.strftime('%Y-%m-%d')} ~ {actual_end.strftime('%Y-%m-%d')})가 " 
                           f"요청 범위({start_datetime.strftime('%Y-%m-%d')} ~ {end_datetime.strftime('%Y-%m-%d')})와 다릅니다")
        
        # 현재 서브플롯 가져오기
        if rows > 1 and cols > 1:
            ax = axes[i // cols, i % cols]
        else:
            ax = axes[i]
        
        # 시간 간격으로 데이터 리샘플링
        df_resampled = df.copy()
        df_resampled.set_index('datetime', inplace=True)
        
        # 날짜 범위에 따라 리샘플링 간격 조정
        date_range = (df['datetime'].max() - df['datetime'].min()).days + 1
        
        if date_range <= 7:  # 7일 이하: 2시간 간격
            resample_rule = '2H'
        elif date_range <= 31:  # 31일 이하: 6시간 간격
            resample_rule = '6H'
        else:  # 31일 초과: 12시간 간격
            resample_rule = '12H'
        
        # 지정된 간격으로 리샘플링
        df_resampled = df_resampled['value'].resample(resample_rule).mean().reset_index()
        
        # 리샘플링된 데이터로 선 그래프와 마커 함께 그리기
        if not df_resampled.empty:
            # 선 그래프
            ax.plot(df_resampled['datetime'], df_resampled['value'], 
                   '-o', linewidth=1.5, markersize=4, color='#1f77b4')
        
        # 그래프 설정
        ax.set_title(metric_name, fontsize=12, pad=10)
        ax.set_xlabel('시간', fontsize=10)
        ax.set_ylabel(f'{unit}' if unit else '값', fontsize=10)
        
        # X축 날짜 표시 설정 - 주간 간격으로 설정
        # 주간 간격 날짜에 맞는 Locator 설정
        days_to_show = [d.day for d in date_ticks]
        
        # X축 날짜 범위 수동 설정 (전체 기간을 명확히 표시)
        ax.set_xlim(start_datetime.date(), end_datetime.date() + timedelta(days=1))  # 하루 추가하여 여백 생성
        
        # 커스텀 날짜 로케이터와 포맷터
        ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=days_to_show))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        
        # 모든 날짜에 보조 눈금 추가
        ax.xaxis.set_minor_locator(mdates.DayLocator())
        ax.grid(which='minor', axis='x', linestyle='-', alpha=0.1)
        
        # 그리드 추가 (밝은 색상으로)
        ax.grid(True, linestyle='--', alpha=0.3)
        
        # 여백 설정
        if unit == '%':
            if metric_name == 'CPU 사용률' or metric_name == '메모리 사용률':
                # CPU나 메모리 사용률은 데이터 최댓값에 맞춰 조정 (위쪽 10% 여유)
                max_value = df['value'].max()
                y_max = min(100, max_value * 1.1)  # 최대 100%를 넘지 않도록
                ax.set_ylim(bottom=0, top=y_max)
            else:
                # 다른 퍼센트 단위는 0-100 범위로 표시
                ax.set_ylim(bottom=0, top=100)
        else:
            # 리샘플링된 데이터의 최소/최대값 기준으로 Y축 설정
            if not df_resampled.empty:
                min_value = df_resampled['value'].min()
                max_value = df_resampled['value'].max()
                
                # 데이터 범위 계산
                data_range = max_value - min_value
                
                # 최소/최대값이 같거나 범위가 매우 작은 경우 처리
                if data_range < 0.001 or min_value == max_value:
                    if max_value == 0:
                        # 모든 값이 0인 경우
                        ax.set_ylim(bottom=0, top=1)
                    else:
                        # 값이 모두 같은 경우, 값 주변에 범위 설정
                        margin = max(max_value * 0.1, 0.1)
                        ax.set_ylim(bottom=max(0, min_value - margin), 
                                    top=max_value + margin)
                else:
                    # 일반적인 경우: 위아래로 10% 여유 공간 추가
                    margin = data_range * 0.1
                    ax.set_ylim(bottom=max(0, min_value - margin), 
                                top=max_value + margin)
            else:
                # 리샘플링된 데이터가 없는 경우 원본 데이터 사용
                max_value = df['value'].max()
                ax.set_ylim(bottom=0, top=max_value * 1.1)  # 위쪽 10% 여유 공간

        # 축 레이블 간격 조정
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
    
    # 남은 빈 서브플롯 제거
    for i in range(num_metrics, rows * cols):
        if rows > 1 and cols > 1:
            fig.delaxes(axes[i // cols, i % cols])
        else:
            fig.delaxes(axes[i])
    
    # 레이아웃 조정 - 더 여유있게
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # top 마진을 남겨 suptitle 공간 확보
    
    # 저장 경로 생성
    site_dir = os.path.join(output_dir, site_name)
    if not os.path.exists(site_dir):
        os.makedirs(site_dir)
    
    # 서버 디렉토리 생성
    server_dir = os.path.join(site_dir, server_name.replace(' ', '_'))
    if not os.path.exists(server_dir):
        os.makedirs(server_dir)
    
    # 파일명 생성 - 날짜 범위 포함
    filename = f"{server_name.replace(' ', '_')}_dashboard_{start_date}_to_{end_date}.png"
    filepath = os.path.join(server_dir, filename)
    
    # 대시보드 저장
    fig.savefig(filepath, dpi=120, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"개선된 대시보드 저장 완료: {filepath}")
    return filepath

def create_individual_metrics(site_name, server_name, metrics_data, metrics_info, start_date, end_date, output_dir="output"):
    """
    개별 메트릭에 대한 개선된 그래프 생성
    
    Args:
        site_name (str): 사이트 이름
        server_name (str): 서버 이름
        metrics_data (list): 메트릭 데이터 목록
        metrics_info (list): 메트릭 정의 정보
        start_date (str): 시작 날짜 (YYYYMMDD 형식)
        end_date (str): 종료 날짜 (YYYYMMDD 형식)
        output_dir (str): 출력 디렉토리
        
    Returns:
        list: 저장된 그래프 파일 경로 목록
    """
    # 한글 폰트 설정
    set_korean_font()
    
    # 로거 설정
    logger = setup_logger()
    
    # 날짜 형식 변환 (표시용)
    start_date_display = datetime.strptime(start_date, '%Y%m%d').strftime('%Y.%m.%d')
    end_date_display = datetime.strptime(end_date, '%Y%m%d').strftime('%Y.%m.%d')
    
    # 시작 날짜와 종료 날짜 객체
    start_datetime = datetime.strptime(start_date, '%Y%m%d')
    end_datetime = datetime.strptime(end_date, '%Y%m%d')
    
    # 주간 간격으로 날짜 목록 생성
    date_ticks = generate_date_ticks(start_datetime.date(), end_datetime.date())
    
    # 메트릭 정의 정보를 딕셔너리로 변환
    metrics_info_dict = {info.get('key'): info for info in metrics_info} if metrics_info else {}
    
    result_files = []
    
    # 저장 경로 생성
    site_dir = os.path.join(output_dir, site_name)
    if not os.path.exists(site_dir):
        os.makedirs(site_dir)
    
    server_dir = os.path.join(site_dir, server_name.replace(' ', '_'))
    if not os.path.exists(server_dir):
        os.makedirs(server_dir)
    
    # 각 메트릭 데이터에 대해 그래프 생성
    for metric_data in metrics_data:
        metric_key = metric_data.get('metric', '')
        
        # 메트릭 정의 정보 조회
        metric_info = metrics_info_dict.get(metric_key, {})
        metric_name = metric_info.get('name', metric_key)
        unit = metric_info.get('unit', '')
        
        # 데이터 포인트 추출
        data_points = metric_data.get('dps', [])
        if not data_points:
            logger.warning(f"'{metric_name}' 메트릭의 데이터가 비어있습니다")
            continue
        
        # 데이터프레임 생성
        df = pd.DataFrame(data_points, columns=['timestamp', 'value'])
        
        # 타임스탬프를 datetime으로 변환 (밀리초 단위)
        df['datetime'] = df['timestamp'].apply(lambda x: datetime.fromtimestamp(x/1000))
        
        # 그래프 생성 (큰 크기로)
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
        
        # 제목 설정
        fig.suptitle(f'{site_name} - {server_name}', fontsize=14)
        ax.set_title(f'{metric_name} 추이\n{start_date_display} ~ {end_date_display}', fontsize=12, pad=10)
        
        # 시간 간격으로 데이터 리샘플링
        df_resampled = df.copy()
        df_resampled.set_index('datetime', inplace=True)
        
        # 날짜 범위에 따라 리샘플링 간격 조정
        date_range = (df['datetime'].max() - df['datetime'].min()).days + 1
        
        if date_range <= 7:  # 7일 이하: 2시간 간격
            resample_rule = '2H'
        elif date_range <= 31:  # 31일 이하: 6시간 간격
            resample_rule = '6H'
        else:  # 31일 초과: 12시간 간격
            resample_rule = '12H'
        
        # 지정된 간격으로 리샘플링
        df_resampled = df_resampled['value'].resample(resample_rule).mean().reset_index()
        
        # 리샘플링된 데이터로 선 그래프와 마커 함께 그리기
        if not df_resampled.empty:
            # 선 그래프
            ax.plot(df_resampled['datetime'], df_resampled['value'], 
                   '-o', linewidth=1.5, markersize=4, color='#1f77b4')
        
        # 그래프 설정
        ax.set_xlabel('날짜', fontsize=10)
        ax.set_ylabel(f'{unit}' if unit else '값', fontsize=10)

        # X축 날짜 표시 설정 - 주간 간격
        days_to_show = [d.day for d in date_ticks]
        
        # X축 날짜 범위 수동 설정 (전체 기간을 명확히 표시)
        ax.set_xlim(start_datetime.date(), end_datetime.date() + timedelta(days=1))  # 하루 추가하여 여백 생성
        
        # 커스텀 날짜 로케이터와 포맷터
        ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=days_to_show))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        
        # 모든 날짜에 보조 눈금 추가
        ax.xaxis.set_minor_locator(mdates.DayLocator())
        ax.grid(which='minor', axis='x', linestyle='-', alpha=0.1)
        
        # 그리드 추가 (밝은 색상으로)
        ax.grid(True, linestyle='--', alpha=0.3)
        
        # 여백 설정
        if unit == '%':
            if metric_name == 'CPU 사용률' or metric_name == '메모리 사용률':
                # CPU나 메모리 사용률은 데이터 최댓값에 맞춰 조정 (위쪽 10% 여유)
                max_value = df['value'].max()
                y_max = min(100, max_value * 1.1)  # 최대 100%를 넘지 않도록
                ax.set_ylim(bottom=0, top=y_max)
            else:
                # 다른 퍼센트 단위는 0-100 범위로 표시
                ax.set_ylim(bottom=0, top=100)
        else:
            # 리샘플링된 데이터의 최소/최대값 기준으로 Y축 설정
            if not df_resampled.empty:
                min_value = df_resampled['value'].min()
                max_value = df_resampled['value'].max()
                
                # 데이터 범위 계산
                data_range = max_value - min_value
                
                # 최소/최대값이 같거나 범위가 매우 작은 경우 처리
                if data_range < 0.001 or min_value == max_value:
                    if max_value == 0:
                        # 모든 값이 0인 경우
                        ax.set_ylim(bottom=0, top=1)
                    else:
                        # 값이 모두 같은 경우, 값 주변에 범위 설정
                        margin = max(max_value * 0.1, 0.1)
                        ax.set_ylim(bottom=max(0, min_value - margin), 
                                    top=max_value + margin)
                else:
                    # 일반적인 경우: 위아래로 10% 여유 공간 추가
                    margin = data_range * 0.1
                    ax.set_ylim(bottom=max(0, min_value - margin), 
                                top=max_value + margin)
            else:
                # 리샘플링된 데이터가 없는 경우 원본 데이터 사용
                max_value = df['value'].max()
                ax.set_ylim(bottom=0, top=max_value * 1.1)  # 위쪽 10% 여유 공간
        
        # 축 레이블 간격 조정
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
        
        # 파일명 생성 - 날짜 범위 포함
        filename = f"{metric_key}_{start_date}_to_{end_date}.png"
        filepath = os.path.join(server_dir, filename)
        
        # 그래프 저장
        plt.tight_layout()
        fig.savefig(filepath, dpi=120, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"개선된 메트릭 그래프 저장 완료: {filepath}")
        result_files.append(filepath)
    
    return result_files

def run_date_range_report(start_date, end_date, site_name=None):
    """
    특정 날짜 범위의 데이터를 조회하여 보고서 생성
    
    Args:
        start_date (str): 시작 날짜 (YYYYMMDD 형식)
        end_date (str): 종료 날짜 (YYYYMMDD 형식)
        site_name (str, optional): 특정 사이트 이름 (None이면 모든 사이트)
    """
    # 로거 설정
    logger = setup_logger()
    logger.info(f"날짜 범위 보고서 생성 시작: {start_date} ~ {end_date}")
    
    # 설정 파일 로드
    configs = load_all_configs()
    
    # 사이트 설정 가져오기
    sites_config = configs.get('sites', {})
    sites = sites_config.get('sites', {})
    
    # 메트릭 정보 로드
    metrics_config = configs.get('metrics', {})
    metrics_info = metrics_config.get('metrics', [])
    
    # 기본 설정
    output_dir = f"output/report_{start_date}_to_{end_date}"
    
    # 타임스탬프 변환
    start_timestamp, end_timestamp = get_custom_timestamps(start_date, end_date)
    
    # 처리할 사이트 목록
    target_sites = {site_name: sites[site_name]} if site_name and site_name in sites else sites
    
    success_count = 0
    
    for site_name, site_config in target_sites.items():
        logger.info(f"사이트 '{site_name}' 처리 중...")
        
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
            continue
        
        if not servers:
            logger.warning(f"사이트 '{site_display_name}'에 등록된 서버가 없습니다.")
            continue
        
        # 메트릭 키 목록
        metric_keys = [metric.get('key') for metric in metrics_info if metric.get('key')]
        
        server_success = 0
        
        # 각 서버에 대해 처리
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
                    start_time=start_timestamp,
                    end_time=end_timestamp,
                    cw_key=cw_key,
                    interval="Min5",
                    aggregation="AVG"
                )
                
                if result:
                    logger.info(f"데이터 조회 성공: {len(result)} 메트릭 데이터")
                    
                    # 유효한 메트릭 데이터 필터링
                    valid_metrics = [m for m in result if m.get('dps')]
                    
                    if valid_metrics:
                        # 개별 메트릭 그래프 생성
                        metric_files = create_individual_metrics(
                            site_name=site_display_name,
                            server_name=server_name,
                            metrics_data=valid_metrics,
                            metrics_info=metrics_info,
                            start_date=start_date,
                            end_date=end_date,
                            output_dir=output_dir
                        )
                        
                        # 대시보드 생성
                        dashboard_file = create_improved_dashboard(
                            site_name=site_display_name,
                            server_name=server_name,
                            metrics_data=valid_metrics,
                            metrics_info=metrics_info,
                            start_date=start_date,
                            end_date=end_date,
                            output_dir=output_dir
                        )
                        
                        logger.info(f"서버 '{server_name}' 처리 완료. 생성된 파일: {len(metric_files) + 1}개")
                        server_success += 1
                    else:
                        logger.warning(f"서버 '{server_name}'의 유효한 메트릭 데이터가 없습니다.")
                else:
                    logger.error(f"서버 '{server_name}' 데이터 조회 실패")
            
            except Exception as e:
                logger.error(f"서버 '{server_name}' 처리 중 오류 발생: {str(e)}")
        
        if server_success > 0:
            success_count += 1
            logger.info(f"사이트 '{site_display_name}' 처리 완료. 성공 서버: {server_success}/{len(servers)}")
        else:
            logger.error(f"사이트 '{site_display_name}' 처리 실패. 모든 서버에서 오류 발생.")
    
    # 결과 요약
    total_sites = len(target_sites)
    logger.info(f"날짜 범위 보고서 생성 완료. 성공 사이트: {success_count}/{total_sites}")
    
    # 보고서 저장 위치 출력
    if success_count > 0:
        logger.info(f"보고서가 다음 위치에 저장되었습니다: {output_dir}")
        print(f"\n보고서가 다음 위치에 저장되었습니다: {os.path.abspath(output_dir)}")

def validate_date(date_str):
    """날짜 형식 검증 (YYYYMMDD)"""
    try:
        datetime.strptime(date_str, '%Y%m%d')
        return True
    except ValueError:
        return False

def main():
    """
    메인 함수
    """
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description='네이버 클라우드 인사이트 날짜 범위 보고서 생성')
    parser.add_argument('start_date', help='시작 날짜 (YYYYMMDD 형식, 예: 20250401)')
    parser.add_argument('end_date', help='종료 날짜 (YYYYMMDD 형식, 예: 20250430)')
    parser.add_argument('--site', help='특정 사이트 ID (입력하지 않으면 모든 사이트 처리)')
    
    args = parser.parse_args()
    
    # 날짜 형식 검증
    if not validate_date(args.start_date):
        print(f"오류: 시작 날짜 '{args.start_date}'가 올바른 형식(YYYYMMDD)이 아닙니다.")
        return 1
    
    if not validate_date(args.end_date):
        print(f"오류: 종료 날짜 '{args.end_date}'가 올바른 형식(YYYYMMDD)이 아닙니다.")
        return 1
    
    # 시작 날짜가 종료 날짜보다 이후인지 확인
    start_date = datetime.strptime(args.start_date, '%Y%m%d')
    end_date = datetime.strptime(args.end_date, '%Y%m%d')
    
    if start_date > end_date:
        print(f"오류: 시작 날짜({args.start_date})가 종료 날짜({args.end_date})보다 이후입니다.")
        return 1
    
    # 보고서 생성
    try:
        run_date_range_report(args.start_date, args.end_date, args.site)
        return 0
    except Exception as e:
        print(f"오류: 보고서 생성 중 예외 발생: {str(e)}")
        return 1

if __name__ == "__main__":
    # matplotlib 경고 무시
    import warnings
    warnings.filterwarnings("ignore")
    
    # 실행
    sys.exit(main())