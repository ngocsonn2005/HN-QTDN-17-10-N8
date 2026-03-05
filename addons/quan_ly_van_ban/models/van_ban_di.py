from odoo import models, fields

class VanBanDi(models.Model):
    _name = 'van_ban_di'
    _description = 'Bảng chứa thông tin văn bản đi'
    _rec_name = 'ten_van_ban'

    so_van_ban_di = fields.Char("Số văn bản đi", required=True)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    so_hieu_van_ban = fields.Char("Số hiệu văn bản", required=True)
    noi_nhan = fields.Char("Nơi nhận")

    ngay_van_ban = fields.Date(string="Ngày văn bản", required=True, default=fields.Date.today)

    loai_van_ban_id = fields.Many2one(
        'loai_van_ban',
        string='Loại văn bản',
        required=True
    )

    nhan_vien_soan_id = fields.Many2one(
        'nhan_vien',
        string='Nhân viên soạn',
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