# modules/reports/visualizer.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from ..utils.logger import setup_logger

class MetricsVisualizer:
    """
    서버 메트릭 데이터 시각화 클래스
    """
    def __init__(self, output_dir="output"):
        """
        초기화
        
        Args:
            output_dir (str): 결과물 저장 디렉토리
        """
        self.logger = setup_logger()
        self.output_dir = output_dir
        
        # 출력 디렉토리가 없으면 생성
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 한글 폰트 설정 (필요한 경우)
        try:
            plt.rcParams['font.family'] = 'NanumGothic'
            plt.rcParams['axes.unicode_minus'] = False
        except:
            self.logger.warning("NanumGothic 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
    
    def create_metric_dataframe(self, metric_data):
        """
        API 응답 데이터를 DataFrame으로 변환
        
        Args:
            metric_data (dict): API 응답 메트릭 데이터
            
        Returns:
            pandas.DataFrame: 변환된 데이터프레임
        """
        if not metric_data or 'dps' not in metric_data or not metric_data['dps']:
            self.logger.warning(f"메트릭 데이터가 비어있습니다: {metric_data}")
            return None
        
        # 데이터 포인트 추출
        data_points = metric_data['dps']
        
        # 데이터프레임 생성
        df = pd.DataFrame(data_points, columns=['timestamp', 'value'])
        
        # 타임스탬프를 datetime으로 변환 (밀리초 단위)
        df['datetime'] = df['timestamp'].apply(lambda x: datetime.fromtimestamp(x/1000))
        
        return df
    
    def plot_metric(self, df, metric_name, unit="", threshold_warning=None, threshold_critical=None):
        """
        단일 메트릭 그래프 생성
        
        Args:
            df (pandas.DataFrame): 메트릭 데이터프레임
            metric_name (str): 메트릭 이름
            unit (str): 메트릭 단위
            threshold_warning (float): 경고 임계값
            threshold_critical (float): 심각 임계값
            
        Returns:
            matplotlib.figure.Figure: 생성된 그래프 객체
        """
        if df is None or df.empty:
            self.logger.warning(f"'{metric_name}' 메트릭의 데이터가 없습니다.")
            return None
        
        # 그래프 생성
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 데이터 플롯
        ax.plot(df['datetime'], df['value'], '-o', markersize=3, label=metric_name)
        
        # 임계값 선 추가 (존재하는 경우)
        if threshold_warning is not None:
            ax.axhline(y=threshold_warning, color='orange', linestyle='--', label=f'경고 임계값 ({threshold_warning}{unit})')
        
        if threshold_critical is not None:
            ax.axhline(y=threshold_critical, color='red', linestyle='--', label=f'심각 임계값 ({threshold_critical}{unit})')
        
        # 그래프 설정
        ax.set_title(f'{metric_name} 추이')
        ax.set_xlabel('시간')
        ax.set_ylabel(f'값 ({unit})' if unit else '값')
        
        # x축 날짜 포맷 설정
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        fig.autofmt_xdate()
        
        # 범례 추가
        ax.legend()
        
        # 그리드 추가
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 여백 조정
        plt.tight_layout()
        
        return fig
    
    def save_metric_plot(self, fig, site_name, server_name, metric_name):
        """
        메트릭 그래프 저장
        
        Args:
            fig (matplotlib.figure.Figure): 그래프 객체
            site_name (str): 사이트 이름
            server_name (str): 서버 이름
            metric_name (str): 메트릭 이름
            
        Returns:
            str: 저장된 파일 경로
        """
        if fig is None:
            return None
        
        # 저장 경로 생성
        site_dir = os.path.join(self.output_dir, site_name)
        if not os.path.exists(site_dir):
            os.makedirs(site_dir)
        
        # 파일명 생성 (공백과 특수문자 제거)
        filename = f"{server_name.replace(' ', '_')}_{metric_name.replace(' ', '_')}.png"
        filepath = os.path.join(site_dir, filename)
        
        # 그래프 저장
        fig.savefig(filepath, dpi=100)
        plt.close(fig)
        
        self.logger.info(f"그래프 저장 완료: {filepath}")
        return filepath
    
    def visualize_all_metrics(self, site_name, server_name, metrics_data, metrics_info):
        """
        모든 메트릭 데이터 시각화 및 저장
        
        Args:
            site_name (str): 사이트 이름
            server_name (str): 서버 이름
            metrics_data (list): 메트릭 데이터 목록
            metrics_info (list): 메트릭 정의 정보
            
        Returns:
            list: 저장된 그래프 파일 경로 목록
        """
        result_files = []
        
        # 메트릭 정의 정보를 딕셔너리로 변환 (빠른 조회용)
        metrics_info_dict = {info.get('key'): info for info in metrics_info} if metrics_info else {}
        
        # 각 메트릭 데이터에 대해 시각화
        for metric_data in metrics_data:
            metric_key = metric_data.get('metric', '')
            
            # 메트릭 정의 정보 조회
            metric_info = metrics_info_dict.get(metric_key, {})
            metric_name = metric_info.get('name', metric_key)
            unit = metric_info.get('unit', '')
            threshold_warning = metric_info.get('threshold_warning')
            threshold_critical = metric_info.get('threshold_critical')
            
            # 데이터프레임 생성
            df = self.create_metric_dataframe(metric_data)
            
            # 그래프 생성 및 저장
            fig = self.plot_metric(df, metric_name, unit, threshold_warning, threshold_critical)
            filepath = self.save_metric_plot(fig, site_name, server_name, metric_name)
            
            if filepath:
                result_files.append(filepath)
        
        return result_files

    def create_dashboard(self, site_name, server_name, metrics_data, metrics_info):
        """
        여러 메트릭을 한 화면에 대시보드 형태로 표시
        
        Args:
            site_name (str): 사이트 이름
            server_name (str): 서버 이름
            metrics_data (list): 메트릭 데이터 목록
            metrics_info (list): 메트릭 정의 정보
            
        Returns:
            str: 저장된 대시보드 파일 경로
        """
        if not metrics_data:
            self.logger.warning("대시보드 생성을 위한 메트릭 데이터가 없습니다.")
            return None
        
        # 메트릭 개수
        num_metrics = len(metrics_data)
        if num_metrics == 0:
            return None
        
        # 행과 열 계산 (2x3, 3x2, 2x2 등 그리드 형태로 배치)
        cols = min(3, num_metrics)
        rows = (num_metrics + cols - 1) // cols
        
        # 메트릭 정의 정보를 딕셔너리로 변환
        metrics_info_dict = {info.get('key'): info for info in metrics_info} if metrics_info else {}
        
        # 현재 시간을 기반으로 타임스탬프 생성
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # 대시보드 생성
        fig, axes = plt.subplots(rows, cols, figsize=(15, 10 * rows / 3))
        fig.suptitle(f'{site_name} - {server_name} 메트릭 대시보드', fontsize=16)
        
        # 축 객체를 1차원 배열로 변환
        if rows == 1 and cols == 1:
            axes = np.array([axes])
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        
        # 각 메트릭 데이터에 대해 서브플롯에 그래프 생성
        for i, metric_data in enumerate(metrics_data):
            if i >= rows * cols:
                break  # 그리드보다 메트릭이 많은 경우 초과분 무시
            
            metric_key = metric_data.get('metric', '')
            
            # 메트릭 정의 정보 조회
            metric_info = metrics_info_dict.get(metric_key, {})
            metric_name = metric_info.get('name', metric_key)
            unit = metric_info.get('unit', '')
            threshold_warning = metric_info.get('threshold_warning')
            threshold_critical = metric_info.get('threshold_critical')
            
            # 데이터프레임 생성
            df = self.create_metric_dataframe(metric_data)
            
            if df is None or df.empty:
                continue
            
            # 현재 서브플롯 가져오기
            if rows > 1 and cols > 1:
                ax = axes[i // cols, i % cols]
            else:
                ax = axes[i]
            
            # 데이터 플롯
            ax.plot(df['datetime'], df['value'], '-o', markersize=2)
            
            # 임계값 선 추가 (존재하는 경우)
            if threshold_warning is not None:
                ax.axhline(y=threshold_warning, color='orange', linestyle='--', label='경고')
            
            if threshold_critical is not None:
                ax.axhline(y=threshold_critical, color='red', linestyle='--', label='심각')
            
            # 그래프 설정
            ax.set_title(metric_name)
            ax.set_xlabel('시간')
            ax.set_ylabel(f'값 ({unit})' if unit else '값')
            
            # x축 날짜 포맷 설정
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            
            # 범례 추가 (임계값이 있는 경우만)
            if threshold_warning is not None or threshold_critical is not None:
                ax.legend()
            
            # 그리드 추가
            ax.grid(True, linestyle='--', alpha=0.7)
        
        # 남은 빈 서브플롯 제거
        for i in range(num_metrics, rows * cols):
            if rows > 1 and cols > 1:
                fig.delaxes(axes[i // cols, i % cols])
            else:
                fig.delaxes(axes[i])
        
        # 레이아웃 조정
        plt.tight_layout(rect=[0, 0, 1, 0.97])  # top 마진을 남겨 suptitle 공간 확보
        
        # 저장 경로 생성
        site_dir = os.path.join(self.output_dir, site_name)
        if not os.path.exists(site_dir):
            os.makedirs(site_dir)
        
        # 파일명 생성
        filename = f"{server_name.replace(' ', '_')}_dashboard_{timestamp}.png"
        filepath = os.path.join(site_dir, filename)
        
        # 대시보드 저장
        fig.savefig(filepath, dpi=100)
        plt.close(fig)
        
        self.logger.info(f"대시보드 저장 완료: {filepath}")
        return filepath