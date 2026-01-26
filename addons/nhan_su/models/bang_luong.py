from odoo import models, fields

class BangLuong(models.Model):
    _name = 'bang_luong'
    _description = 'Bảng lương'

    name = fields.Char(string='Mã bảng lương')
