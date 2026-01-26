from odoo import models, fields

class TinTuyenDung(models.Model):
    _name = 'tin_tuyen_dung'
    _description = 'Tin tuyển dụng'

    name = fields.Char(string='Tiêu đề')
