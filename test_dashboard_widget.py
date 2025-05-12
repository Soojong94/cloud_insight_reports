# test_dashboard_widget_fixed.py
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

def download_widget_image(access_key, secret_key, dashboard_id, widget_id, start_time, end_time, output_path):
    """위젯 이미지 다운로드"""
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
    
    # 시그니처 생성 시 쿼리 스트링 포함 여부 확인 필요
    # 일부 API는 쿼리 스트링을 포함하여 서명하고, 일부는 포함하지 않습니다
    
    # 시도 1: 쿼리 스트링 없이 시그니처 생성
    signature, timestamp = make_signature(access_key, secret_key, method, uri)
    
    headers = {
        'x-ncp-apigw-timestamp': timestamp,
        'x-ncp-iam-access-key': access_key,
        'x-ncp-apigw-signature-v2': signature,
    }
    
    api_url = "https://cw.apigw.ntruss.com" + uri
    
    print(f"Attempting download with URL: {api_url}")
    print(f"Headers: {headers}")
    print(f"Params: {params}")
    
    response = requests.get(api_url, headers=headers, params=params)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Image saved to: {output_path}")
        return True
    else:
        print(f"Failed to download widget image: {response.status_code}")
        print(response.text)
        
        # 시도 2: 쿼리 스트링 포함하여 시그니처 생성
        print("\nTrying with query string in signature...")
        uri_with_query = f"{uri}?{query_string}"
        signature2, timestamp2 = make_signature(access_key, secret_key, method, uri_with_query)
        
        headers2 = {
            'x-ncp-apigw-timestamp': timestamp2,
            'x-ncp-iam-access-key': access_key,
            'x-ncp-apigw-signature-v2': signature2,
        }
        
        response2 = requests.get(api_url, headers=headers2, params=params)
        
        if response2.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response2.content)
            print(f"Image saved to: {output_path}")
            return True
        else:
            print(f"Failed again: {response2.status_code}")
            print(response2.text)
        
        return False

def test_simple_widget_download(access_key, secret_key):
    """간단한 위젯 이미지 다운로드 테스트"""
    # 직접 알고 있는 값으로 테스트
    dashboard_id = "df_460438474722512896"  # Server(VPC) dashboard
    widget_id = "avg_cpu_used_rto__460438474722512896"  # CPU widget
    
    # 최근 1시간 데이터
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - (3600 * 1000)  # 1시간 전
    
    output_path = "test_widget.png"
    
    print("=== Simple Widget Download Test ===")
    print(f"Dashboard ID: {dashboard_id}")
    print(f"Widget ID: {widget_id}")
    print(f"Time range: {datetime.fromtimestamp(start_time/1000)} ~ {datetime.fromtimestamp(end_time/1000)}")
    
    success = download_widget_image(
        access_key,
        secret_key,
        dashboard_id,
        widget_id,
        start_time,
        end_time,
        output_path
    )
    
    return success

def main():
    # 설정 로드
    configs = load_all_configs()
    sites_config = configs.get('sites', {})
    site_config = sites_config.get('sites', {}).get('site1', {})
    
    ncp_config = site_config.get('ncp', {})
    access_key = ncp_config.get('access_key')
    secret_key = ncp_config.get('secret_key')
    
    # 간단한 테스트 먼저 실행
    if not test_simple_widget_download(access_key, secret_key):
        print("\nSimple test failed. Checking API access...")
        
        # API 접근 권한 확인
        dashboards = get_dashboard_list(access_key, secret_key)
        if dashboards:
            print("Dashboard list API works fine.")
        else:
            print("Cannot access dashboard list API.")
            return
    
    # 전체 프로세스 실행
    print("\n=== Full Dashboard Widget Process ===")
    
    # 1. 대시보드 목록 조회
    dashboards = get_dashboard_list(access_key, secret_key)
    
    if not dashboards:
        print("No dashboards found")
        return
    
    # Server(VPC) 대시보드 찾기
    server_dashboard = None
    for dashboard in dashboards:
        if dashboard.get('name') == 'Server(VPC)':
            server_dashboard = dashboard
            break
    
    if not server_dashboard:
        print("Server(VPC) dashboard not found")
        return
    
    dashboard_id = server_dashboard.get('id')
    dashboard_name = server_dashboard.get('name')
    
    # 2. 위젯 목록 조회
    widgets = get_dashboard_widget_list(access_key, secret_key, dashboard_id)
    
    if not widgets:
        print("No widgets found")
        return
    
    # CPU 위젯 찾기
    cpu_widget = None
    for widget in widgets:
        if 'CPU' in widget.get('name', '').upper():
            cpu_widget = widget
            break
    
    if not cpu_widget:
        print("CPU widget not found")
        return
    
    # 3. 1월 데이터 테스트
    print("\n=== Testing January Data ===")
    
    start_time = 1735701540000  # 2025년 1월 1일
    end_time = 1738297140000    # 2025년 1월 31일
    
    output_path = "cpu_widget_jan2025.png"
    
    success = download_widget_image(
        access_key,
        secret_key,
        dashboard_id,
        cpu_widget.get('widgetId'),
        start_time,
        end_time,
        output_path
    )

if __name__ == "__main__":
    main()