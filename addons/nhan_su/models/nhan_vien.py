# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError

class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'ten asc, tuoi desc'

    ma_dinh_danh = fields.Char("Mã định danh", required=True)

    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char(
        "Họ và tên",
        compute="_compute_ho_va_ten",
        store=True
    )

    ngay_sinh = fields.Date("Ngày sinh")
    que_quan = fields.Char("Quê quán")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    anh = fields.Binary("Ảnh")

    tuoi = fields.Integer(
        "Tuổi",
        compute="_compute_tuoi",
        store=True
    )

    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac",
        inverse_name="nhan_vien_id",
        string="Danh sách lịch sử công tác"
    )

    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap",
        inverse_name="nhan_vien_id",
        string="Danh sách chứng chỉ bằng cấp"
    )

    # TẠM THỜI COMMENT FIELD NÀY ĐỂ KIỂM TRA
    # so_nguoi_bang_tuoi = fields.Integer(
    #     "Số người bằng tuổi",
    #     default=0
    # )

    _sql_constraints = [
        ('ma_dinh_danh_unique',
         'unique(ma_dinh_danh)',
         'Mã định danh phải là duy nhất')
    ]

    # ================= COMPUTE =================

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                record.ho_va_ten = f"{record.ho_ten_dem} {record.ten}"

    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        for record in self:
            if record.ngay_sinh:
                today = date.today()
                birth_date = fields.Date.from_string(record.ngay_sinh)
                age = today.year - birth_date.year
                # Kiểm tra nếu chưa đến sinh nhật trong năm nay
                if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                    age -= 1
                record.tuoi = age
            else:
                record.tuoi = 0

    # ================= ONCHANGE =================

    @api.onchange("ten", "ho_ten_dem")
    def _onchange_ma_dinh_danh(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                chu_cai_dau = ''.join(
                    [tu[0] for tu in record.ho_ten_dem.lower().split()]
                )
                record.ma_dinh_danh = record.ten.lower() + chu_cai_dau

    # TẠM THỜI COMMENT ONCHANGE NÀY
    # @api.onchange("ngay_sinh")
    # def _onchange_ngay_sinh(self):
    #     if self.ngay_sinh:
    #         today = date.today()
    #         birth_date = fields.Date.from_string(self.ngay_sinh)
    #         age = today.year - birth_date.year
    #         if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
    #             age -= 1
    #         self.tuoi = age

    # ================= CONSTRAINT =================

    @api.constrains('tuoi')
    def _check_tuoi(self):
        for record in self:
            if record.tuoi < 18:
                raise ValidationError("Tuổi không được bé hơn 18")