# -*- coding: utf-8 -*-
import os
import json
import logging
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import models, api

_logger = logging.getLogger(__name__)


class ChatbotService(models.AbstractModel):
    """Service trợ lý AI nội bộ - truy vấn dữ liệu ERP và gọi OpenAI."""
    _name = 'chatbot.service'
    _description = 'Chatbot AI Service'

    # Danh sách model AI được hỗ trợ
    SUPPORTED_MODELS = {
        'openai_gpt4o_mini': {
            'provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'label': 'GPT-4o mini (OpenAI)',
        },
        'gemini_pro': {
            'provider': 'gemini',
            'model_name': 'gemini-2.0-flash-001',
            'label': 'Gemini 2.0 Flash (Google)',
        },
    }
    DEFAULT_MODEL_KEY = 'openai_gpt4o_mini'

    def _load_env_key(self, env_key):
        """Đọc file .env thủ công khi biến môi trường chưa có."""
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
        )
        env_path = os.path.join(base_dir, '.env')
        if not os.path.isfile(env_path):
            return None
        try:
            with open(env_path, 'r', encoding='utf-8') as env_file:
                for line in env_file:
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, val = line.strip().split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key == env_key and val:
                        os.environ.setdefault(env_key, val)
                        return val
        except Exception as exc:
            _logger.warning("Không thể đọc .env: %s", exc)
        return None

    @api.model
    def _get_api_key(self, provider):
        """Đọc API key tương ứng từng provider."""
        provider_map = {
            'openai': ('OPENAI_API_KEY', 'openai.api_key'),
            'gemini': ('GEMINI_API_KEY', 'gemini.api_key'),
        }

        env_key, config_key = provider_map.get(provider, (None, None))
        if not env_key:
            raise ValueError(f"Provider không được hỗ trợ: {provider}")

        # Thử đọc từ environment variable
        api_key = os.getenv(env_key, '')
        if api_key:
            return api_key
            
        # Thử đọc từ file .env
        api_key = self._load_env_key(env_key) or ''
        if api_key:
            return api_key
            
        # Thử đọc từ ir.config_parameter
        if config_key:
            api_key = self.env['ir.config_parameter'].sudo().get_param(config_key, '')
            if api_key:
                return api_key
                
        _logger.error(
            "%s missing: set in environment, .env, hoặc ir.config_parameter(%s)",
            env_key,
            config_key,
        )
        return api_key

    @api.model
    def query_documents(self, question):
        """Truy vấn dữ liệu ERP dựa trên câu hỏi."""
        user = self.env.user
        today = date.today()
        first_day_of_month = today.replace(day=1)

        context_data = {
            'user_name': user.name,
            'today': str(today),
            'month': today.strftime('%m/%Y'),
        }

        question_lower = question.lower()

        # --- Văn bản quá hạn xử lý ---
        if 'quá hạn' in question_lower or 'qua han' in question_lower:
            context_data['overdue_documents'] = self._get_overdue_documents()

        # --- Văn bản trong tháng này ---
        if 'tháng này' in question_lower or 'thang nay' in question_lower or 'trong tháng' in question_lower:
            context_data['monthly_documents'] = self._get_monthly_documents(first_day_of_month, today)

        # --- Văn bản theo khách hàng ---
        customer_name = self._extract_customer_name(question)
        if customer_name:
            context_data['customer_documents'] = self._get_customer_documents(customer_name, first_day_of_month, today)
            context_data['customer_query'] = customer_name

        # --- Hợp đồng ---
        if 'hợp đồng' in question_lower or 'hop dong' in question_lower:
            context_data['contracts'] = self._get_contracts()

        # --- Báo giá ---
        if 'báo giá' in question_lower or 'bao gia' in question_lower:
            context_data['quotes'] = self._get_quotes()

        # --- Nhân viên ---
        if ('nhân viên' in question_lower or 'nhan vien' in question_lower or 
            'nhân sự' in question_lower or 'nhan su' in question_lower):
            context_data['employees'] = self._get_employees()

        # --- Yêu cầu khách hàng ---
        if 'yêu cầu' in question_lower or 'yeu cau' in question_lower:
            context_data['customer_requests'] = self._get_customer_requests()

        # --- Thống kê tổng quan (luôn lấy) ---
        context_data['statistics'] = self._get_statistics()

        return context_data

    @api.model
    def _get_overdue_documents(self):
        """Lấy danh sách văn bản đến đang quá hạn xử lý."""
        try:
            # Kiểm tra model van_ban_den có tồn tại không
            if 'van_ban_den' not in self.env:
                _logger.warning("Model van_ban_den không tồn tại")
                return []
                
            VanBanDen = self.env['van_ban_den']
            today = date.today()
            
            # Giả sử có trường han_xu_ly, nếu không thì dùng ngay_van_ban + 7 ngày
            overdue = VanBanDen.search([
                ('ngay_van_ban', '<', today),
            ], limit=50)
            
            result = []
            for doc in overdue:
                # Tính số ngày quá hạn (tạm tính từ ngày văn bản)
                overdue_days = (today - doc.ngay_van_ban).days if doc.ngay_van_ban else 0
                result.append({
                    'so_ky_hieu': doc.so_ky_hieu if hasattr(doc, 'so_ky_hieu') else doc.so_hieu_van_ban,
                    'trich_yeu': doc.trich_yeu[:100] if doc.trich_yeu else '',
                    'ngay_van_ban': str(doc.ngay_van_ban) if doc.ngay_van_ban else '',
                    'so_ngay_qua_han': overdue_days,
                })
            return result
        except Exception as e:
            _logger.warning("Không thể truy vấn văn bản quá hạn: %s", str(e))
            return []

    @api.model
    def _get_monthly_documents(self, start_date, end_date):
        """Lấy danh sách văn bản trong khoảng thời gian."""
        try:
            result = {
                'van_ban_den': [],
                'van_ban_di': [],
                'total_den': 0,
                'total_di': 0,
            }
            
            # Lấy văn bản đến
            if 'van_ban_den' in self.env:
                VanBanDen = self.env['van_ban_den']
                vb_den = VanBanDen.search([
                    ('ngay_van_ban', '>=', start_date),
                    ('ngay_van_ban', '<=', end_date),
                ], limit=30)
                
                for d in vb_den:
                    result['van_ban_den'].append({
                        'so_ky_hieu': d.so_ky_hieu if hasattr(d, 'so_ky_hieu') else d.so_hieu_van_ban,
                        'trich_yeu': d.trich_yeu[:80] if d.trich_yeu else '',
                        'ngay_van_ban': str(d.ngay_van_ban),
                    })
                result['total_den'] = len(vb_den)
            
            # Lấy văn bản đi
            if 'van_ban_di' in self.env:
                VanBanDi = self.env['van_ban_di']
                vb_di = VanBanDi.search([
                    ('ngay_van_ban', '>=', start_date),
                    ('ngay_van_ban', '<=', end_date),
                ], limit=30)
                
                for d in vb_di:
                    result['van_ban_di'].append({
                        'so_ky_hieu': d.so_ky_hieu if hasattr(d, 'so_ky_hieu') else d.so_hieu_van_ban,
                        'trich_yeu': d.trich_yeu[:80] if d.trich_yeu else '',
                        'ngay_van_ban': str(d.ngay_van_ban),
                    })
                result['total_di'] = len(vb_di)
            
            return result
        except Exception as e:
            _logger.warning("Không thể truy vấn văn bản tháng này: %s", str(e))
            return {'van_ban_den': [], 'van_ban_di': [], 'total_den': 0, 'total_di': 0}

    @api.model
    def _get_customer_documents(self, customer_name, start_date, end_date):
        """Lấy văn bản của khách hàng theo tên."""
        try:
            if 'khach_hang' not in self.env:
                return {'found': False, 'customer_name': customer_name, 'documents': []}
                
            KhachHang = self.env['khach_hang']
            customers = KhachHang.search([
                ('ten_khach_hang', 'ilike', customer_name)
            ], limit=5)
            
            if not customers:
                return {'found': False, 'customer_name': customer_name, 'documents': []}
            
            docs = []
            if 'van_ban_den' in self.env:
                VanBanDen = self.env['van_ban_den']
                docs = VanBanDen.search([
                    ('khach_hang_id', 'in', customers.ids),
                    ('ngay_van_ban', '>=', start_date),
                    ('ngay_van_ban', '<=', end_date),
                ], limit=30)
            
            return {
                'found': True,
                'customers': [{'id': c.id, 'name': c.ten_khach_hang} for c in customers],
                'documents': [{
                    'so_ky_hieu': d.so_ky_hieu if hasattr(d, 'so_ky_hieu') else d.so_hieu_van_ban,
                    'trich_yeu': d.trich_yeu[:80] if d.trich_yeu else '',
                    'ngay_van_ban': str(d.ngay_van_ban),
                } for d in docs],
                'total': len(docs),
            }
        except Exception as e:
            _logger.warning("Không thể truy vấn văn bản khách hàng: %s", str(e))
            return {'found': False, 'customer_name': customer_name, 'documents': []}

    @api.model
    def _extract_customer_name(self, question):
        """Trích xuất tên khách hàng từ câu hỏi."""
        patterns = ['khách hàng ', 'khach hang ', 'của ', 'cho ', 'công ty ', 'cong ty ']
        
        question_lower = question.lower()
        for pattern in patterns:
            if pattern in question_lower:
                idx = question_lower.find(pattern) + len(pattern)
                rest = question[idx:].strip()
                for stop_word in [' có ', ' trong ', ' tháng ', ' năm ', ' đang ', ' là ', '?', '.']:
                    if stop_word in rest.lower():
                        rest = rest[:rest.lower().find(stop_word)]
                if rest and len(rest) > 1:
                    return rest.strip()
        return None

    @api.model
    def _get_statistics(self):
        """Thống kê tổng quan văn bản."""
        try:
            today = date.today()
            first_day_of_month = today.replace(day=1)
            
            stats = {
                'total_van_ban_den': 0,
                'total_van_ban_di': 0,
                'van_ban_den_thang_nay': 0,
                'van_ban_di_thang_nay': 0,
                'qua_han': 0,
            }
            
            if 'van_ban_den' in self.env:
                VanBanDen = self.env['van_ban_den']
                stats['total_van_ban_den'] = VanBanDen.search_count([])
                stats['van_ban_den_thang_nay'] = VanBanDen.search_count([
                    ('ngay_van_ban', '>=', first_day_of_month),
                    ('ngay_van_ban', '<=', today),
                ])
            
            if 'van_ban_di' in self.env:
                VanBanDi = self.env['van_ban_di']
                stats['total_van_ban_di'] = VanBanDi.search_count([])
                stats['van_ban_di_thang_nay'] = VanBanDi.search_count([
                    ('ngay_van_ban', '>=', first_day_of_month),
                    ('ngay_van_ban', '<=', today),
                ])
            
            # Tính số văn bản quá hạn (tạm tính từ ngày văn bản > 7 ngày chưa xử lý)
            if 'van_ban_den' in self.env:
                cutoff = today - relativedelta(days=7)
                stats['qua_han'] = self.env['van_ban_den'].search_count([
                    ('ngay_van_ban', '<', cutoff)
                ])
            
            return stats
        except Exception as e:
            _logger.warning("Không thể lấy thống kê: %s", str(e))
            return {}

    @api.model
    def _get_contracts(self):
        """Lấy danh sách hợp đồng."""
        try:
            if 'hop_dong' not in self.env:
                _logger.info("Model hop_dong không tồn tại")
                return []
                
            HopDong = self.env['hop_dong']
            contracts = HopDong.search([], limit=20)
            result = []
            for c in contracts:
                contract_data = {
                    'so_hop_dong': c.so_hop_dong if hasattr(c, 'so_hop_dong') else '',
                    'ten_hop_dong': c.ten_hop_dong if hasattr(c, 'ten_hop_dong') else '',
                    'khach_hang': c.khach_hang_id.ten_khach_hang if hasattr(c, 'khach_hang_id') and c.khach_hang_id else '',
                    'ngay_ky': str(c.ngay_ky) if hasattr(c, 'ngay_ky') and c.ngay_ky else '',
                }
                if hasattr(c, 'tong_gia_tri'):
                    contract_data['tong_gia_tri'] = c.tong_gia_tri
                if hasattr(c, 'trang_thai'):
                    contract_data['trang_thai'] = c.trang_thai
                result.append(contract_data)
            return result
        except Exception as e:
            _logger.warning("Không thể truy vấn hợp đồng: %s", str(e))
            return []

    @api.model
    def _get_quotes(self):
        """Lấy danh sách báo giá."""
        try:
            if 'bao_gia' not in self.env:
                _logger.info("Model bao_gia không tồn tại")
                return []
                
            BaoGia = self.env['bao_gia']
            quotes = BaoGia.search([], limit=20)
            result = []
            for q in quotes:
                quote_data = {
                    'so_bao_gia': q.so_bao_gia if hasattr(q, 'so_bao_gia') else '',
                    'ten_bao_gia': q.ten_bao_gia if hasattr(q, 'ten_bao_gia') else '',
                    'khach_hang': q.khach_hang_id.ten_khach_hang if hasattr(q, 'khach_hang_id') and q.khach_hang_id else '',
                    'ngay_bao_gia': str(q.ngay_bao_gia) if hasattr(q, 'ngay_bao_gia') and q.ngay_bao_gia else '',
                }
                if hasattr(q, 'tong_tien'):
                    quote_data['tong_tien'] = q.tong_tien
                if hasattr(q, 'trang_thai'):
                    quote_data['trang_thai'] = q.trang_thai
                result.append(quote_data)
            return result
        except Exception as e:
            _logger.warning("Không thể truy vấn báo giá: %s", str(e))
            return []

    @api.model
    def _get_employees(self, limit=50):
        """Lấy danh sách nhân viên."""
        try:
            # Kiểm tra model nhan_vien có tồn tại không
            if 'nhan_vien' not in self.env:
                _logger.warning("Model nhan_vien không tồn tại")
                return []
            
            NhanVien = self.env['nhan_vien']
            employees = NhanVien.search([], limit=limit)
            
            _logger.info("Found %d employees in database", len(employees))
            
            result = []
            for e in employees:
                # Lấy thông tin nhân viên một cách an toàn
                emp_data = {
                    'ma_dinh_danh': e.ma_dinh_danh if hasattr(e, 'ma_dinh_danh') else '',
                    'ho_va_ten': e.ho_va_ten if hasattr(e, 'ho_va_ten') else '',
                    'ten': e.ten if hasattr(e, 'ten') else '',
                    'don_vi': e.don_vi_hien_tai.ten_don_vi if hasattr(e, 'don_vi_hien_tai') and e.don_vi_hien_tai else '',
                    'chuc_vu': e.chuc_vu_hien_tai.ten_chuc_vu if hasattr(e, 'chuc_vu_hien_tai') and e.chuc_vu_hien_tai else '',
                    'tuoi': e.tuoi if hasattr(e, 'tuoi') else '',
                    'email': e.email if hasattr(e, 'email') else '',
                    'so_dien_thoai': e.so_dien_thoai if hasattr(e, 'so_dien_thoai') else '',
                }
                result.append(emp_data)
            
            _logger.info("Returning %d employee records", len(result))
            return result
        except Exception as e:
            _logger.error("Không thể truy vấn nhân viên: %s", str(e))
            return []

    @api.model
    def _get_customer_requests(self):
        """Lấy danh sách yêu cầu khách hàng."""
        try:
            if 'yeu_cau_khach_hang' not in self.env:
                _logger.info("Model yeu_cau_khach_hang không tồn tại")
                return []
                
            YeuCauKhachHang = self.env['yeu_cau_khach_hang']
            requests = YeuCauKhachHang.search([], limit=20)
            result = []
            for r in requests:
                req_data = {
                    'tieu_de': r.tieu_de if hasattr(r, 'tieu_de') else '',
                    'noi_dung': r.noi_dung[:100] if hasattr(r, 'noi_dung') and r.noi_dung else '',
                    'khach_hang': r.khach_hang_id.ten_khach_hang if hasattr(r, 'khach_hang_id') and r.khach_hang_id else '',
                    'ngay_tao': str(r.create_date.date()) if hasattr(r, 'create_date') and r.create_date else '',
                }
                if hasattr(r, 'trang_thai'):
                    req_data['trang_thai'] = r.trang_thai
                result.append(req_data)
            return result
        except Exception as e:
            _logger.warning("Không thể truy vấn yêu cầu khách hàng: %s", str(e))
            return []

    @api.model
    def _build_system_prompt(self, erp_context):
        """Xây dựng system prompt với dữ liệu ERP."""
        prompt = f"""Bạn là trợ lý AI nội bộ của hệ thống quản lý văn bản và khách hàng. 
Hãy trả lời ngắn gọn, chính xác dựa trên dữ liệu ERP được cung cấp.
Nếu không có dữ liệu liên quan, hãy thông báo rõ ràng.
Ngày hôm nay: {erp_context.get('today', '')}
Tháng hiện tại: {erp_context.get('month', '')}
Người dùng: {erp_context.get('user_name', '')}

=== THỐNG KÊ TỔNG QUAN ===
{json.dumps(erp_context.get('statistics', {}), ensure_ascii=False, indent=2)}
"""
        
        if erp_context.get('overdue_documents'):
            prompt += f"""
=== VĂN BẢN QUÁ HẠN ({len(erp_context['overdue_documents'])} văn bản) ===
{json.dumps(erp_context['overdue_documents'], ensure_ascii=False, indent=2)}
"""
        
        if erp_context.get('monthly_documents'):
            monthly = erp_context['monthly_documents']
            prompt += f"""
=== VĂN BẢN THÁNG NÀY ===
Văn bản đến: {monthly.get('total_den', 0)} văn bản
Văn bản đi: {monthly.get('total_di', 0)} văn bản
"""

        if erp_context.get('customer_documents'):
            cust = erp_context['customer_documents']
            if cust.get('found'):
                prompt += f"""
=== VĂN BẢN CỦA KHÁCH HÀNG ===
Khách hàng: {[c['name'] for c in cust.get('customers', [])]}
Tổng số văn bản: {cust.get('total', 0)}
"""

        if erp_context.get('contracts'):
            prompt += f"""
=== HỢP ĐỒNG ({len(erp_context['contracts'])} hợp đồng) ===
{json.dumps(erp_context['contracts'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('quotes'):
            prompt += f"""
