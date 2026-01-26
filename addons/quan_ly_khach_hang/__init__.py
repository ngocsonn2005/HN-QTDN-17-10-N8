# -*- coding: utf-8 -*-

from . import controllers
from . import models

def post_init_hook(cr, registry):
    """Tự động cập nhật thống kê khi module được cài đặt"""
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env['thong_ke_ho_tro_nhan_vien'].update_thong_ke()
    except Exception as e:
        # Bỏ qua lỗi nếu chưa có dữ liệu
        pass