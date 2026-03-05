# -*- coding: utf-8 -*-
{
    'name': "dashboard",
    'summary': "Dashboard tích hợp AI",
    'description': "Dashboard tổng hợp từ các module Nhân sự, Khách hàng, Văn bản",
    'author': "FIT-DNU",
    'website': "https://ttdn1501.aiotlabdnu.xyz/web",
    'category': 'Dashboard',
    'version': '0.1',
    'depends': ['base', 'nhan_su', 'quan_ly_khach_hang', 'quan_ly_van_ban'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dashboard/static/dashboard.js',
            'dashboard/static/dashboard.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}