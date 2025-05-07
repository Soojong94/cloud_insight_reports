# modules/utils/config_loader.py
import yaml
import os

def load_config(config_file):
    """
    YAML 설정 파일 로드
    
    Args:
        config_file (str): 설정 파일 경로
        
    Returns:
        dict: 설정 데이터
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    return config

def load_all_configs(config_dir="config"):
    """
    config 디렉토리의 모든 설정 파일 로드
    
    Args:
        config_dir (str): 설정 파일 디렉토리
        
    Returns:
        dict: 설정 데이터 (파일명을 키로 사용)
    """
    configs = {}
    
    # 설정 파일 목록
    config_files = {
        'settings': os.path.join(config_dir, 'settings.yaml'),
        'sites': os.path.join(config_dir, 'sites.yaml'),
        'metrics': os.path.join(config_dir, 'metrics.yaml')
    }
    
    # 각 설정 파일 로드
    for key, file_path in config_files.items():
        try:
            configs[key] = load_config(file_path)
        except FileNotFoundError as e:
            print(f"경고: {e}")
            configs[key] = {}
    
    return configs