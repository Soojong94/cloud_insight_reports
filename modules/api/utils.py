# modules/api/utils.py
import hmac
import hashlib
import base64
import time
import json
import requests
from datetime import datetime, timedelta

# modules/api/utils.py (일부)
def make_signature(access_key, secret_key, method, uri):
    """
    네이버 클라우드 API 호출을 위한 서명 생성
    """
    timestamp = int(time.time() * 1000)
    timestamp = str(timestamp)
    
    secret_key_bytes = bytes(secret_key, 'UTF-8')
    
    # 여기서 메서드와 URI만 사용하여 시그니처 생성
    # 쿼리 파라미터는 포함하지 않음
    string_to_sign = method + " " + uri + "\n" + timestamp + "\n" + access_key
    string_to_sign_bytes = bytes(string_to_sign, 'UTF-8')
    
    signature = base64.b64encode(hmac.new(secret_key_bytes, string_to_sign_bytes, digestmod=hashlib.sha256).digest())
    
    return signature.decode('utf-8'), timestamp

def handle_api_error(response):
    """
    API 응답 오류 처리
    """
    if response.status_code >= 400:
        try:
            error_info = response.json()
            error_msg = f"API 오류 ({response.status_code}): {error_info}"
        except ValueError:
            error_msg = f"API 오류 ({response.status_code}): {response.text}"
        
        raise Exception(error_msg)
    
    return response