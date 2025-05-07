# modules/reports/pdf_generator.py
import os
import time
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
from ..utils.logger import setup_logger

class PDFReport(FPDF):
    """
    PDF 보고서 클래스 (FPDF 확장)
    """
    def __init__(self, title="서버 메트릭 보고서", format='A4', unit='mm', font='NanumGothic'):
        """
        PDF 보고서 초기화
        """
        super().__init__(orientation='P', unit=unit, format=format)
        self.title = title
        self.default_font = font
        self.logger = setup_logger()
        
        # 기본 여백 설정
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(True, margin=15)
        
        # 문서 정보 설정
        self.set_creator('네이버 클라우드 인사이트 보고서')
        self.set_author('자동화 시스템')
        self.set_title(title)
        
        # 한글 지원을 위한 폰트 추가
        try:
            self.add_font(font, '', os.path.join('fonts', f'{font}.ttf'), uni=True)
            self.logger.info(f"'{font}' 폰트가 성공적으로 로드되었습니다.")
        except Exception as e:
            self.logger.warning(f"한글 폰트 로드 실패, 기본 폰트 사용: {str(e)}")
    
    def header(self):
        """
        페이지 헤더
        """
        # 로고 (옵션)
        # self.image('logo.png', 10, 8, 33)
        
        # 타이틀
        try:
            self.set_font(self.default_font, '', 15)
        except:
            self.set_font('Arial', 'B', 15)
        
        self.cell(0, 10, self.title, 0, 1, 'C')
        
        # 생성 일시
        self.set_font('Arial', 'I', 8)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cell(0, 5, f'생성일시: {now}', 0, 1, 'R')
        
        # 구분선
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)
    
    def footer(self):
        """
        페이지 푸터
        """
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        
        # 페이지 번호
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        """
        챕터 제목
        """
        try:
            self.set_font(self.default_font, 'B', 12)
        except:
            self.set_font('Arial', 'B', 12)
        
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, title, 0, 1, 'L', 1)
        self.ln(4)
    
    def section_title(self, title):
        """
        섹션 제목
        """
        try:
            self.set_font(self.default_font, 'B', 10)
        except:
            self.set_font('Arial', 'B', 10)
        
        self.set_text_color(0, 0, 140)
        self.cell(0, 6, title, 0, 1, 'L')
        self.set_text_color(0, 0, 0)
        self.ln(2)
    
    def body_text(self, text):
        """
        본문 텍스트
        """
        try:
            self.set_font(self.default_font, '', 9)
        except:
            self.set_font('Arial', '', 9)
        
        self.multi_cell(0, 5, text)
        self.ln(2)
    
    def key_value_table(self, data, widths=(60, 130)):
        """
        키-값 테이블
        """
        try:
            self.set_font(self.default_font, '', 9)
        except:
            self.set_font('Arial', '', 9)
        
        # 테이블 머리글
        self.set_fill_color(240, 240, 240)
        self.set_text_color(0, 0, 0)
        
        # 데이터 행
        fill = False
        for key, value in data.items():
            self.set_fill_color(240, 240, 240)
            if fill:
                self.set_fill_color(224, 235, 255)
            
            # 기본 값 처리
            if isinstance(value, float):
                value = round(value, 2)
            elif value is None:
                value = '-'
            
            self.cell(widths[0], 6, str(key), 1, 0, 'L', fill)
            self.cell(widths[1], 6, str(value), 1, 1, 'L', fill)
            fill = not fill
        
        self.ln(4)
    
    def add_image(self, image_path, w=0, h=0, caption=None):
        """
        이미지 추가
        """
        if not os.path.exists(image_path):
            self.logger.warning(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            return False
        
        try:
            # 현재 Y 위치 확인
            current_y = self.get_y()
            
            # 이미지 크기 조정 (필요한 경우)
            if w == 0 and h == 0:
                # 여백을 고려한 최대 너비
                max_width = self.w - self.l_margin - self.r_margin
                self.image(image_path, x=self.l_margin, y=current_y, w=max_width)
            else:
                self.image(image_path, x=self.l_margin, y=current_y, w=w, h=h)
            
            # 캡션 추가 (있는 경우)
            if caption:
                self.ln(2)
                try:
                    self.set_font(self.default_font, 'I', 8)
                except:
                    self.set_font('Arial', 'I', 8)
                
                self.cell(0, 5, caption, 0, 1, 'C')
            
            self.ln(5)
            return True
        
        except Exception as e:
            self.logger.error(f"이미지 추가 중 오류 발생: {str(e)}")
            return False


class ReportGenerator:
    """
    PDF 보고서 생성기 클래스
    """
    def __init__(self, output_dir="output"):
        """
        초기화
        
        Args:
            output_dir (str): 출력 디렉토리
        """
        self.logger = setup_logger()
        self.output_dir = output_dir
        
        # 출력 디렉토리가 없으면 생성
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def generate_server_report(self, site_name, server_name, metrics_data, metrics_info, metrics_analysis):
        """
        단일 서버에 대한 보고서 생성
        
        Args:
            site_name (str): 사이트 이름
            server_name (str): 서버 이름
            metrics_data (list): 메트릭 데이터 목록
            metrics_info (list): 메트릭 정의 정보 목록
            metrics_analysis (dict): 메트릭 분석 결과
            
        Returns:
            str: 저장된 PDF 파일 경로
        """
        # 메트릭 정의 정보를 딕셔너리로 변환
        metrics_info_dict = {info.get('key'): info for info in metrics_info} if metrics_info else {}
        
        # 보고서 제목
        report_title = f"{site_name} - {server_name} 서버 메트릭 보고서"
        
        # PDF 객체 생성
        pdf = PDFReport(title=report_title)
        pdf.add_page()
        
        # 보고서 개요
        pdf.chapter_title("1. 보고서 개요")
        
        # 서버 정보
        pdf.section_title("1.1 서버 정보")
        server_info = {
            "사이트명": site_name,
            "서버명": server_name,
            "보고서 생성일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        pdf.key_value_table(server_info)
        
        # 메트릭 요약
        pdf.section_title("1.2 메트릭 요약")
        metrics_summary = {}
        for metric_data in metrics_data:
            metric_key = metric_data.get('metric', '')
            metric_info = metrics_info_dict.get(metric_key, {})
            metric_name = metric_info.get('name', metric_key)
            
            # 분석 결과에서 요약 정보 추출
            analysis = metrics_analysis.get(metric_key, {})
            if analysis and 'statistics' in analysis:
                stats = analysis['statistics']
                metrics_summary[metric_name] = f"평균: {round(stats.get('mean', 0), 2)}, 최대: {round(stats.get('max', 0), 2)}"
            else:
                metrics_summary[metric_name] = "데이터 부족"
        
        pdf.key_value_table(metrics_summary)
        
        # 각 메트릭에 대한 상세 분석
        pdf.chapter_title("2. 메트릭 상세 분석")
        
        section_num = 1
        for metric_data in metrics_data:
            metric_key = metric_data.get('metric', '')
            metric_info = metrics_info_dict.get(metric_key, {})
            metric_name = metric_info.get('name', metric_key)
            
            # 섹션 제목
            pdf.section_title(f"2.{section_num} {metric_name} 분석")
            section_num += 1
            
            # 메트릭 설명 (있는 경우)
            description = metric_info.get('description', '')
            if description:
                pdf.body_text(f"설명: {description}")
            
            # 분석 결과에서 정보 추출
            analysis = metrics_analysis.get(metric_key, {})
            if not analysis:
                pdf.body_text("이 메트릭에 대한 분석 결과가 없습니다.")
                continue
            
            # 통계 정보
            if 'statistics' in analysis:
                stats = analysis['statistics']
                if stats:
                    pdf.body_text("기본 통계:")
                    stats_info = {
                        "데이터 포인트": stats.get('count', 0),
                        "최소값": round(stats.get('min', 0), 2),
                        "최대값": round(stats.get('max', 0), 2),
                        "평균": round(stats.get('mean', 0), 2),
                        "중앙값": round(stats.get('median', 0), 2),
                        "표준편차": round(stats.get('std', 0), 2)
                    }
                    pdf.key_value_table(stats_info)
            
            # 이상치 정보
            if 'anomalies' in analysis:
                anomalies = analysis['anomalies']
                if anomalies:
                    pdf.body_text("이상치 탐지 결과:")
                    
                    if anomalies.get('warning') or anomalies.get('critical'):
                        warning_count = len(anomalies.get('warning', []))
                        critical_count = len(anomalies.get('critical', []))
                        outlier_count = len(anomalies.get('outliers', []))
                        
                        anomaly_info = {
                            "경고 이상치": f"{warning_count}개 발견",
                            "심각 이상치": f"{critical_count}개 발견",
                            "통계적 이상치": f"{outlier_count}개 발견"
                        }
                        pdf.key_value_table(anomaly_info)
            
            # 기간 비교 정보
            if 'period_comparison' in analysis:
                period_comp = analysis['period_comparison']
                if period_comp:
                    pdf.body_text("기간 비교 분석:")
                    
                    current = period_comp.get('current_period', {})
                    previous = period_comp.get('previous_period', {})
                    changes = period_comp.get('changes', {})
                    
                    if current and previous and changes:
                        comp_info = {
                            "현재 기간 평균": round(current.get('mean', 0), 2),
                            "이전 기간 평균": round(previous.get('mean', 0), 2),
                            "평균 변화율": f"{round(changes.get('mean_change', 0), 2)}%",
                            "최대값 변화율": f"{round(changes.get('max_change', 0), 2)}%"
                        }
                        pdf.key_value_table(comp_info)
            
            # 그래프 이미지 추가 (서버 디렉토리에서 찾기)
            graph_filename = f"{metric_key}.png"
            site_dir = os.path.join(self.output_dir, site_name)
            server_dir = os.path.join(site_dir, server_name.replace(' ', '_'))
            graph_path = os.path.join(server_dir, graph_filename)
            
            # 이미지 파일이 존재하는 경우 추가
            if os.path.exists(graph_path):
                # 새 페이지가 필요한지 확인 (여유 공간 확인)
                if pdf.get_y() > 180:  # A4 페이지의 경우 약 270이 최대 높이, 그래프는 크므로 180 정도에서 새 페이지
                    pdf.add_page()
                
                pdf.add_image(graph_path, caption=f"{metric_name} 추이 그래프")
            else:
                pdf.body_text("그래프 이미지를 찾을 수 없습니다.")
            
            # 구분선
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(5)
        
        # 대시보드 이미지 추가
        pdf.add_page()
        pdf.chapter_title("3. 종합 대시보드")
        
        dashboard_filename = "dashboard.png"
        dashboard_path = os.path.join(os.path.join(self.output_dir, site_name), 
                                     server_name.replace(' ', '_'), 
                                     dashboard_filename)
        
        if os.path.exists(dashboard_path):
            pdf.add_image(dashboard_path, caption="종합 메트릭 대시보드")
        else:
            pdf.body_text("대시보드 이미지를 찾을 수 없습니다.")
        
        # 결론 및 권장사항
        pdf.add_page()
        pdf.chapter_title("4. 결론 및 권장사항")
        
        # 분석된 데이터를 기반으로 간단한 결론 도출
        warnings_detected = False
        critical_detected = False
        
        for analysis in metrics_analysis.values():
            if 'anomalies' in analysis:
                anomalies = analysis['anomalies']
                if anomalies and anomalies.get('warning'):
                    warnings_detected = True
                if anomalies and anomalies.get('critical'):
                    critical_detected = True
        
        if critical_detected:
            pdf.body_text("분석 결과, 일부 메트릭에서 심각 수준의 이상치가 발견되었습니다. 즉각적인 조치가 필요합니다.")
        elif warnings_detected:
            pdf.body_text("분석 결과, 일부 메트릭에서 경고 수준의 이상치가 발견되었습니다. 주의 깊은 모니터링이 필요합니다.")
        else:
            pdf.body_text("분석 결과, 모든 메트릭이 정상 범위 내에서 운영되고 있습니다.")
        
        # 파일 저장 경로 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"{server_name.replace(' ', '_')}_{timestamp}.pdf"
        pdf_dir = os.path.join(self.output_dir, site_name, "pdf")
        
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        
        # PDF 저장
        try:
            pdf.output(pdf_path)
            self.logger.info(f"PDF 보고서 생성 완료: {pdf_path}")
            return pdf_path
        except Exception as e:
            self.logger.error(f"PDF 보고서 저장 중 오류 발생: {str(e)}")
            return None
    
    def generate_site_report(self, site_name, servers_data, metrics_info):
        """
        사이트 전체에 대한 종합 보고서 생성
        
        Args:
            site_name (str): 사이트 이름
            servers_data (dict): 각 서버별 메트릭 데이터 및 분석 결과
            metrics_info (list): 메트릭 정의 정보 목록
            
        Returns:
            str: 저장된 PDF 파일 경로
        """
        # 보고서 제목
        report_title = f"{site_name} 사이트 종합 보고서"
        
        # PDF 객체 생성
        pdf = PDFReport(title=report_title)
        pdf.add_page()
        
        # 보고서 개요
        pdf.chapter_title("1. 종합 보고서 개요")
        
        # 사이트 정보
        pdf.section_title("1.1 사이트 정보")
        site_info = {
            "사이트명": site_name,
            "서버 수": len(servers_data),
            "보고서 생성일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        pdf.key_value_table(site_info)
        
        # 서버 목록
        pdf.section_title("1.2 서버 목록")
        for server_name in servers_data.keys():
            pdf.body_text(f"- {server_name}")
        pdf.ln(5)
        
        # 사이트 전체 요약
        pdf.chapter_title("2. 사이트 전체 요약")
        
        # 메트릭 정보를 딕셔너리로 변환
        metrics_info_dict = {info.get('key'): info for info in metrics_info} if metrics_info else {}
        
        # 각 메트릭 유형별로 전체 서버의 평균/최대 계산
        metric_keys = list(set([key for server_data in servers_data.values() 
                               for key in server_data.get('metrics_analysis', {}).keys()]))
        
        for metric_key in metric_keys:
            metric_info = metrics_info_dict.get(metric_key, {})
            metric_name = metric_info.get('name', metric_key)
            
            pdf.section_title(f"2.{metric_keys.index(metric_key) + 1} {metric_name} 요약")
            
            # 모든 서버의 이 메트릭에 대한 통계 수집
            server_values = {}
            all_means = []
            all_maxes = []
            
            for server_name, server_data in servers_data.items():
                analysis = server_data.get('metrics_analysis', {}).get(metric_key, {})
                if analysis and 'statistics' in analysis:
                    stats = analysis['statistics']
                    mean_value = stats.get('mean')
                    max_value = stats.get('max')
                    
                    if mean_value is not None:
                        server_values[server_name] = round(mean_value, 2)
                        all_means.append(mean_value)
                    
                    if max_value is not None:
                        all_maxes.append(max_value)
            
            # 통계 표시
            if server_values:
                pdf.body_text(f"전체 서버 평균: {round(sum(all_means) / len(all_means), 2)}")
                pdf.body_text(f"전체 서버 최대값: {round(max(all_maxes), 2)}")
                
                # 서버별 평균값 표 생성
                pdf.body_text("서버별 평균값:")
                pdf.key_value_table(server_values)
            else:
                pdf.body_text("이 메트릭에 대한 데이터가 충분하지 않습니다.")
        
        # 이상치 요약
        pdf.chapter_title("3. 이상치 요약")
        
        # 서버별 이상치 개수 계산
        anomaly_summary = {}
        
        for server_name, server_data in servers_data.items():
            warnings = 0
            criticals = 0
            
            for metric_key, analysis in server_data.get('metrics_analysis', {}).items():
                if 'anomalies' in analysis:
                    anomalies = analysis['anomalies']
                    warnings += len(anomalies.get('warning', []))
                    criticals += len(anomalies.get('critical', []))
            
            if warnings > 0 or criticals > 0:
                anomaly_summary[server_name] = f"경고: {warnings}개, 심각: {criticals}개"
        
        if anomaly_summary:
            pdf.body_text("다음 서버에서 이상치가 발견되었습니다:")
            pdf.key_value_table(anomaly_summary)
        else:
            pdf.body_text("분석된 모든 서버에서 이상치가 발견되지 않았습니다.")
        
        # 결론 및 권장사항
        pdf.add_page()
        pdf.chapter_title("4. 결론 및 권장사항")
        
        # 전체적인 상태 평가
        total_warnings = sum(len(analysis.get('anomalies', {}).get('warning', []))
                            for server_data in servers_data.values()
                            for analysis in server_data.get('metrics_analysis', {}).values())
        
        total_criticals = sum(len(analysis.get('anomalies', {}).get('critical', []))
                             for server_data in servers_data.values()
                             for analysis in server_data.get('metrics_analysis', {}).values())
        
        if total_criticals > 0:
            pdf.body_text(f"사이트 전체에서 {total_criticals}개의 심각 수준 이상치가 발견되었습니다. 즉각적인 조치가 필요합니다.")
        elif total_warnings > 0:
            pdf.body_text(f"사이트 전체에서 {total_warnings}개의 경고 수준 이상치가 발견되었습니다. 주의 깊은 모니터링이 필요합니다.")
        else:
            pdf.body_text("사이트 전체가 정상적으로 운영되고 있으며, 분석된 모든 메트릭이 정상 범위 내에 있습니다.")
        
        # 파일 저장 경로 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"{site_name}_site_report_{timestamp}.pdf"
        pdf_dir = os.path.join(self.output_dir, site_name, "pdf")
        
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        
        # PDF 저장
        try:
            pdf.output(pdf_path)
            self.logger.info(f"사이트 종합 보고서 생성 완료: {pdf_path}")
            return pdf_path
        except Exception as e:
            self.logger.error(f"사이트 종합 보고서 저장 중 오류 발생: {str(e)}")
            return None