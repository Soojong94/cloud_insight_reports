# modules/reports/data_processor.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ..utils.logger import setup_logger

class MetricsDataProcessor:
    """
    서버 메트릭 데이터 처리 및 분석 클래스
    """
    def __init__(self):
        """
        초기화
        """
        self.logger = setup_logger()
    
    def process_metric_data(self, metric_data):
        """
        메트릭 데이터를 데이터프레임으로 변환 및 처리
        
        Args:
            metric_data (dict): API 응답 메트릭 데이터
            
        Returns:
            pandas.DataFrame: 변환된 데이터프레임, 실패 시 None
        """
        if not metric_data or 'dps' not in metric_data or not metric_data['dps']:
            metric_name = metric_data.get('metric', 'unknown') if metric_data else 'unknown'
            self.logger.warning(f"'{metric_name}' 메트릭 데이터가 비어있습니다")
            return None
        
        # 데이터 포인트 추출
        data_points = metric_data['dps']
        
        # 데이터프레임 생성
        df = pd.DataFrame(data_points, columns=['timestamp', 'value'])
        
        # 타임스탬프를 datetime으로 변환 (밀리초 단위)
        df['datetime'] = df['timestamp'].apply(lambda x: datetime.fromtimestamp(x/1000))
        
        # 날짜 및 시간 컬럼 추가
        df['date'] = df['datetime'].dt.date
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.day_name()
        
        return df
    
    def calculate_statistics(self, df):
        """
        메트릭 데이터의 통계 계산
        
        Args:
            df (pandas.DataFrame): 메트릭 데이터프레임
            
        Returns:
            dict: 통계 정보
        """
        if df is None or df.empty:
            return None
        
        # 기본 통계
        stats = {
            'count': len(df),
            'min': df['value'].min(),
            'max': df['value'].max(),
            'mean': df['value'].mean(),
            'median': df['value'].median(),
            'std': df['value'].std(),
            'first_time': df['datetime'].min(),
            'last_time': df['datetime'].max()
        }
        
        # 백분위 통계
        percentiles = [10, 25, 75, 90, 95, 99]
        for p in percentiles:
            stats[f'percentile_{p}'] = df['value'].quantile(p/100)
        
        # 일별 평균
        daily_avg = df.groupby('date')['value'].mean().to_dict()
        stats['daily_avg'] = daily_avg
        
        # 시간별 평균 (하루 중 시간대별)
        hourly_avg = df.groupby('hour')['value'].mean().to_dict()
        stats['hourly_avg'] = hourly_avg
        
        # 요일별 평균
        day_of_week_avg = df.groupby('day_of_week')['value'].mean().to_dict()
        stats['day_of_week_avg'] = day_of_week_avg
        
        return stats
    
    def detect_anomalies(self, df, threshold_warning=None, threshold_critical=None):
        """
        이상치 탐지
        
        Args:
            df (pandas.DataFrame): 메트릭 데이터프레임
            threshold_warning (float): 경고 임계값
            threshold_critical (float): 심각 임계값
            
        Returns:
            dict: 이상치 정보
        """
        if df is None or df.empty:
            return None
        
        anomalies = {
            'warning': [],
            'critical': [],
            'outliers': []
        }
        
        # 임계값 기반 이상치
        if threshold_warning is not None:
            warning_points = df[df['value'] >= threshold_warning]
            if not warning_points.empty:
                anomalies['warning'] = warning_points.to_dict('records')
        
        if threshold_critical is not None:
            critical_points = df[df['value'] >= threshold_critical]
            if not critical_points.empty:
                anomalies['critical'] = critical_points.to_dict('records')
        
        # 통계적 이상치 (IQR 방식 - 1.5 IQR 벗어나는 값)
        q1 = df['value'].quantile(0.25)
        q3 = df['value'].quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = df[(df['value'] < lower_bound) | (df['value'] > upper_bound)]
        if not outliers.empty:
            anomalies['outliers'] = outliers.to_dict('records')
        
        return anomalies
    
    def compare_time_periods(self, df, period_days=7):
        """
        기간별 비교 (현재 기간 vs 이전 기간)
        
        Args:
            df (pandas.DataFrame): 메트릭 데이터프레임
            period_days (int): 비교 기간 (일)
            
        Returns:
            dict: 기간 비교 정보
        """
        if df is None or df.empty:
            return None
        
        # 최대/최소 날짜 확인
        min_date = df['datetime'].min().date()
        max_date = df['datetime'].max().date()
        
        # 기간 구분이 가능한지 확인
        date_range = (max_date - min_date).days
        if date_range < period_days * 2:
            self.logger.warning(f"비교 기간({period_days}일)의 2배({period_days*2}일) 보다 데이터 기간({date_range}일)이 짧아 기간 비교를 할 수 없습니다.")
            return None
        
        # 현재 기간과 이전 기간 구분
        mid_date = max_date - timedelta(days=period_days)
        
        current_period = df[df['datetime'].dt.date > mid_date]
        previous_period = df[df['datetime'].dt.date <= mid_date]
        
        # 각 기간의 통계 계산
        current_stats = {
            'mean': current_period['value'].mean(),
            'max': current_period['value'].max(),
            'min': current_period['value'].min(),
            'std': current_period['value'].std(),
            'start_date': current_period['datetime'].min().date(),
            'end_date': current_period['datetime'].max().date(),
            'count': len(current_period)
        }
        
        previous_stats = {
            'mean': previous_period['value'].mean(),
            'max': previous_period['value'].max(),
            'min': previous_period['value'].min(),
            'std': previous_period['value'].std(),
            'start_date': previous_period['datetime'].min().date(),
            'end_date': previous_period['datetime'].max().date(),
            'count': len(previous_period)
        }
        
        # 변화율 계산
        changes = {
            'mean_change': ((current_stats['mean'] - previous_stats['mean']) / previous_stats['mean'] * 100) if previous_stats['mean'] != 0 else float('inf'),
            'max_change': ((current_stats['max'] - previous_stats['max']) / previous_stats['max'] * 100) if previous_stats['max'] != 0 else float('inf'),
            'min_change': ((current_stats['min'] - previous_stats['min']) / previous_stats['min'] * 100) if previous_stats['min'] != 0 else float('inf')
        }
        
        return {
            'current_period': current_stats,
            'previous_period': previous_stats,
            'changes': changes
        }
    
    def analyze_metric(self, metric_data, metric_info):
        """
        단일 메트릭에 대한 종합 분석 수행
        
        Args:
            metric_data (dict): API 응답 메트릭 데이터
            metric_info (dict): 메트릭 정의 정보
            
        Returns:
            dict: 분석 결과
        """
        if not metric_data:
            return None
        
        # 메트릭 정보 추출
        metric_key = metric_data.get('metric', '')
        metric_name = metric_info.get('name', metric_key) if metric_info else metric_key
        threshold_warning = metric_info.get('threshold_warning') if metric_info else None
        threshold_critical = metric_info.get('threshold_critical') if metric_info else None
        
        # 데이터프레임 변환
        df = self.process_metric_data(metric_data)
        
        if df is None or df.empty:
            self.logger.warning(f"'{metric_name}' 메트릭의 데이터가 비어있거나 처리할 수 없습니다.")
            return None
        
        # 분석 수행
        analysis = {
            'metric_key': metric_key,
            'metric_name': metric_name,
            'data_points': len(df),
            'timestamp_range': {
                'start': df['datetime'].min(),
                'end': df['datetime'].max(),
                'duration_hours': (df['datetime'].max() - df['datetime'].min()).total_seconds() / 3600
            },
            'statistics': self.calculate_statistics(df),
            'anomalies': self.detect_anomalies(df, threshold_warning, threshold_critical),
            'period_comparison': self.compare_time_periods(df)
        }
        
        return analysis
    
    def analyze_multiple_metrics(self, metrics_data, metrics_info):
        """
        여러 메트릭에 대한 분석 수행
        
        Args:
            metrics_data (list): 메트릭 데이터 목록
            metrics_info (list): 메트릭 정의 정보 목록
            
        Returns:
            dict: 메트릭별 분석 결과
        """
        if not metrics_data:
            return None
        
        # 메트릭 정의 정보를 딕셔너리로 변환 (빠른 조회용)
        metrics_info_dict = {info.get('key'): info for info in metrics_info} if metrics_info else {}
        
        # 각 메트릭 분석
        results = {}
        for metric_data in metrics_data:
            metric_key = metric_data.get('metric', '')
            
            # 메트릭 정의 정보 조회
            metric_info = metrics_info_dict.get(metric_key, {})
            
            # 메트릭 분석
            analysis = self.analyze_metric(metric_data, metric_info)
            
            if analysis:
                results[metric_key] = analysis
        
        return results