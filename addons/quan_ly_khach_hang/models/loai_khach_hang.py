from odoo import models, fields

class LoaiKhachHang(models.Model):
    _name = 'loai_khach_hang'
    _description = 'Loại khách hàng'

    name = fields.Char("Tên loại khách hàng", required=True)
    mo_ta = fields.Text("Mô tả")
