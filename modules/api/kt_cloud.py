# modules/api/kt_cloud.py
import requests
import time
from datetime import datetime

def get_subject_token(usr_name, usr_passwd):
    """
    KT Cloud API 인증 토큰 발급
    """
    request_body = {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "domain": {"id": "default"},
                        "name": usr_name,
                        "password": usr_passwd
                    }
                }
            },
            "scope": {
                "project": {
                    "domain": {"id": "default"},
                    "name": usr_name
                }
            }
        }
    }
    
    # 공공 D1 API 인증 토큰 URL
    api_end_point_for_get_token = 'https://api.ucloudbiz.olleh.com/gd1/identity/auth/tokens'
    
    post_response = requests.post(api_end_point_for_get_token, json=request_body)
    
    # 인증 토큰 발급 요청이 성공하면 201 created 응답 코드 발생
    # 토큰은 응답 헤더의 X-Subject-Token의 필드값으로 전달
    if post_response.status_code == 201:
        x_subject_token = post_response.headers['X-Subject-Token']
        return x_subject_token
    else:
        error_msg = f"KT Cloud 인증 실패 ({post_response.status_code}): {post_response.text}"
        raise Exception(error_msg)

def get_watch_metric_value(x_auth_token, vm_id, metric_name, period="5min", term="5min"):
    """
    KT Cloud Watch에서 메트릭 값 조회
    """
    # 공공 D1 플랫폼 watch 호출
    api_common_url = 'https://api.ucloudbiz.olleh.com/gd1/watch/'
    
    # Average, Minimum, Maximum, Sum, SampleCount
    statistic_type = 'Average'
    
    # 요청 URL 작성
    request_parameters = f'namespace=gcloudserver&metricName={metric_name}' \
    f'&statisticType={statistic_type}&period={period}&term={term}&dimension.name=id' \
    f"&dimension.value={vm_id}"
    
    api_url = api_common_url + 'v3/metrics?' + request_parameters
    
    headers = {'X-Auth-Token': x_auth_token}
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result and 'data' in result and 'result' in result['data'] and result['data']['result']:
            return float(result['data']['result'][0]['values'][0][1])
        else:
            return 0.0
    else:
        error_msg = f"KT Cloud Watch 데이터 조회 실패 ({response.status_code}): {response.text}"
        raise Exception(error_msg)