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
            
            for week in range(1, 5):
                end_date = today - timedelta(days=7*(week-1))
                start_date = today - timedelta(days=7*week)
                
                _logger.info("Week %s: from %s to %s", week, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                
                vb_count = 0
                if 'van_ban_den' in request.env:
                    vb_count = request.env['van_ban_den'].search_count([
                        ('nhan_vien_xu_ly_id', '=', nhan_vien.id),
                        ('ngay_van_ban', '>=', start_date.date()),
                        ('ngay_van_ban', '<', end_date.date())
                    ])
                
                ht_count = 0
                if 'ho_tro_khach_hang' in request.env:
                    ht_count = request.env['ho_tro_khach_hang'].search_count([
                        ('nhan_vien_phu_trach', '=', nhan_vien.id),
                        ('thoi_gian_bat_dau', '>=', start_date),
                        ('thoi_gian_bat_dau', '<', end_date)
                    ])
                
                lich_su.append(vb_count + ht_count)
                _logger.info("Week %s: VB=%s, HT=%s, Total=%s", week, vb_count, ht_count, vb_count + ht_count)
            
            if sum(lich_su) == 0:
                du_doan = 0
                do_tin_cay = 0
            else:
                du_doan = round(lich_su[0]*0.4 + lich_su[1]*0.3 + lich_su[2]*0.2 + lich_su[3]*0.1, 1)
                avg = sum(lich_su) / 4
                bien_dong = sum(abs(x - avg) for x in lich_su) / 4
                do_tin_cay = round(max(50, min(95, 100 - bien_dong * 5)), 1)
            
            try:
                if 'ai.prediction' in request.env:
                    request.env['ai.prediction'].create({
                        'nhan_vien_id': nhan_vien.id,
                        'khoi_luong_du_doan': du_doan,
                        'do_tin_cay': do_tin_cay,
                    })
            except Exception as e:
                _logger.warning("Could not save prediction: %s", str(e))
            
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
            
            model_manager = request.env['ai.model.manager'].search([('is_active', '=', True)], limit=1)
            if not model_manager:
                model_manager = request.env['ai.model.manager'].create({
                    'name': 'AI Prediction Model',
                    'model_type': 'random_forest',
                    'is_active': True
                })
                _logger.info("Đã tạo mới AI Model Manager")
            
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
    
    @http.route('/chatbot/test', type='json', auth='user', methods=['POST'], csrf=False)
    def chatbot_test(self):
        """Route test để kiểm tra dữ liệu nhận được"""
        try:
            _logger.info("=== CHATBOT TEST ROUTE ===")
            _logger.info("Request method: %s", request.httprequest.method)
            _logger.info("Request data: %s", request.httprequest.data)
            _logger.info("Request params: %s", request.params)
            
            # Thử đọc dữ liệu theo nhiều cách
            data1 = request.params
            data2 = request.jsonrequest
            data3 = {}
            
            # Đọc raw data
            if request.httprequest.data:
                try:
                    data3 = json.loads(request.httprequest.data.decode('utf-8'))
                except:
                    pass
            
            question = ''
            if data1 and data1.get('question'):
                question = data1.get('question')
            elif data2 and data2.get('question'):
                question = data2.get('question')
            elif data3 and data3.get('question'):
                question = data3.get('question')
            
            _logger.info("Question from params: %s", data1.get('question') if data1 else None)
            _logger.info("Question from jsonrequest: %s", data2.get('question') if data2 else None)
            _logger.info("Question from raw: %s", data3.get('question') if data3 else None)
            _logger.info("Final question: %s", question)
            
            return {
                'success': True,
                'received_data': {
                    'params': data1,
                    'jsonrequest': data2,
                    'raw': data3,
                },
                'question': question
            }
        except Exception as e:
            _logger.error("Test error: %s", str(e), exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/chatbot/ask', type='json', auth='user', methods=['POST'], csrf=False)
    def chatbot_ask(self):
        """Gửi câu hỏi đến chatbot"""
        try:
            _logger.info("=== CHATBOT ASK ROUTE ===")
            
            # Thử đọc dữ liệu từ nhiều nguồn
            data = {}
            
            # Cách 1: request.params
            if request.params:
                data.update(request.params)
                _logger.info("Data from params: %s", request.params)
            
            # Cách 2: request.jsonrequest
            if request.jsonrequest:
                data.update(request.jsonrequest)
                _logger.info("Data from jsonrequest: %s", request.jsonrequest)
            
            # Cách 3: Đọc raw data
            if request.httprequest.data:
                try:
                    raw_data = json.loads(request.httprequest.data.decode('utf-8'))
                    data.update(raw_data)
                    _logger.info("Data from raw: %s", raw_data)
                except Exception as e:
                    _logger.warning("Cannot parse raw data: %s", e)
            
            question = data.get('question', '')
            model_key = data.get('model_key', None)
            session_id = data.get('session_id', None)
            
            _logger.info("Final question: '%s'", question)
            _logger.info("Question length: %d", len(question))
            
            if not question or question.strip() == '':
                _logger.warning("Empty question received")
                return {'success': False, 'error': 'Vui lòng nhập câu hỏi.'}
            
            chatbot_service = request.env['chatbot.service']
            result = chatbot_service.ask(question, model_key, session_id)
            
            _logger.info("Result from service: %s", result.get('success', False))
            return result
            
        except Exception as e:
            _logger.error("Chatbot error: %s", str(e), exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/chatbot/history', type='json', auth='user', methods=['POST'], csrf=False)
    def chatbot_history(self):
        """Lấy lịch sử chat của user"""
        try:
            data = request.params
            session_id = data.get('session_id', None)
            limit = data.get('limit', 50)
            
            _logger.info("Chatbot history - session: %s, limit: %s", session_id, limit)
            
            chat_history = request.env['chat.history']
            
            if session_id:
                messages = chat_history.get_session_messages(session_id)
            else:
                messages = chat_history.get_user_chat_history(limit)
            
            return {
                'success': True,
                'messages': messages,
                'session_id': session_id
            }
            
        except Exception as e:
            _logger.error("Chatbot history error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    @http.route('/chatbot/clear_history', type='json', auth='user', methods=['POST'], csrf=False)
    def chatbot_clear_history(self):
        """Xóa lịch sử chat của user"""
        try:
            data = request.params
            session_id = data.get('session_id', None)
            days = data.get('days', 30)
            
            _logger.info("Chatbot clear history - session: %s, days: %s", session_id, days)
            
            chat_history = request.env['chat.history']
            
            if session_id:
                records = chat_history.search([('session_id', '=', session_id)])
                count = len(records)
                records.unlink()
                return {'success': True, 'deleted': count}
            else:
                count = chat_history.cleanup_old_history(days)
                return {'success': True, 'deleted': count}
            
        except Exception as e:
            _logger.error("Chatbot clear history error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    @http.route('/chatbot/models', type='json', auth='user', methods=['GET', 'POST'], csrf=False)
    def chatbot_models(self):
        """Lấy danh sách model AI được hỗ trợ"""
        try:
            chatbot_service = request.env['chatbot.service']
            return {
                'success': True,
                'models': chatbot_service.SUPPORTED_MODELS,
                'default': chatbot_service.DEFAULT_MODEL_KEY
            }
        except Exception as e:
            _logger.error("Chatbot models error: %s", str(e))
            return {'success': False, 'error': str(e)}