# -*- coding: utf-8 -*-

from odoo import models, fields, api
import uuid


class ChatHistory(models.Model):
    _name = 'chat.history'
    _description = 'Lịch sử chat với AI'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='Người dùng', default=lambda self: self.env.user, readonly=True)
    session_id = fields.Char('ID phiên chat', required=True, index=True)
    message = fields.Text('Nội dung tin nhắn', required=True)
    is_bot = fields.Boolean('Là tin nhắn từ bot', default=False)
    message_type = fields.Selection([
        ('text', 'Văn bản'),
        ('file', 'File'),
        ('system', 'Hệ thống')
    ], string='Loại tin nhắn', default='text')
    file_name = fields.Char('Tên file')
    file_data = fields.Binary('Dữ liệu file')
    timestamp = fields.Datetime('Thời gian', default=fields.Datetime.now, readonly=True)

    @api.model
    def create(self, vals):
        if not vals.get('session_id'):
            vals['session_id'] = str(uuid.uuid4())
        return super(ChatHistory, self).create(vals)

    @api.model
    def get_user_chat_history(self, limit=50):
        """Lấy lịch sử chat của user hiện tại"""
        records = self.search([
            ('user_id', '=', self.env.user.id)
        ], limit=limit, order='create_date desc')
        return records.read([
            'id', 'user_id', 'session_id', 'message', 'is_bot', 
            'message_type', 'file_name', 'timestamp'
        ])

    @api.model
    def get_session_messages(self, session_id):
        """Lấy tất cả tin nhắn trong một phiên chat"""
        records = self.search([
            ('session_id', '=', session_id)
        ], order='timestamp asc')
        return records.read([
            'id', 'user_id', 'session_id', 'message', 'is_bot', 
            'message_type', 'file_name', 'timestamp'
        ])

    @api.model
    def cleanup_old_history(self, days=30):
        """Xóa lịch sử chat cũ"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        old_records = self.search([('create_date', '<', cutoff_date)])
        count = len(old_records)
        old_records.unlink()
        return count