=== BÁO GIÁ ({len(erp_context['quotes'])} báo giá) ===
{json.dumps(erp_context['quotes'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('employees'):
            prompt += f"""
=== NHÂN VIÊN ({len(erp_context['employees'])} nhân viên) ===
{json.dumps(erp_context['employees'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('customer_requests'):
            prompt += f"""
=== YÊU CẦU KHÁCH HÀNG ({len(erp_context['customer_requests'])} yêu cầu) ===
{json.dumps(erp_context['customer_requests'][:10], ensure_ascii=False, indent=2)}
"""

        return prompt

    @api.model
    def _get_demo_response(self, question, erp_context):
        """Tạo câu trả lời demo khi không có API key."""
        question_lower = question.lower()
        
        # Kiểm tra câu hỏi về thống kê
        if 'thống kê' in question_lower or 'tong quan' in question_lower or 'thong ke' in question_lower:
            stats = erp_context.get('statistics', {})
            return f"""📊 **THỐNG KÊ TỔNG QUAN**

- Tổng văn bản đến: {stats.get('total_van_ban_den', 0)}
- Tổng văn bản đi: {stats.get('total_van_ban_di', 0)}
- Văn bản đến tháng này: {stats.get('van_ban_den_thang_nay', 0)}
- Văn bản đi tháng này: {stats.get('van_ban_di_thang_nay', 0)}
- Văn bản quá hạn: {stats.get('qua_han', 0)}"""
        
        # Kiểm tra câu hỏi về nhân viên
        if 'nhân viên' in question_lower or 'nhan vien' in question_lower:
            employees = erp_context.get('employees', [])
            _logger.info("Employees count in context: %d", len(employees))
            
            if employees:
                emp_list = []
                for e in employees[:10]:
                    emp_name = e.get('ho_va_ten', '')
                    if not emp_name:
                        emp_name = e.get('ten', 'Không tên')
                    emp_info = f"- {emp_name}"
                    
                    if e.get('chuc_vu'):
                        emp_info += f" ({e.get('chuc_vu')})"
                    if e.get('don_vi'):
                        emp_info += f" - {e.get('don_vi')}"
                    if e.get('email'):
                        emp_info += f"\n  📧 {e.get('email')}"
                    emp_list.append(emp_info)
                
                return f"""👥 **DANH SÁCH NHÂN VIÊN** ({len(employees)} người)

{chr(10).join(emp_list)}"""
            else:
                # Kiểm tra xem có bảng nhan_vien không
                try:
                    if 'nhan_vien' in self.env:
                        count = self.env['nhan_vien'].search_count([])
                        if count > 0:
                            return f"⚠️ Có {count} nhân viên trong hệ thống nhưng không thể lấy chi tiết. Vui lòng kiểm tra lại quyền truy cập."
                    return "📋 **KHÔNG CÓ DỮ LIỆU NHÂN VIÊN**\n\nChưa có nhân viên nào trong hệ thống. Vui lòng thêm nhân viên vào module Nhân sự trước."
                except Exception as e:
                    return f"❌ **LỖI TRUY VẤN NHÂN VIÊN**\n\nKhông thể truy cập dữ liệu nhân viên. Lỗi: {str(e)}"
        
        # Kiểm tra câu hỏi về văn bản
        if 'văn bản' in question_lower or 'van ban' in question_lower:
            stats = erp_context.get('statistics', {})
            monthly = erp_context.get('monthly_documents', {})
            
            response = f"""📄 **THÔNG TIN VĂN BẢN**

**Tổng quan:**
- Tổng văn bản đến: {stats.get('total_van_ban_den', 0)}
- Tổng văn bản đi: {stats.get('total_van_ban_di', 0)}

**Tháng này ({erp_context.get('month', '')}):**
- Văn bản đến: {stats.get('van_ban_den_thang_nay', 0)}
- Văn bản đi: {stats.get('van_ban_di_thang_nay', 0)}"""

            # Thêm danh sách văn bản gần đây
            if monthly.get('van_ban_den') and len(monthly.get('van_ban_den', [])) > 0:
                response += "\n\n**Văn bản đến gần đây:**\n"
                for doc in monthly['van_ban_den'][:5]:
                    response += f"- {doc.get('so_ky_hieu', 'N/A')}: {doc.get('trich_yeu', '')[:50]}\n"
            
            if monthly.get('van_ban_di') and len(monthly.get('van_ban_di', [])) > 0:
                response += "\n**Văn bản đi gần đây:**\n"
                for doc in monthly['van_ban_di'][:5]:
                    response += f"- {doc.get('so_ky_hieu', 'N/A')}: {doc.get('trich_yeu', '')[:50]}\n"
            
            return response
        
        # Kiểm tra câu hỏi về văn bản quá hạn
        if 'quá hạn' in question_lower or 'qua han' in question_lower:
            overdue = erp_context.get('overdue_documents', [])
            if overdue:
                doc_list = []
                for d in overdue[:5]:
                    doc_list.append(f"- {d['so_ky_hieu']}: quá hạn {d.get('so_ngay_qua_han', 0)} ngày")
                return f"""⚠️ **VĂN BẢN QUÁ HẠN** ({len(overdue)} văn bản)

{chr(10).join(doc_list)}"""
            return "✅ Không có văn bản nào quá hạn xử lý."
        
        # Câu hỏi thông thường
        stats = erp_context.get('statistics', {})
        return f"""🤖 **Xin chào! Tôi là trợ lý AI.**

Câu hỏi của bạn: *"{question}"*

📋 **Dữ liệu từ hệ thống:**
- Người dùng: {erp_context.get('user_name', '')}
- Hôm nay: {erp_context.get('today', '')}
- Tháng: {erp_context.get('month', '')}
- Tổng văn bản: {stats.get('total_van_ban_den', 0) + stats.get('total_van_ban_di', 0)}

💡 **Tôi có thể giúp bạn:**
- Hỏi "thống kê" để xem số liệu tổng quan
- Hỏi "nhân viên" để xem danh sách nhân viên
- Hỏi "văn bản" để xem danh sách văn bản
- Hỏi "văn bản quá hạn" để xem các văn bản cần xử lý

(Đang chạy chế độ demo. Để có câu trả lời thông minh từ AI thực, vui lòng cấu hình API key)"""

    @api.model
    def ask(self, question, model_key=None, session_id=None, user_id=None):
        """Xử lý câu hỏi từ người dùng."""
        _logger.info("=== CHATBOT SERVICE ASK ===")
        _logger.info("Question received: '%s'", question)
        _logger.info("Question type: %s", type(question))
        _logger.info("Model key: %s", model_key)
        
        if not question or not question.strip():
            _logger.warning("Empty question in service")
            return {'success': False, 'error': 'Vui lòng nhập câu hỏi.'}
        
        # Tạo session_id nếu chưa có
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            _logger.info("Created new session_id: %s", session_id)
        
        # Xác định model
        selected_key = model_key or self.DEFAULT_MODEL_KEY
        model_config = self.SUPPORTED_MODELS.get(selected_key)
        if not model_config:
            selected_key = self.DEFAULT_MODEL_KEY
            model_config = self.SUPPORTED_MODELS[self.DEFAULT_MODEL_KEY]
            _logger.info("Using default model: %s", selected_key)

        provider = model_config['provider']
        api_key = self._get_api_key(provider)
        
        _logger.info("Provider: %s", provider)
        _logger.info("API Key exists: %s", bool(api_key))
        
        # Nếu không có API key, dùng chế độ demo
        if not api_key:
            _logger.info("No API key found, using demo mode")
            try:
                # Truy vấn dữ liệu ERP để có thông tin thực
                erp_context = self.query_documents(question)
                # Tạo câu trả lời demo dựa trên dữ liệu thực
                answer = self._get_demo_response(question, erp_context)
                
                # Lưu vào lịch sử chat
                try:
                    if 'chat.history' in self.env:
                        self.env['chat.history'].create({
                            'session_id': session_id,
                            'message': question,
                            'is_bot': False,
                        })
                        self.env['chat.history'].create({
                            'session_id': session_id,
                            'message': answer,
                            'is_bot': True,
                        })
                except Exception as e:
                    _logger.warning("Could not save chat history: %s", str(e))
                
                return {
                    'success': True,
                    'answer': answer,
                    'session_id': session_id,
                    'model_key': selected_key,
                    'demo_mode': True,
                }
            except Exception as e:
                _logger.error("Error in demo mode: %s", str(e))
                return {
                    'success': True,
                    'answer': f"🤖 Xin chào! Tôi là trợ lý AI.\n\nCâu hỏi của bạn: {question}\n\n(Đang chạy chế độ demo. Để có câu trả lời thông minh từ AI thực, vui lòng cấu hình API key trong System Parameters hoặc file .env)",
                    'session_id': session_id,
                    'model_key': selected_key,
                    'demo_mode': True,
                }
        
        try:
            # Có API key, gọi AI thực
            _logger.info("Querying ERP data for: %s", question)
            erp_context = self.query_documents(question)
            
            # Tạo prompt
            system_prompt = self._build_system_prompt(erp_context)
            _logger.info("System prompt created, length: %d", len(system_prompt))
            
            # Gọi API
            if provider == 'openai':
                _logger.info("Calling OpenAI API...")
                answer = self._call_openai(api_key, system_prompt, question, model_config['model_name'])
            elif provider == 'gemini':
                _logger.info("Calling Gemini API...")
                answer = self._call_gemini(api_key, system_prompt, question, model_config['model_name'])
            else:
                raise ValueError(f"Provider không hỗ trợ: {provider}")
            
            _logger.info("Answer received, length: %d", len(answer))
            
            # Lưu vào lịch sử chat
            try:
                if 'chat.history' in self.env:
                    self.env['chat.history'].create({
                        'session_id': session_id,
                        'message': question,
                        'is_bot': False,
                    })
                    self.env['chat.history'].create({
                        'session_id': session_id,
                        'message': answer,
                        'is_bot': True,
                    })
            except Exception as e:
                _logger.warning("Could not save chat history: %s", str(e))
            
            return {
                'success': True,
                'answer': answer,
                'session_id': session_id,
                'model_key': selected_key,
            }
        except Exception as e:
            _logger.exception("Chatbot error in service: %s", str(e))
            return {'success': False, 'error': str(e)}

    @api.model
    def _call_openai(self, api_key, system_prompt, user_question, model_name):
        """Gọi OpenAI API."""
        import urllib.request
        import urllib.error
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt[:8000]},
                {"role": "user", "content": user_question}
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"Lỗi API OpenAI: {e.code} - {error_body[:200]}")
        except Exception as e:
            raise Exception(f"Lỗi kết nối OpenAI: {str(e)}")

    def _call_gemini(self, api_key, system_prompt, user_question, model_name):
        """Gọi Google Gemini API."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise Exception("Thiếu thư viện google-generativeai. Cài đặt: pip install google-generativeai")

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            full_prompt = f"{system_prompt[:8000]}\n\nCâu hỏi: {user_question}"
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 1024,
                }
            )
            return response.text if response else "Không có phản hồi từ Gemini."
        except Exception as e:
            raise Exception(f"Lỗi Gemini: {str(e)}")