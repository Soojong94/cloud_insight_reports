# modules/api/naver_insight.py
import requests
import json
from datetime import datetime, timedelta
import time
from ..api.utils import make_signature, handle_api_error

def query_data(access_key, secret_key, cw_key, metric, dimension_key, dimension_value, 
               start_time, end_time, interval="Min5", aggregation="AVG", product_name="System/Server(VPC)"):
    """
    Cloud Insight API를 사용하여 단일 메트릭 데이터 조회
    
    Args:
        access_key (str): 네이버 클라우드 플랫폼 API 액세스 키
        secret_key (str): 네이버 클라우드 플랫폼 API 시크릿 키
        cw_key (str): Cloud Insight 스키마 키
        metric (str): 조회할 메트릭 이름
        dimension_key (str): 차원 키 (예: vm_name)
        dimension_value (str): 차원 값 (예: 서버 이름)
        start_time (int): 조회 시작 시간 (Unix timestamp in milliseconds)
        end_time (int): 조회 종료 시간 (Unix timestamp in milliseconds)
        interval (str): 데이터 집계 간격 (Min1, Min5, Min30, Hour2, Day1)
        aggregation (str): 집계 함수 (AVG, MAX, MIN, SUM, COUNT)
        product_name (str): 제품 유형
        
    Returns:
        list: 조회된 시계열 데이터 (timestamp, value)
    """
    method = "POST"
    uri = "/cw_fea/real/cw/api/data/query"
    api_url = "https://cw.apigw.ntruss.com" + uri
    
    signature, timestamp = make_signature(access_key, secret_key, method, uri)
    
    headers = {
        'x-ncp-apigw-timestamp': timestamp,
        'x-ncp-iam-access-key': access_key,
        'x-ncp-apigw-signature-v2': signature,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "timeStart": start_time,
        "timeEnd": end_time,
        "cw_key": cw_key,
        "productName": product_name,
        "metric": metric,
        "interval": interval,
        "aggregation": aggregation,
        "dimensions": {
            dimension_key: dimension_value
        }
    }
    
    response = requests.post(api_url, headers=headers, json=payload)
    response = handle_api_error(response)
    
    return response.json()

def query_multiple_data(access_key, secret_key, metrics, dimension_key, dimension_value, 
                       start_time, end_time, cw_key, interval="Min5", aggregation="AVG"):
    """
    Cloud Insight API를 사용하여 여러 메트릭 데이터 조회
    
    Args:
        access_key (str): 네이버 클라우드 플랫폼 API 액세스 키
        secret_key (str): 네이버 클라우드 플랫폼 API 시크릿 키
        metrics (list): 조회할 메트릭 이름 목록
        dimension_key (str): 차원 키 (예: vm_name)
        dimension_value (str): 차원 값 (예: 서버 이름)
        start_time (int): 조회 시작 시간 (Unix timestamp in milliseconds)
        end_time (int): 조회 종료 시간 (Unix timestamp in milliseconds)
        cw_key (str): Cloud Insight 스키마 키
        interval (str): 데이터 집계 간격 (Min1, Min5, Min30, Hour2, Day1)
        aggregation (str): 집계 함수 (AVG, MAX, MIN, SUM, COUNT)
        
    Returns:
        list: 각 메트릭별 조회된 시계열 데이터
    """
    method = "POST"
    uri = "/cw_fea/real/cw/api/data/query/multiple"
    api_url = "https://cw.apigw.ntruss.com" + uri
    
    signature, timestamp = make_signature(access_key, secret_key, method, uri)
    
    headers = {
        'x-ncp-apigw-timestamp': timestamp,
        'x-ncp-iam-access-key': access_key,
        'x-ncp-apigw-signature-v2': signature,
        'Content-Type': 'application/json'
    }
    
    metric_info_list = []
    for metric in metrics:
        metric_info = {
            "aggregation": aggregation,
            "dimensions": {
                dimension_key: dimension_value
            },
            "interval": interval,
            "metric": metric,
            "prodKey": cw_key
        }
        metric_info_list.append(metric_info)
    
    payload = {
        "timeStart": start_time,
        "timeEnd": end_time,
        "metricInfoList": metric_info_list
    }
    
    response = requests.post(api_url, headers=headers, json=payload)
    response = handle_api_error(response)
    
    return response.json()

def send_data(access_key, secret_key, cw_key, vm_name, metrics_data):
    """
    Cloud Insight로 커스텀 데이터 전송
    
    Args:
        access_key (str): 네이버 클라우드 플랫폼 API 액세스 키
        secret_key (str): 네이버 클라우드 플랫폼 API 시크릿 키
        cw_key (str): Cloud Insight 스키마 키
        vm_name (str): 서버 이름
        metrics_data (dict): 메트릭 이름과 값 딕셔너리
        
    Returns:
        dict: API 응답 데이터
    """
    method = "POST"
    api_url = "https://cw.apigw.ntruss.com"
    action = "/cw_collector/real/data"
    
    signature, timestamp = make_signature(access_key, secret_key, method, action)
    
    http_header = {
        'x-ncp-apigw-signature-v2': signature,
        'x-ncp-apigw-timestamp': timestamp,
        'x-ncp-iam-access-key': access_key,
        'x-ncp-dmn_cd': 'PUB',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "cw_key": cw_key,
        "data": {
            "vm_name": vm_name,
            **metrics_data
        }
    }
    
    response = requests.post(api_url + action, headers=http_header, json=payload)
    response = handle_api_error(response)
    
    return response.json()

def get_timestamps_for_april_2024():
    """
    2024년 4월의 시작과 끝 타임스탬프 반환 (밀리초 단위)
    
    Returns:
        tuple: (시작 시간, 종료 시간) 밀리초 단위 타임스탬프
    """
    # 2024년 4월 1일 00:00:00
    start_date = datetime(2024, 4, 1, 0, 0, 0)
    # 2024년 4월 30일 23:59:59
    end_date = datetime(2024, 4, 30, 23, 59, 59)
    
    # Unix timestamp (밀리초 단위)로 변환
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    return start_timestamp, end_timestamp

def get_recent_timestamps(days=7):
    """
    최근 일정 기간의 시작과 끝 타임스탬프 반환 (밀리초 단위)
    
    Args:
        days (int): 조회할 기간 (일)
    
    Returns:
        tuple: (시작 시간, 종료 시간) 밀리초 단위 타임스탬프
    """
    # 현재 시간
    end_date = datetime.now()
    # days일 전
    start_date = end_date - timedelta(days=days)
    
    # Unix timestamp (밀리초 단위)로 변환
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    return start_timestamp, end_timestamp