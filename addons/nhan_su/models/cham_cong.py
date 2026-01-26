from odoo import models, fields

class ChamCong(models.Model):
    _name = 'cham_cong'
    _description = 'Chấm công'

    name = fields.Char()
