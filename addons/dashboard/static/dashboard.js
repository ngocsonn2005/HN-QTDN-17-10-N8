odoo.define('dashboard.dashboard', function(require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var Dashboard = AbstractAction.extend({
        start: function() {
            var self = this;
            this._renderDashboard();
            this.load_data();
            return this._super.apply(this, arguments);
        },

        _renderDashboard: function() {
            var html = `
                <div class="o_dashboard">
                    <h2>📊 Dashboard tổng hợp</h2>
                    
                    <div class="dashboard-grid">
                        <!-- Nhân sự card -->
                        <div class="dashboard-card">
                            <div class="card-header bg-primary-gradient">
                                <i class="fa fa-users mr-2"></i> Nhân sự
                            </div>
                            <div class="card-body">
                                <div class="stat-item">
                                    <span class="stat-label">Tổng số</span>
                                    <span class="stat-value tong-nv">0</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Dưới 30 tuổi</span>
                                    <span class="stat-value nv-duoi30">0</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">30-45 tuổi</span>
                                    <span class="stat-value nv-30-45">0</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Trên 45 tuổi</span>
                                    <span class="stat-value nv-tren45">0</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Tuổi trung bình</span>
                                    <span class="stat-value tuoi-tb">0</span>
                                </div>
                            </div>
                        </div>

                        <!-- Khách hàng card -->
                        <div class="dashboard-card">
                            <div class="card-header bg-success-gradient">
                                <i class="fa fa-handshake-o mr-2"></i> Khách hàng
                            </div>
                            <div class="card-body">
                                <div class="stat-item">
                                    <span class="stat-label">Tổng khách hàng</span>
                                    <span class="stat-value tong-kh">0</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Tổng hỗ trợ</span>
                                    <span class="stat-value tong-ht">0</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Hỗ trợ mới (7 ngày)</span>
                                    <span class="stat-value ht-moi">0</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Đang chờ xử lý</span>
                                    <span class="stat-value ht-cho">0</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Đánh giá trung bình</span>
                                    <span class="stat-value danh-gia">0</span>
                                </div>
                            </div>
                        </div>

                        <!-- Văn bản card -->
                        <div class="dashboard-card">
                            <div class="card-header bg-warning-gradient">
                                <i class="fa fa-file-text-o mr-2"></i> Văn bản
                            </div>
                            <div class="card-body">
                                <div class="stat-item">
                                    <span class="stat-label">Tổng văn bản</span>
                                    <span class="stat-value tong-vb">0</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Tháng này</span>
                                    <span class="stat-value vb-thang-nay">0</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Tháng trước</span>
                                    <span class="stat-value vb-thang-truoc">0</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Tăng trưởng</span>
                                    <span class="stat-value tang-truong">0%</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Khu vực AI -->
                    <div style="margin-top: 30px; text-align: center;">
                        <button class="btn btn-ai" id="predict_button">
                            <i class="fa fa-robot mr-2"></i> Dự đoán AI - Khối lượng công việc nhân viên
                        </button>
                        <button class="btn btn-ai-outline" id="test_button">
                            <i class="fa fa-flask mr-2"></i> Test AI Route
                        </button>
                    </div>

                    <!-- Kết quả dự đoán -->
                    <div id="prediction_result" style="margin-top: 30px;"></div>
                </div>
            `;
            
            this.$el.html(html);
            this.$('#predict_button').click(this.predict_staff.bind(this));
            this.$('#test_button').click(this.test_ai.bind(this));
        },

        load_data: function() {
            var self = this;
            rpc.query({
                route: '/dashboard/data',
            }).then(function(data) {
                self.update_display(data);
            }).catch(function(error) {
                console.error("Error loading data:", error);
                self.$el.prepend('<div class="alert alert-danger">Lỗi tải dữ liệu: ' + JSON.stringify(error) + '</div>');
            });
        },

        update_display: function(data) {
            if (data.error) {
                console.error("Data error:", data.error);
                return;
            }
            
            // Nhân sự
            this.$('.tong-nv').text(data.nhan_su.tong || 0);
            this.$('.nv-duoi30').text(data.nhan_su.duoi30 || 0);
            this.$('.nv-30-45').text(data.nhan_su['30_45'] || 0);
            this.$('.nv-tren45').text(data.nhan_su.tren45 || 0);
            this.$('.tuoi-tb').text(data.nhan_su.tuoi_tb || 0);
            
            // Khách hàng
            this.$('.tong-kh').text(data.khach_hang.tong || 0);
            this.$('.tong-ht').text(data.khach_hang.ho_tro.tong || 0);
            this.$('.ht-moi').text(data.khach_hang.ho_tro.moi || 0);
            this.$('.ht-cho').text(data.khach_hang.ho_tro.cho || 0);
            this.$('.danh-gia').text(data.khach_hang.ho_tro.danh_gia || 0);
            
            // Văn bản
            this.$('.tong-vb').text(data.van_ban.tong || 0);
            this.$('.vb-thang-nay').text(data.van_ban.thang_nay || 0);
            this.$('.vb-thang-truoc').text(data.van_ban.thang_truoc || 0);
            this.$('.tang-truong').text((data.van_ban.tang_truong || 0) + '%');
        },

        test_ai: function() {
            window.open('/ai/test', '_blank');
        },

        predict_staff: function() {
            var self = this;
            
            rpc.query({
                model: 'nhan_vien',
                method: 'search_read',
                fields: ['id', 'ho_va_ten'],
            }).then(function(employees) {
                if (!employees.length) {
                    alert("Không có nhân viên nào trong hệ thống!");
                    return;
                }
                
                var options = employees.map(function(emp) {
                    return emp.id + ': ' + emp.ho_va_ten;
                }).join('\n');
                
                var nv_id = prompt("Chọn ID nhân viên từ danh sách:\n" + options);
                if (nv_id) {
                    self.call_predict(parseInt(nv_id));
                }
            }).catch(function(error) {
                var nv_id = prompt("Nhập ID nhân viên:");
                if (nv_id) {
                    self.call_predict(parseInt(nv_id));
                }
            });
        },

        call_predict: function(nv_id) {
            var self = this;
            rpc.query({
                route: '/ai/predict/' + nv_id,
            }).then(function(result) {
                if (result.error) {
                    alert("Lỗi: " + result.error);
                } else {
                    var resultHtml = `
                        <div class="dashboard-card" style="margin-top: 20px;">
                            <div class="card-header bg-info-gradient">
                                <i class="fa fa-robot mr-2"></i> Kết quả dự đoán cho ${result.nhan_vien}
                            </div>
                            <div class="card-body">
                                <div class="stat-item">
                                    <span class="stat-label">Dự đoán khối lượng</span>
                                    <span class="stat-value">${result.du_doan} công việc/ngày</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Độ tin cậy</span>
                                    <span class="stat-value">${result.do_tin_cay}%</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Dữ liệu 4 tuần</span>
                                    <span class="stat-value">${result.lich_su.join(' → ')}</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Khuyến nghị</span>
                                    <span class="stat-value" style="font-size:1rem;">${result.khuyen_nghi}</span>
                                </div>
                            </div>
                        </div>
                    `;
                    self.$('#prediction_result').html(resultHtml);
                }
            }).catch(function(error) {
                console.error("Predict error:", error);
                alert("Lỗi kết nối: " + JSON.stringify(error));
            });
        },
    });

    core.action_registry.add('dashboard', Dashboard);
    return Dashboard;
});