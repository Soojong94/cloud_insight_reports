# test_dy_agr_dashboard.py
import os
import sys
import requests
from datetime import datetime, timedelta
import urllib.parse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.api.utils import make_signature
from modules.utils.config_loader import load_all_configs

def get_dashboard_list(access_key, secret_key):
    """대시보드 목록 조회"""
    method = "GET"
    uri = "/cw_fea/real/cw/api/chart/dashboard"
    api_url = "https://cw.apigw.ntruss.com" + uri
    
    signature, timestamp = make_signature(access_key, secret_key, method, uri)
    
    headers = {
        'x-ncp-apigw-timestamp': timestamp,
        'x-ncp-iam-access-key': access_key,
        'x-ncp-apigw-signature-v2': signature,
    }
    
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get dashboard list: {response.status_code}")
        print(response.text)
        return None

def get_dashboard_widget_list(access_key, secret_key, dashboard_id):
    """대시보드 위젯 목록 조회"""
    method = "GET"
    uri = f"/cw_fea/real/cw/api/chart/dashboard/{dashboard_id}/widgets"
    api_url = "https://cw.apigw.ntruss.com" + uri
    
    signature, timestamp = make_signature(access_key, secret_key, method, uri)
    
    headers = {
        'x-ncp-apigw-timestamp': timestamp,
        'x-ncp-iam-access-key': access_key,
        'x-ncp-apigw-signature-v2': signature,
    }
    
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get widget list: {response.status_code}")
        print(response.text)
        return None

def download_widget_image_with_query(access_key, secret_key, dashboard_id, widget_id, start_time, end_time, output_path):
    """위젯 이미지 다운로드 (쿼리 스트링 포함 시그니처)"""
    method = "GET"
    uri = f"/cw_fea/real/cw/api/chart/dashboard/{dashboard_id}/widgets/{widget_id}"
    
    # 쿼리 파라미터
    params = {
        'startTime': str(start_time),
        'endTime': str(end_time),
        'widgetResolutionMode': 'AUTO'
    }
    
    # 쿼리 스트링 생성
    query_string = urllib.parse.urlencode(params)
    
    # 쿼리 스트링 포함하여 시그니처 생성
    uri_with_query = f"{uri}?{query_string}"
    signature, timestamp = make_signature(access_key, secret_key, method, uri_with_query)
    
    headers = {
        'x-ncp-apigw-timestamp': timestamp,
        'x-ncp-iam-access-key': access_key,
        'x-ncp-apigw-signature-v2': signature,
    }
    
    api_url = "https://cw.apigw.ntruss.com" + uri
    
    response = requests.get(api_url, headers=headers, params=params)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Image saved to: {output_path}")
        return True
    else:
        print(f"Failed to download widget image: {response.status_code}")
        print(response.text)
        return False

def download_dy_agr_data():
    """DY_AGR 대시보드 데이터 다운로드"""
    # 설정 로드
    configs = load_all_configs()
    sites_config = configs.get('sites', {})
    site_config = sites_config.get('sites', {}).get('site1', {})
    
    ncp_config = site_config.get('ncp', {})
    access_key = ncp_config.get('access_key')
    secret_key = ncp_config.get('secret_key')
    
    # 1. 대시보드 목록에서 DY_AGR 찾기
    print("=== Finding DY_AGR Dashboard ===")
    dashboards = get_dashboard_list(access_key, secret_key)
    
    if not dashboards:
        print("No dashboards found")
        return
    
    dy_agr_dashboard = None
    for dashboard in dashboards:
        if dashboard.get('name') == 'DY_AGR':
            dy_agr_dashboard = dashboard
            break
    
    if not dy_agr_dashboard:
        print("DY_AGR dashboard not found")
        return
    
    dashboard_id = dy_agr_dashboard.get('id')
    dashboard_name = dy_agr_dashboard.get('name')
    print(f"Found dashboard: {dashboard_name} (ID: {dashboard_id})")
    
    # 2. DY_AGR 위젯 목록 조회
    print(f"\n=== Getting Widgets for {dashboard_name} ===")
    widgets = get_dashboard_widget_list(access_key, secret_key, dashboard_id)
    
    if not widgets:
        print("No widgets found")
        return
    
    print(f"Found {len(widgets)} widgets:")
    for i, widget in enumerate(widgets):
        widget_id = widget.get('widgetId')
        widget_name = widget.get('name')
        print(f"{i+1}. ID: {widget_id} - Name: {widget_name}")
    
    # 3. 출력 디렉토리 생성
    output_dir = f"dy_agr_widgets"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 4. 1월 데이터 다운로드
    print(f"\n=== Downloading January 2025 Data for {dashboard_name} ===")
    
    # 1월 날짜 설정
    start_time = 1735701540000  # 2025년 1월 1일
    end_time = 1738297140000    # 2025년 1월 31일
    
    print(f"Date range: {datetime.fromtimestamp(start_time/1000)} ~ {datetime.fromtimestamp(end_time/1000)}")
    
    # 모든 위젯 다운로드
    for widget in widgets:
        widget_id = widget.get('widgetId')
        widget_name = widget.get('name', 'untitled').replace('/', '_').replace(' ', '_')
        
        output_path = os.path.join(output_dir, f"{widget_name}_jan2025.png")
        
        print(f"\nDownloading: {widget_name}")
        success = download_widget_image_with_query(
            access_key, 
            secret_key, 
            dashboard_id, 
            widget_id, 
            start_time, 
            end_time, 
            output_path
        )
    
    # 5. 최근 7일 데이터도 다운로드 (비교용)
    print(f"\n=== Downloading Recent 7 Days Data for {dashboard_name} ===")
    
    # 최근 7일 설정
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    recent_start = int(start_date.timestamp() * 1000)
    recent_end = int(end_date.timestamp() * 1000)
    
    print(f"Date range: {start_date} ~ {end_date}")
    
    # 처음 3개 위젯만 다운로드 (샘플)
    for widget in widgets[:3]:
        widget_id = widget.get('widgetId')
        widget_name = widget.get('name', 'untitled').replace('/', '_').replace(' ', '_')
        
        output_path = os.path.join(output_dir, f"{widget_name}_recent7days.png")
        
        print(f"\nDownloading: {widget_name}")
        success = download_widget_image_with_query(
            access_key, 
            secret_key, 
            dashboard_id, 
            widget_id, 
            recent_start, 
            recent_end, 
            output_path
        )

if __name__ == "__main__":
    download_dy_agr_data()