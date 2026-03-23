# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from datetime import datetime, timedelta, date
import json
import logging

_logger = logging.getLogger(__name__)

class DashboardAI(http.Controller):

    @http.route('/dashboard/data', type='json', auth='user', methods=['POST'], csrf=False)
    def get_dashboard_data(self):
        """Lấy dữ liệu thống kê"""
        try:
            # NHÂN SỰ
            nhan_viens = request.env['nhan_vien'].search([])
            tong_nv = len(nhan_viens)
            
            # Đếm theo độ tuổi
            nv_duoi30 = 0
            nv_30_45 = 0
            nv_tren45 = 0
            tong_tuoi = 0
            
            for nv in nhan_viens:
                if nv.tuoi:
                    tong_tuoi += nv.tuoi
                    if nv.tuoi < 30:
                        nv_duoi30 += 1
                    elif nv.tuoi <= 45:
                        nv_30_45 += 1
                    else:
                        nv_tren45 += 1
            
            tuoi_tb = round(tong_tuoi / tong_nv, 1) if tong_nv else 0
            
            # KHÁCH HÀNG
            khach_hangs = request.env['khach_hang'].search([])
            tong_kh = len(khach_hangs)
            
            # HỖ TRỢ KHÁCH HÀNG
            ho_tros = request.env['ho_tro_khach_hang'].search([])
            tong_ht = len(ho_tros)
            
            # Đếm hỗ trợ mới 7 ngày
            seven_days_ago = datetime.now() - timedelta(days=7)
            ht_moi = 0
            for ht in ho_tros:
                if ht.thoi_gian_bat_dau and ht.thoi_gian_bat_dau >= seven_days_ago:
                    ht_moi += 1
            
            # Đếm hỗ trợ đang chờ
            ht_cho = 0
            for ht in ho_tros:
                if ht.trang_thai == 'pending':
                    ht_cho += 1
            
            # Điểm đánh giá trung bình
            tong_diem = 0
            so_danh_gia = 0
            for ht in ho_tros:
                if ht.diem_danh_gia and ht.diem_danh_gia > 0:
                    tong_diem += ht.diem_danh_gia
                    so_danh_gia += 1
            danh_gia_tb = round(tong_diem / so_danh_gia, 1) if so_danh_gia else 0
            
            # VĂN BẢN
            vb_den = request.env['van_ban_den'].search([]) if 'van_ban_den' in request.env else []
            vb_di = request.env['van_ban_di'].search([]) if 'van_ban_di' in request.env else []
            tong_vb = len(vb_den) + len(vb_di)
            
            # Lấy tháng hiện tại
            today = date.today()
            current_month = today.month
            current_year = today.year
            
            # Tháng trước
            if current_month == 1:
                last_month = 12
                last_month_year = current_year - 1
            else:
                last_month = current_month - 1
                last_month_year = current_year
            
            # Đếm văn bản đến tháng này
            vb_den_thang_nay = 0
            for vb in vb_den:
                if vb.ngay_van_ban:
                    if vb.ngay_van_ban.month == current_month and vb.ngay_van_ban.year == current_year:
                        vb_den_thang_nay += 1
            
            # Đếm văn bản đến tháng trước
            vb_den_thang_truoc = 0
            for vb in vb_den:
                if vb.ngay_van_ban:
                    if vb.ngay_van_ban.month == last_month and vb.ngay_van_ban.year == last_month_year:
                        vb_den_thang_truoc += 1
            
            # Đếm văn bản đi tháng này
            vb_di_thang_nay = 0
            for vb in vb_di:
                if vb.ngay_van_ban:
                    if vb.ngay_van_ban.month == current_month and vb.ngay_van_ban.year == current_year:
                        vb_di_thang_nay += 1
            
            # Đếm văn bản đi tháng trước
            vb_di_thang_truoc = 0
            for vb in vb_di:
                if vb.ngay_van_ban:
                    if vb.ngay_van_ban.month == last_month and vb.ngay_van_ban.year == last_month_year:
                        vb_di_thang_truoc += 1
            
            # Tổng hợp
            vb_thang_nay = vb_den_thang_nay + vb_di_thang_nay
            vb_thang_truoc = vb_den_thang_truoc + vb_di_thang_truoc
            
            # Tỷ lệ tăng trưởng
            tang_truong = 0
            if vb_thang_truoc > 0:
                tang_truong = round((vb_thang_nay - vb_thang_truoc) / vb_thang_truoc * 100, 1)
            
            return {
                'nhan_su': {
                    'tong': tong_nv,
                    'duoi30': nv_duoi30,
                    '30_45': nv_30_45,
                    'tren45': nv_tren45,
                    'tuoi_tb': tuoi_tb,
                },
                'khach_hang': {
                    'tong': tong_kh,
                    'ho_tro': {
                        'tong': tong_ht,
                        'moi': ht_moi,
                        'cho': ht_cho,
                        'danh_gia': danh_gia_tb,
                    }
                },
                'van_ban': {
                    'tong': tong_vb,
                    'den': len(vb_den),
                    'di': len(vb_di),
                    'thang_nay': vb_thang_nay,
                    'thang_truoc': vb_thang_truoc,
                    'tang_truong': tang_truong,
                }
            }
        except Exception as e:
            _logger.error("Error in get_dashboard_data: %s", str(e))
            return {'error': str(e)}

    @http.route('/ai/predict/<int:nhan_vien_id>', type='json', auth='user', methods=['POST'], csrf=False)
    def predict_workload(self, nhan_vien_id):
        """Dự đoán khối lượng công việc cho nhân viên"""
        try:
            nhan_vien = request.env['nhan_vien'].browse(nhan_vien_id)
            if not nhan_vien:
                return {'error': 'Không tìm thấy nhân viên'}
            
            # Lấy dữ liệu 4 tuần gần nhất
            today = datetime.now()
            lich_su = []
            
            _logger.info("=== PREDICT FOR: %s (ID: %s) ===", nhan_vien.ho_va_ten, nhan_vien.id)
            _logger.info("Current date: %s", today.strftime('%Y-%m-%d %H:%M:%S'))
            
            # Tính từ tuần gần nhất (week=1) đến tuần xa nhất (week=4)
            # week=1: từ 0-7 ngày trước (gần nhất)
            # week=2: từ 7-14 ngày trước
            # week=3: từ 14-21 ngày trước
            # week=4: từ 21-28 ngày trước
            for week in range(1, 5):
                # Tính ngày bắt đầu và kết thúc của tuần
                end_date = today - timedelta(days=7*(week-1))
                start_date = today - timedelta(days=7*week)
                
                _logger.info("Week %s: from %s to %s", week, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                
                # Văn bản xử lý
                vb_count = 0
                if 'van_ban_den' in request.env:
                    vb_count = request.env['van_ban_den'].search_count([
                        ('nhan_vien_xu_ly_id', '=', nhan_vien.id),
                        ('ngay_van_ban', '>=', start_date.date()),
                        ('ngay_van_ban', '<', end_date.date())
                    ])
                
                # Hỗ trợ khách hàng
                ht_count = 0
                if 'ho_tro_khach_hang' in request.env:
                    ht_count = request.env['ho_tro_khach_hang'].search_count([
                        ('nhan_vien_phu_trach', '=', nhan_vien.id),
                        ('thoi_gian_bat_dau', '>=', start_date),
                        ('thoi_gian_bat_dau', '<', end_date)
                    ])
                
                lich_su.append(vb_count + ht_count)
                _logger.info("Week %s: VB=%s, HT=%s, Total=%s", week, vb_count, ht_count, vb_count + ht_count)
            
            # Dự đoán bằng trung bình động (tuần gần nhất trọng số cao)
            if sum(lich_su) == 0:
                du_doan = 0
                do_tin_cay = 0
            else:
                # lich_su[0] = tuần 1 (gần nhất), lich_su[3] = tuần 4 (xa nhất)
                du_doan = round(lich_su[0]*0.4 + lich_su[1]*0.3 + lich_su[2]*0.2 + lich_su[3]*0.1, 1)
                
                # Độ tin cậy dựa trên độ biến động
                avg = sum(lich_su) / 4
                bien_dong = sum(abs(x - avg) for x in lich_su) / 4
                do_tin_cay = round(max(50, min(95, 100 - bien_dong * 5)), 1)
            
            # Lưu dự đoán
            try:
                if 'ai.prediction' in request.env:
                    request.env['ai.prediction'].create({
                        'nhan_vien_id': nhan_vien.id,
                        'khoi_luong_du_doan': du_doan,
                        'do_tin_cay': do_tin_cay,
                    })
            except Exception as e:
                _logger.warning("Could not save prediction: %s", str(e))
            
            # Khuyến nghị
            if du_doan > 15:
                khuyen_nghi = "🔴 NHÂN VIÊN QUÁ TẢI! Cần phân công lại công việc."
            elif du_doan > 10:
                khuyen_nghi = "🟡 CÔNG VIỆC CAO. Cần theo dõi sát sao."
            elif du_doan > 5:
                khuyen_nghi = "🟢 ỔN ĐỊNH. Khối lượng công việc phù hợp."
            elif du_doan > 0:
                khuyen_nghi = "🔵 NHÀN RỖI. Có thể giao thêm việc."
            else:
                khuyen_nghi = "⚪ CHƯA CÓ DỮ LIỆU. Cần giao việc để đánh giá."
            
            return {
                'nhan_vien': nhan_vien.ho_va_ten,
                'du_doan': du_doan,
                'do_tin_cay': do_tin_cay,
                'lich_su': lich_su,
                'khuyen_nghi': khuyen_nghi
            }
        except Exception as e:
            _logger.error("Error in predict_workload: %s", str(e))
            return {'error': str(e)}

    @http.route('/ai/train_model', type='json', auth='user', methods=['POST'], csrf=False)
    def train_model(self):
        """Route huấn luyện AI model"""
        try:
            _logger.info("=== TRAIN MODEL ROUTE CALLED ===")
            
            # Lấy model manager đang hoạt động
            model_manager = request.env['ai.model.manager'].search([('is_active', '=', True)], limit=1)
            if not model_manager:
                # Tạo mới model manager
                model_manager = request.env['ai.model.manager'].create({
                    'name': 'AI Prediction Model',
                    'model_type': 'random_forest',
                    'is_active': True
                })
                _logger.info("Đã tạo mới AI Model Manager")
            
            # Gọi hàm huấn luyện
            result = model_manager.action_train_model()
            
            _logger.info("Train result: %s", result)
            return result
            
        except Exception as e:
            _logger.error(f"Error training model: {str(e)}", exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True
                }
            }