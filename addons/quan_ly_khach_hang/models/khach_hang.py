from odoo import models, fields, api
from datetime import date

class KhachHang(models.Model):
    _name = 'khach_hang'
    _description = 'Khách hàng'
    _rec_name = 'ten_khach_hang'

    ma_khach_hang = fields.Char(string="Mã khách hàng", required=True)
    ten_khach_hang = fields.Char(string="Tên khách hàng", required=True)

    loai_khach_hang_id = fields.Many2one(
        'loai_khach_hang',
        string='Loại khách hàng',
        required=True
    )
    
    # 👇 SỬA LẠI FIELD NÀY - Thay related bằng compute
    loai_khach = fields.Char(
        string="Loại khách hàng",
        compute='_compute_loai_khach',
        store=True,
        readonly=True
    )
    
    nhan_vien_phu_trach_id = fields.Many2one(
        'nhan_vien',
        string='Nhân viên phụ trách'
    )
    
    trang_thai = fields.Selection(
        [
            ('hoat_dong', 'Hoạt động'),
            ('ngung', 'Ngừng hoạt động'),
        ],
        string='Trạng thái',
        default='hoat_dong'
    )

    dien_thoai = fields.Char(string="Điện thoại")
    email = fields.Char(string="Email")
    dia_chi = fields.Text(string="Địa chỉ")
    ghi_chu = fields.Text(string="Ghi chú")
    
    ho_tro_ids = fields.One2many('ho_tro_khach_hang', 'ten_khach_hang', string='Hỗ trợ khách hàng')
    khach_hang_tiem_nang_ids = fields.One2many('khach_hang_tiem_nang', 'khach_hang_id', string='Khách hàng tiềm năng')

    @api.depends('loai_khach_hang_id')
    def _compute_loai_khach(self):
        for record in self:
            if record.loai_khach_hang_id:
                record.loai_khach = record.loai_khach_hang_id.name
            else:
                record.loai_khach = False
    
    def action_view_nhan_vien(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nhân viên phụ trách',
            'res_model': 'nhan_vien',
            'view_mode': 'form',
            'res_id': self.nhan_vien_phu_trach_id.id,
            'target': 'current'
        }