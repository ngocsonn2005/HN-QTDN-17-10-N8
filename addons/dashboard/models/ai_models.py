# -*- coding: utf-8 -*-
# models/ai_models.py

from odoo import models, fields, api
from datetime import datetime, timedelta
import os
import logging

_logger = logging.getLogger(__name__)

# Kiểm tra import thư viện ML
try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    import joblib
    ML_AVAILABLE = True
    _logger.info("Machine Learning libraries loaded successfully")
except ImportError as e:
    ML_AVAILABLE = False
    _logger.warning(f"Cannot import ML libraries: {e}")

class AIModelManager(models.Model):
    _name = 'ai.model.manager'
    _description = 'Quản lý mô hình AI'

    name = fields.Char(string='Tên mô hình', required=True, default='AI Prediction Model')
    model_type = fields.Selection([
        ('random_forest', 'Random Forest'),
        ('gradient_boosting', 'Gradient Boosting'),
        ('linear', 'Linear Regression')
    ], string='Loại mô hình', default='random_forest')
    is_active = fields.Boolean(string='Đang hoạt động', default=True)
    trained_date = fields.Datetime(string='Ngày huấn luyện')
    accuracy = fields.Float(string='Độ chính xác (R²)', digits=(6, 4))
    mae = fields.Float(string='MAE (Sai số trung bình)', digits=(6, 2))
    training_samples = fields.Integer(string='Số mẫu huấn luyện')
    model_path = fields.Char(string='Đường dẫn model')
    
    @api.model
    def get_active_model(self):
        """Lấy model đang hoạt động"""
        return self.search([('is_active', '=', True)], limit=1)
    
    def action_train_model(self):
        """Nút huấn luyện mô hình AI"""
        try:
            _logger.info("=== BẮT ĐẦU HUẤN LUYỆN MÔ HÌNH AI ===")
            
            # Kiểm tra thư viện ML
            if not ML_AVAILABLE:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Thiếu thư viện',
                        'message': 'Vui lòng cài đặt: pip3 install scikit-learn pandas numpy joblib',
                        'type': 'danger',
                        'sticky': True
                    }
                }
            
            # Tạo thư mục lưu model
            module_path = os.path.dirname(os.path.dirname(__file__))
            model_dir = os.path.join(module_path, 'models', 'saved_models')
            
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
                _logger.info(f"Created model directory: {model_dir}")
            
            # Lấy dữ liệu lịch sử
            historical_data = self._get_historical_data()
            
            if not historical_data or len(historical_data) < 5:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Không đủ dữ liệu',
                        'message': f'Cần ít nhất 5 mẫu dữ liệu. Hiện có {len(historical_data)} mẫu.',
                        'type': 'warning',
                        'sticky': True
                    }
                }
            
            # Chuẩn bị dữ liệu
            X, y = self._prepare_features(historical_data)
            
            # Chia train/test
            test_size = 0.2 if len(historical_data) > 10 else 0.3
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Huấn luyện model
            model = RandomForestRegressor(
                n_estimators=50,
                max_depth=8,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train, y_train)
            
            # Đánh giá model
            if len(y_test) > 0:
                y_pred = model.predict(X_test)
                r2 = r2_score(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
            else:
                r2 = 0
                mae = 0
            
            _logger.info(f"Đánh giá model: R²={r2:.4f}, MAE={mae:.2f}")
            
            # Lưu model
            model_file = f'ai_model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
            model_path = os.path.join(model_dir, model_file)
            joblib.dump(model, model_path)
            
            # Lưu scaler
            scaler = StandardScaler()
            scaler.fit(X_train)
            scaler_path = os.path.join(model_dir, 'scaler.pkl')
            joblib.dump(scaler, scaler_path)
            
            # Lưu thông tin model
            self.write({
                'trained_date': datetime.now(),
                'accuracy': r2,
                'mae': mae,
                'training_samples': len(historical_data),
                'model_path': model_path
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Huấn luyện thành công!',
                    'message': f'R²: {r2:.4f}\nMAE: {mae:.2f}\nSố mẫu: {len(historical_data)}',
                    'type': 'success',
                    'sticky': False
                }
            }
            
        except Exception as e:
            _logger.error(f"Lỗi huấn luyện model: {str(e)}", exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi huấn luyện',
                    'message': f'{str(e)}',
                    'type': 'danger',
                    'sticky': True
                }
            }
    
    def _get_historical_data(self):
        """Lấy dữ liệu lịch sử để huấn luyện"""
        data = []
        
        # Lấy dữ liệu hỗ trợ khách hàng
        supports = self.env['ho_tro_khach_hang'].search([])
        _logger.info(f"Found {len(supports)} support records")
        
        for support in supports:
            if support.thoi_gian_bat_dau and support.nhan_vien_phu_trach:
                day_of_week = support.thoi_gian_bat_dau.weekday()
                month = support.thoi_gian_bat_dau.month
                hour = support.thoi_gian_bat_dau.hour
                
                data.append({
                    'day_of_week': day_of_week,
                    'month': month,
                    'hour': hour,
                    'employee_id': support.nhan_vien_phu_trach.id,
                    'workload': 1
                })
        
        _logger.info(f"Loaded {len(data)} support samples")
        
        # Thêm dữ liệu văn bản nếu có
        if 'van_ban_den' in self.env:
            docs = self.env['van_ban_den'].search([])
            for doc in docs:
                if doc.ngay_van_ban and doc.nhan_vien_xu_ly_id:
                    day_of_week = doc.ngay_van_ban.weekday()
                    month = doc.ngay_van_ban.month
                    
                    data.append({
                        'day_of_week': day_of_week,
                        'month': month,
                        'hour': 9,
                        'employee_id': doc.nhan_vien_xu_ly_id.id,
                        'workload': 1
                    })
            
            _logger.info(f"Added {len(docs)} document samples")
        
        return data
    
    def _prepare_features(self, data):
        """Chuẩn bị features cho model"""
        df = pd.DataFrame(data)
        
        features = ['day_of_week', 'month', 'hour', 'employee_id']
        X = df[features].values
        y = df['workload'].values
        
        return X, y
    
    def predict_with_ai(self, nhan_vien_id):
        """Dự đoán bằng AI model đã huấn luyện"""
        try:
            if not ML_AVAILABLE:
                return None
            
            if not self.model_path or not os.path.exists(self.model_path):
                _logger.warning("Chưa có model AI")
                return None
            
            # Load model
            model = joblib.load(self.model_path)
            
            # Load scaler
            module_path = os.path.dirname(os.path.dirname(__file__))
            scaler_path = os.path.join(module_path, 'models', 'saved_models', 'scaler.pkl')
            
            scaler = None
            if os.path.exists(scaler_path):
                scaler = joblib.load(scaler_path)
            
            # Lấy dữ liệu hiện tại
            now = datetime.now()
            features = np.array([[
                now.weekday(),
                now.month,
                now.hour,
                nhan_vien_id
            ]])
            
            # Scale features
            if scaler:
                features = scaler.transform(features)
            
            # Dự đoán
            prediction = model.predict(features)[0]
            
            # Độ tin cậy (đơn giản)
            confidence = min(95, max(50, 90 - abs(prediction - 5) * 2))
            
            return {
                'prediction': round(prediction, 1),
                'confidence': round(confidence, 1)
            }
            
        except Exception as e:
            _logger.error(f"Lỗi dự đoán AI: {str(e)}")
            return None