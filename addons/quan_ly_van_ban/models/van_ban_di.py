from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VanBanDi(models.Model):
    _name = 'van_ban_di'
    _description = 'Bảng chứa thông tin văn bản đi'
    _rec_name = 'ten_van_ban'
    _order = 'ngay_van_ban desc, so_van_ban_di desc'

    so_van_ban_di = fields.Char("Số văn bản đi", required=True, copy=False)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    so_hieu_van_ban = fields.Char("Số hiệu văn bản", required=True)
    noi_nhan = fields.Char("Nơi nhận")
    trich_yeu = fields.Text("Trích yếu nội dung")
    
    ngay_van_ban = fields.Date(string="Ngày văn bản", required=True, default=fields.Date.today)
    ngay_ky = fields.Date(string="Ngày ký", default=fields.Date.today)
    
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
    
    file_dinh_kem = fields.Binary(string='File đính kèm')
    file_name = fields.Char(string='Tên file')
    ghi_chu = fields.Text(string='Ghi chú')
    user_id = fields.Many2one('res.users', string='Người tạo', default=lambda self: self.env.user)
    
    _sql_constraints = [
        ('unique_so_van_ban_di', 'unique(so_van_ban_di)', 'Số văn bản đi đã tồn tại!')
    ]
    
    @api.constrains('ngay_van_ban', 'ngay_ky')
    def _check_ngay_thang(self):
        for record in self:
            if record.ngay_ky and record.ngay_van_ban and record.ngay_ky < record.ngay_van_ban:
                raise ValidationError("Ngày ký không thể trước ngày văn bản!")
                
    @api.model
    def create(self, vals):
        if not vals.get('so_van_ban_di'):
            year = fields.Date.today().year
            last_record = self.search([], order='so_van_ban_di desc', limit=1)
            if last_record and last_record.so_van_ban_di:
                last_number = int(last_record.so_van_ban_di.split('/')[0])
                new_number = last_number + 1
            else:
                new_number = 1
            vals['so_van_ban_di'] = f"{new_number}/VBĐI-{year}"
        return super(VanBanDi, self).create(vals)