# ai_model.py (nâng cấp với AI thực)
from odoo import models, fields, api
from datetime import timedelta
import json
import logging

_logger = logging.getLogger(__name__)

class AIPrediction(models.Model):
    _name = 'ai.prediction'
    _description = 'Dự đoán AI'
    _rec_name = 'nhan_vien_id'
    _order = 'ngay_du_doan desc'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên', required=True)
    ngay_du_doan = fields.Date(string='Ngày dự đoán', default=fields.Date.today)
    
    # Dự đoán chi tiết
    khoi_luong_du_doan = fields.Float(string='Khối lượng công việc dự đoán (cv/ngày)')
    do_tin_cay = fields.Float(string='Độ tin cậy (%)', default=75)
    workload_trend = fields.Selection([
        ('increasing', 'Tăng mạnh'),
        ('stable', 'Ổn định'),
        ('decreasing', 'Giảm')
    ], string='Xu hướng', compute='_compute_trend')
    
    # Dự đoán khác
    ngay_qua_tai = fields.Date(string='Ngày dự đoán quá tải')
    muc_do_stress = fields.Selection([
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('critical', 'Nghiêm trọng')
    ], string='Mức độ căng thẳng', compute='_compute_stress_level')
    
    # Lịch sử dự đoán
    prediction_history = fields.Text(string='Lịch sử dự đoán')
    
    # Phân tích chi tiết
    phan_tich_chi_tiet = fields.Text(string='Phân tích chi tiết')
    khuyen_nghi_chi_tiet = fields.Text(string='Khuyến nghị chi tiết')
    
    @api.depends('khoi_luong_du_doan')
    def _compute_trend(self):
        for record in self:
            # Lấy 3 lần dự đoán gần nhất
            previous_predictions = self.search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('id', '<', record.id)
            ], limit=3, order='id desc')
            
            if len(previous_predictions) >= 2:
                trend = previous_predictions[0].khoi_luong_du_doan - previous_predictions[1].khoi_luong_du_doan
                if trend > 2:
                    record.workload_trend = 'increasing'
                elif trend < -2:
                    record.workload_trend = 'decreasing'
                else:
                    record.workload_trend = 'stable'
            else:
                record.workload_trend = 'stable'
    
    @api.depends('khoi_luong_du_doan')
    def _compute_stress_level(self):
        for record in self:
            if record.khoi_luong_du_doan > 20:
                record.muc_do_stress = 'critical'
            elif record.khoi_luong_du_doan > 15:
                record.muc_do_stress = 'high'
            elif record.khoi_luong_du_doan > 10:
                record.muc_do_stress = 'medium'
            else:
                record.muc_do_stress = 'low'
    
    def generate_detailed_analysis(self):
        """Tạo phân tích chi tiết"""
        for record in self:
            nv = record.nhan_vien_id
            
            # Phân tích hiệu suất
            analysis = f"""
            📊 **PHÂN TÍCH HIỆU SUẤT NHÂN VIÊN**
            
            👤 Nhân viên: {nv.ho_va_ten}
            📅 Ngày dự đoán: {record.ngay_du_doan}
            
            📈 **KHỐI LƯỢNG CÔNG VIỆC**
            • Dự đoán: {record.khoi_luong_du_doan} công việc/ngày
            • Độ tin cậy: {record.do_tin_cay}%
            • Xu hướng: {dict(record._fields['workload_trend'].selection).get(record.workload_trend)}
            
            🎯 **ĐÁNH GIÁ**
            """
            
            if record.khoi_luong_du_doan > 15:
                analysis += """
            ⚠️ **CẢNH BÁO QUÁ TẢI**
            • Mức độ căng thẳng: Cao/Nghiêm trọng
            • Nguy cơ: Burnout, giảm chất lượng công việc
            • Cần can thiệp ngay lập tức
            """
            elif record.khoi_luong_du_doan > 10:
                analysis += """
            🟡 **CẦN THEO DÕI**
            • Mức độ căng thẳng: Trung bình
            • Nguy cơ: Có thể bị quá tải trong tương lai gần
            • Cần phân bổ lại công việc hợp lý
            """
            else:
                analysis += """
            🟢 **ỔN ĐỊNH**
            • Mức độ căng thẳng: Thấp
            • Có thể nhận thêm công việc nếu cần
            • Hiệu suất tốt
            """
            
            record.phan_tich_chi_tiet = analysis
            record._generate_recommendations()
    
    def _generate_recommendations(self):
        """Tạo khuyến nghị chi tiết"""
        for record in self:
            nv = record.nhan_vien_id
            recommendations = []
            
            if record.khoi_luong_du_doan > 15:
                recommendations.append("🔴 **HÀNH ĐỘNG KHẨN CẤP:**")
                recommendations.append("• Giảm tải ngay lập tức 30-40% công việc")
                recommendations.append("• Phân công hỗ trợ từ đồng nghiệp")
                recommendations.append("• Kiểm tra sức khỏe tinh thần của nhân viên")
                recommendations.append("• Tạm dừng giao việc mới trong 1 tuần")
            elif record.khoi_luong_du_doan > 10:
                recommendations.append("🟡 **KHUYẾN NGHỊ:**")
                recommendations.append("• Giảm 15-20% khối lượng công việc")
                recommendations.append("• Ưu tiên các công việc quan trọng nhất")
                recommendations.append("• Họp đánh giá tình hình hàng tuần")
                recommendations.append("• Cân nhắc tuyển thêm nhân sự nếu kéo dài")
            elif record.khoi_luong_du_doan > 5:
                recommendations.append("🟢 **KHUYẾN NGHỊ:**")
                recommendations.append("• Duy trì khối lượng công việc hiện tại")
                recommendations.append("• Có thể giao thêm các dự án phát triển")
                recommendations.append("• Khuyến khích đào tạo nâng cao kỹ năng")
            else:
                recommendations.append("🔵 **KHUYẾN NGHỊ:**")
                recommendations.append("• Tăng cường giao việc để tận dụng nguồn lực")
                recommendations.append("• Phân công thêm các dự án mới")
                recommendations.append("• Đào tạo để nâng cao năng lực")
            
            # Thêm khuyến nghị về đào tạo
            recommendations.append("\n📚 **ĐỀ XUẤT ĐÀO TẠO:**")
            if record.khoi_luong_du_doan > 10:
                recommendations.append("• Kỹ năng quản lý thời gian")
                recommendations.append("• Kỹ năng ưu tiên công việc")
            else:
                recommendations.append("• Kỹ năng nâng cao chuyên môn")
                recommendations.append("• Kỹ năng lãnh đạo dự án")
            
            record.khuyen_nghi_chi_tiet = '\n'.join(recommendations)
    
    def action_train_ai_model(self):
        """Nút huấn luyện AI model"""
        try:
            _logger.info("=== ACTION TRAIN AI MODEL CALLED ===")
            
            # Lấy model manager đang hoạt động
            model_manager = self.env['ai.model.manager'].get_active_model()
            
            if not model_manager:
                # Tạo mới model manager
                model_manager = self.env['ai.model.manager'].create({
                    'name': 'AI Prediction Model',
                    'model_type': 'random_forest',
                    'is_active': True
                })
                _logger.info("Đã tạo mới AI Model Manager")
            
            # Gọi hàm huấn luyện
            result = model_manager.action_train_model()
            
            # Trả về kết quả
            return result
            
        except Exception as e:
            _logger.error(f"Lỗi huấn luyện AI: {str(e)}", exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': f'Không thể huấn luyện AI: {str(e)}',
                    'type': 'danger',
                    'sticky': True
                }
            }