import io
from datetime import datetime
from typing import Dict, Any, List
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ReportService:
    """PDF报告生成服务"""

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("请安装reportlab库: pip install reportlab")

    def generate_pdf_report(
        self,
        session_id: str,
        file_name: str,
        file_type: str,
        data: Any,
        columns: List[str],
        messages: List[Dict],
        chart_option: Dict = None,
        analysis_summary: str = None,
        sql_content: str = None,
        sql_result: Dict = None,
        chart_images: List[str] = None
    ) -> bytes:
        """
        生成完整的PDF分析报告

        Args:
            session_id: 会话ID
            file_name: 文件名
            file_type: 文件类型 (csv/sql/xlsx)
            data: 数据（DataFrame dict或list）
            columns: 列名列表
            messages: 对话消息列表
            chart_option: 图表配置（可选）
            analysis_summary: 分析摘要（可选）
            sql_content: SQL文件内容（可选）
            sql_result: SQL执行结果（可选）

        Returns:
            PDF文件的字节流
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # 样式定义
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1677ff')
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#333333')
        )
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#666666')
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=8,
            alignment=TA_JUSTIFY
        )

        story = []

        # 1. 报告标题
        story.append(Paragraph(f"数据分析报告", title_style))
        story.append(Spacer(1, 0.3*inch))

        # 2. 基本信息
        story.append(Paragraph("📋 一、基本信息", heading_style))
        basic_info = [
            ['项目', '详情'],
            ['会话ID', session_id[:8] + '...' if len(session_id) > 8 else session_id],
            ['文件名', file_name],
            ['文件类型', file_type.upper()],
            ['生成时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['数据行数', f"{len(data) if isinstance(data, list) else 'N/A'} 行"],
            ['列数', f"{len(columns)} 列"]
        ]
        table = Table(basic_info, colWidths=[3*cm, 10*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1677ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.4*inch))

        # 3. 数据概览
        story.append(Paragraph("📊 二、数据概览", heading_style))
        story.append(Paragraph(f"<b>文件</b>：{file_name}", subheading_style))

        # 显示数据表格（最多显示前20行）
        if isinstance(data, list) and len(data) > 0:
            display_data = data[:20]
            header_row = columns[:10]  # 最多显示10列
            table_data = [header_row]

            for row in display_data:
                row_data = []
                for col in header_row:
                    value = row.get(col, '') if isinstance(row, dict) else ''
                    # 截断过长的值
                    str_value = str(value)
                    if len(str_value) > 50:
                        str_value = str_value[:47] + '...'
                    row_data.append(str_value)
                table_data.append(row_data)

            # 数据表格
            data_table = Table(table_data, colWidths=[2.5*cm] * min(len(header_row), 8))
            data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4096ff')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(data_table)

            if len(data) > 20:
                story.append(Paragraph(f"<i>注：仅显示前20条数据，共{len(data)}条记录</i>", body_style))
        else:
            story.append(Paragraph("<i>暂无数据</i>", body_style))

        story.append(Spacer(1, 0.4*inch))

        # 4. 对话记录
        if messages and len(messages) > 0:
            story.append(PageBreak())
            story.append(Paragraph("💬 三、对话记录", heading_style))

            for i, msg in enumerate(messages[-20:], 1):  # 最近20条消息
                role = msg.get('role', '')
                content = msg.get('content', '')

                if role == 'user':
                    role_label = "👤 用户"
                    bg_color = colors.HexColor('#e6f7ff')
                elif role == 'ai':
                    role_label = "🤖 AI助手"
                    bg_color = colors.HexColor('#f6ffed')
                else:
                    role_label = "ℹ️ 系统"
                    bg_color = colors.HexColor('#fff7e6')

                # 消息标题
                story.append(Paragraph(f"<b>{role_label}</b> ({i})", subheading_style))

                # 消息内容（处理长文本）
                content_str = str(content)
                if len(content_str) > 500:
                    content_str = content_str[:497] + '...'

                # 转义HTML特殊字符并换行
                content_formatted = content_str.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')

                msg_table = Table([[Paragraph(content_formatted, body_style)]], colWidths=[14*cm])
                msg_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(msg_table)
                story.append(Spacer(1, 0.1*inch))

        # 5. 分析总结
        if analysis_summary:
            story.append(PageBreak())
            story.append(Paragraph("📝 四、分析总结", heading_style))

            summary_text = str(analysis_summary)
            if len(summary_text) > 2000:
                summary_text = summary_text[:1997] + '...'

            # 格式化Markdown
            summary_formatted = self._format_markdown_for_pdf(summary_text)

            summary_table = Table([[Paragraph(summary_formatted, body_style)]], colWidths=[14*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fffbe6')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#ffe58f')),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(summary_table)

        # 6. 图表（如果有）
        if chart_images:
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("📈 五、分析图表", heading_style))
            for i, img_b64 in enumerate(chart_images):
                try:
                    import base64
                    img_bytes = base64.b64decode(img_b64.split(',')[-1] if ',' in img_b64 else img_b64)
                    from reportlab.lib.utils import ImageReader
                    img_reader = ImageReader(io.BytesIO(img_bytes))
                    iw, ih = img_reader.getSize()
                    max_w = 14 * cm
                    max_h = 10 * cm
                    ratio = min(max_w / iw, max_h / ih)
                    story.append(Image(img_reader, width=iw * ratio, height=ih * ratio))
                    if len(chart_images) > 1:
                        story.append(Paragraph(f"<i>图表 {i+1}</i>", body_style))
                    story.append(Spacer(1, 0.2*inch))
                except Exception:
                    story.append(Paragraph(f"<i>图表 {i+1} 无法渲染</i>", body_style))
        elif chart_option:
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("📈 五、图表配置", heading_style))
            story.append(Paragraph("<i>本次分析生成了可视化图表，可在系统中查看交互式图表。</i>", body_style))

        # 生成PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _format_markdown_for_pdf(self, text: str) -> str:
        """将简单的Markdown转换为ReportLab可识别的格式"""
        import re
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'```(\w*)\n?(.*?)```', r'<font face="Courier" size="9">\2</font>', text, flags=re.DOTALL)
        text = text.replace('\n\n', '<br/><br/>').replace('\n', '<br/>')

        return text


# 单例实例
_report_service_instance = None

def get_report_service() -> ReportService:
    """获取ReportService单例"""
    global _report_service_instance
    if _report_service_instance is None:
        _report_service_instance = ReportService()
    return _report_service_instance
