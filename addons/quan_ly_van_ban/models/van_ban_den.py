from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VanBanDen(models.Model):
    _name = 'van_ban_den'
    _description = 'Bảng chứa thông tin văn bản đến'
    _rec_name = 'ten_van_ban'
    _order = 'ngay_van_ban desc, so_van_ban_den desc'

    so_van_ban_den = fields.Char("Số văn bản đến", required=True, copy=False)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    so_hieu_van_ban = fields.Char("Số hiệu văn bản", required=True)
    noi_gui_den = fields.Char("Nơi gửi đến")
    trich_yeu = fields.Text("Trích yếu nội dung")
    
    ngay_van_ban = fields.Date(string="Ngày văn bản", required=True, default=fields.Date.today)
    ngay_nhan = fields.Date(string="Ngày nhận", required=True, default=fields.Date.today)
    
    do_khan = fields.Selection([
        ('binh_thuong', 'Bình thường'),
        ('khan', 'Khẩn'),
        ('hoa_toc', 'Hỏa tốc')
    ], string='Độ khẩn', default='binh_thuong', required=True)
    
    do_mat = fields.Selection([
        ('binh_thuong', 'Bình thường'),
        ('mat', 'Mật'),
        ('tuyet_mat', 'Tuyệt mật')
    ], string='Độ mật', default='binh_thuong', required=True)

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
    
    file_dinh_kem = fields.Binary(string='File đính kèm')
    file_name = fields.Char(string='Tên file')
    ghi_chu = fields.Text(string='Ghi chú')
    user_id = fields.Many2one('res.users', string='Người nhập', default=lambda self: self.env.user)
    
    _sql_constraints = [
        ('unique_so_van_ban_den', 'unique(so_van_ban_den)', 'Số văn bản đến đã tồn tại!')
    ]
    
    @api.constrains('ngay_van_ban', 'ngay_nhan')
    def _check_ngay_thang(self):
        for record in self:
            if record.ngay_nhan and record.ngay_van_ban and record.ngay_nhan < record.ngay_van_ban:
                raise ValidationError("Ngày nhận không thể trước ngày văn bản!")
                
    @api.model
    def create(self, vals):
        if not vals.get('so_van_ban_den'):
            year = fields.Date.today().year
            last_record = self.search([], order='so_van_ban_den desc', limit=1)
            if last_record and last_record.so_van_ban_den:
                last_number = int(last_record.so_van_ban_den.split('/')[0])
                new_number = last_number + 1
            else:
                new_number = 1
            vals['so_van_ban_den'] = f"{new_number}/VBĐ-{year}"
        return super(VanBanDen, self).create(vals)