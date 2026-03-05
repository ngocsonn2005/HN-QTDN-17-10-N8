from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class ThongKeHoTroNhanVien(models.Model):
    _name = 'thong_ke_ho_tro_nhan_vien'
    _description = 'Thống kê hỗ trợ nhân viên'
    _rec_name = 'nhan_vien_id'

    # SỬA: Thay 'res.users' bằng 'nhan_vien'
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    so_lan_ho_tro = fields.Integer(string="Số lần hỗ trợ", default=0)
    ho_tro_ids = fields.Many2many('ho_tro_khach_hang', string="Danh sách hỗ trợ")

    @api.model_create_multi
    def create(self, vals_list):
        # Chỉ cho phép tạo từ hệ thống (qua nút cập nhật)
        if self.env.context.get('from_update_button'):
            return super(ThongKeHoTroNhanVien, self).create(vals_list)
        raise UserError(_("Không được phép tạo thủ công dữ liệu thống kê! Vui lòng sử dụng nút 'Cập nhật thống kê'."))

    def write(self, vals):
        # Chỉ cho phép sửa từ hệ thống
        if self.env.context.get('from_update_button'):
            return super(ThongKeHoTroNhanVien, self).write(vals)
        raise UserError(_("Không được phép sửa thủ công dữ liệu thống kê! Vui lòng sử dụng nút 'Cập nhật thống kê'."))

    def unlink(self):
        # Chỉ cho phép xóa từ hệ thống
        if self.env.context.get('from_update_button'):
            return super(ThongKeHoTroNhanVien, self).unlink()
        raise UserError(_("Không được phép xóa thủ công dữ liệu thống kê!"))

    @api.model
    def update_thong_ke(self, nhan_vien_id=None):
        """
        Cập nhật thống kê cho một nhân viên hoặc tất cả nhân viên.
        """
        # Xóa tất cả bản ghi cũ với context đặc biệt
        all_records = self.search([])
        if all_records:
            # Sử dụng context để bypass validation
            all_records.with_context(from_update_button=True).unlink()

        domain = [('nhan_vien_phu_trach', '!=', False)]
        if nhan_vien_id:
            domain.append(('nhan_vien_phu_trach', '=', nhan_vien_id))

        # Nhóm dữ liệu theo nhân viên
        ho_tro_data = self.env['ho_tro_khach_hang'].read_group(
            domain,
            ['nhan_vien_phu_trach'],
            ['nhan_vien_phu_trach']
        )

        for data in ho_tro_data:
            nhan_vien_id_val = data['nhan_vien_phu_trach']
            if nhan_vien_id_val:
                # SỬA: lấy ID nhân viên từ nhan_vien_phu_trach
                nhan_vien = nhan_vien_id_val[0]  # Lấy ID nhân viên
                so_lan_ho_tro = data['nhan_vien_phu_trach_count']
                ho_tro_records = self.env['ho_tro_khach_hang'].search([('nhan_vien_phu_trach', '=', nhan_vien)])

                # Tạo bản ghi mới với context đặc biệt
                self.with_context(from_update_button=True).create({
                    'nhan_vien_id': nhan_vien,  # SỬA: trực tiếp gán ID
                    'so_lan_ho_tro': so_lan_ho_tro,
                    'ho_tro_ids': [(6, 0, ho_tro_records.ids)]
                })

        return True

    def action_update_thong_ke(self):
        """
        Nút trên giao diện để cập nhật thống kê.
        """
        self.update_thong_ke()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',  # Tải lại trang để xem kết quả
        }

    @api.model
    def init(self):
        """
        Tự động cập nhật thống kê khi module được cài đặt
        """
        try:
            self.update_thong_ke()
        except Exception as e:
            # Bỏ qua lỗi nếu chưa có dữ liệu
            pass