from odoo import models, fields, api

class AIPrediction(models.Model):
    _name = 'ai.prediction'
    _description = 'Dự đoán AI'
    _rec_name = 'nhan_vien_id'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên', required=True)
    ngay_du_doan = fields.Date(string='Ngày dự đoán', default=fields.Date.today)
    khoi_luong_du_doan = fields.Float(string='Khối lượng công việc dự đoán (công việc/ngày)')
    do_tin_cay = fields.Float(string='Độ tin cậy (%)', default=75)
    
    @api.depends('khoi_luong_du_doan')
    def _get_trang_thai(self):
        if self.khoi_luong_du_doan > 15:
            return 'rat_cao'
        elif self.khoi_luong_du_doan > 10:
            return 'cao'
        elif self.khoi_luong_du_doan > 5:
            return 'trung_binh'
        else:
            return 'thap'
    
    trang_thai = fields.Char(string='Trạng thái', compute='_get_trang_thai')