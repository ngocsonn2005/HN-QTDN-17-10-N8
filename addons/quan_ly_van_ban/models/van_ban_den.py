from odoo import models, fields

class VanBanDen(models.Model):
    _name = 'van_ban_den'
    _description = 'Bảng chứa thông tin văn bản đến'
    _rec_name = 'ten_van_ban'

    so_van_ban_den = fields.Char("Số văn bản đến", required=True)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    so_hieu_van_ban = fields.Char("Số hiệu văn bản", required=True)
    noi_gui_den = fields.Char("Nơi gửi đến")

    loai_van_ban_id = fields.Many2one(
        'loai_van_ban',
        string='Loại văn bản',
        required=True
    )

    nhan_vien_xu_ly_id = fields.Many2one(
        'nhan_vien',
        string='Nhân viên xử lý',
        required=True
    )

    nhan_vien_ky_id = fields.Many2one(
        'nhan_vien',
        string='Người ký'
    )
    
    khach_hang_id = fields.Many2one(
        'khach_hang',
        string='Khách hàng',
        required=True,
    )