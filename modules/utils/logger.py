# modules/utils/logger.py
import logging
import os
from datetime import datetime

def setup_logger(log_dir="logs", log_level=logging.INFO):
    """
    프로젝트 로거 설정
    
    Args:
        log_dir (str): 로그 파일 저장 디렉토리
        log_level (int): 로깅 레벨
        
    Returns:
        logging.Logger: 설정된 로거 객체
    """
    # 로그 디렉토리가 없으면 생성
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 로그 파일명 (현재 날짜 기준)
    log_filename = datetime.now().strftime('%Y-%m-%d') + '.log'
    log_filepath = os.path.join(log_dir, log_filename)
    
    # 로거 설정
    logger = logging.getLogger('cloud_insight_reports')
    logger.setLevel(log_level)
    
    # 이미 핸들러가 있으면 중복 추가 방지
    if not logger.handlers:
        # 파일 핸들러
        file_handler = logging.FileHandler(log_filepath)
        file_handler.setLevel(log_level)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # 포맷 설정
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 핸들러 추가
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger