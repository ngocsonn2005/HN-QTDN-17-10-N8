from odoo import http
from odoo.http import request
from datetime import datetime, timedelta, date

class DashboardAI(http.Controller):

    @http.route('/dashboard/data', type='json', auth='user', methods=['POST'])
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
            
            ho_tros = request.env['ho_tro_khach_hang'].search([])
            tong_ht = len(ho_tros)
            
            # Đếm hỗ trợ mới 7 ngày
            seven_days_ago = datetime.now() - timedelta(days=7)
            ht_moi = 0
            for ht in ho_tros:
                if ht.create_date and ht.create_date >= seven_days_ago:
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
            vb_den = request.env['van_ban_den'].search([])
            vb_di = request.env['van_ban_di'].search([])
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
                    'den': len(vb_den),           # THÊM DÒNG NÀY
                    'di': len(vb_di),              # THÊM DÒNG NÀY
                    'thang_nay': vb_thang_nay,
                    'thang_truoc': vb_thang_truoc,
                    'tang_truong': tang_truong,
                }
            }
        except Exception as e:
            return {'error': str(e)}

    @http.route('/ai/predict/<int:nhan_vien_id>', type='json', auth='user', methods=['POST'])
    def predict_workload(self, nhan_vien_id):
        """Dự đoán khối lượng công việc cho nhân viên"""
        try:
            nhan_vien = request.env['nhan_vien'].browse(nhan_vien_id)
            if not nhan_vien:
                return {'error': 'Không tìm thấy nhân viên'}
            
            # Lấy dữ liệu 4 tuần gần nhất
            today = datetime.now()
            lich_su = []
            
            for i in range(4, 0, -1):
                start = today - timedelta(weeks=i)
                end = today - timedelta(weeks=i-1)
                
                # Văn bản xử lý
                vb = request.env['van_ban_den'].search_count([
                    ('nhan_vien_xu_ly_id', '=', nhan_vien.id),
                    ('ngay_van_ban', '>=', start.date()),
                    ('ngay_van_ban', '<', end.date())
                ])
                
                # Hỗ trợ khách hàng
                ht = request.env['ho_tro_khach_hang'].search_count([
                    ('nhan_vien_phu_trach', '=', nhan_vien.id),
                    ('create_date', '>=', start),
                    ('create_date', '<', end)
                ])
                
                lich_su.append(vb + ht)
            
            # Dự đoán bằng trung bình động
            if sum(lich_su) == 0:
                du_doan = 0
                do_tin_cay = 0
            else:
                du_doan = round(lich_su[3]*0.4 + lich_su[2]*0.3 + lich_su[1]*0.2 + lich_su[0]*0.1, 1)
                
                # Độ tin cậy
                avg = sum(lich_su) / 4
                bien_dong = sum(abs(x - avg) for x in lich_su) / 4
                do_tin_cay = round(max(50, min(95, 100 - bien_dong * 5)), 1)
            
            # Lưu dự đoán
            request.env['ai.prediction'].create({
                'nhan_vien_id': nhan_vien.id,
                'khoi_luong_du_doan': du_doan,
                'do_tin_cay': do_tin_cay,
            })
            
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
            return {'error': str(e)}

    @http.route('/ai/test', type='http', auth='user')
    def test_ai(self):
        """Route test để kiểm tra AI"""
        nhan_viens = request.env['nhan_vien'].search([])
        result = "<h1>Test AI Route</h1><ul>"
        for nv in nhan_viens:
            result += f"<li>{nv.id} - {nv.ho_va_ten}</li>"
        result += "</ul>"
        return result