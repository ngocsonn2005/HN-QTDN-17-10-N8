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
            this._startAutoRefresh();
            return this._super.apply(this, arguments);
        },

        _startAutoRefresh: function() {
            var self = this;
            setInterval(function() {
                self.load_data(true);
            }, 300000);
        },

        _renderDashboard: function() {
            var html = `
                <div class="o_dashboard">
                    <!-- Header với thời gian -->
                    <div class="dashboard-header">
                        <div class="header-left">
                            <h2>
                                <i class="fa fa-dashboard"></i> 
                                Dashboard tổng hợp
                            </h2>
                            <p class="text-muted">
                                <i class="fa fa-calendar"></i> 
                                <span id="current-datetime">${this._getCurrentDateTime()}</span>
                            </p>
                        </div>
                        <div class="header-right">
                            <button class="btn btn-refresh" id="refresh-btn">
                                <i class="fa fa-refresh"></i> Làm mới
                            </button>
                        </div>
                    </div>

                    <!-- KPI Cards -->
                    <div class="kpi-grid">
                        <div class="kpi-card">
                            <div class="kpi-icon bg-primary">
                                <i class="fa fa-users"></i>
                            </div>
                            <div class="kpi-content">
                                <span class="kpi-label">Tổng nhân viên</span>
                                <span class="kpi-value tong-nv">0</span>
                            </div>
                        </div>

                        <div class="kpi-card">
                            <div class="kpi-icon bg-success">
                                <i class="fa fa-handshake-o"></i>
                            </div>
                            <div class="kpi-content">
                                <span class="kpi-label">Tổng khách hàng</span>
                                <span class="kpi-value tong-kh">0</span>
                            </div>
                        </div>

                        <div class="kpi-card">
                            <div class="kpi-icon bg-warning">
                                <i class="fa fa-file-text"></i>
                            </div>
                            <div class="kpi-content">
                                <span class="kpi-label">Tổng văn bản</span>
                                <span class="kpi-value tong-vb">0</span>
                            </div>
                        </div>

                        <div class="kpi-card">
                            <div class="kpi-icon bg-info">
                                <i class="fa fa-tasks"></i>
                            </div>
                            <div class="kpi-content">
                                <span class="kpi-label">Hỗ trợ đang chờ</span>
                                <span class="kpi-value ht-cho">0</span>
                            </div>
                        </div>
                    </div>

                    <!-- Charts Row -->
                    <div class="charts-row">
                        <div class="chart-card">
                            <div class="chart-header">
                                <h4><i class="fa fa-pie-chart"></i> Phân bố nhân viên theo độ tuổi</h4>
                            </div>
                            <div class="chart-body">
                                <canvas id="ageChart" width="400" height="200"></canvas>
                                <div class="chart-stats">
                                    <div class="stat-badge"><30: <span class="nv-duoi30">0</span></div>
                                    <div class="stat-badge">30-45: <span class="nv-30-45">0</span></div>
                                    <div class="stat-badge">>45: <span class="nv-tren45">0</span></div>
                                </div>
                            </div>
                        </div>

                        <div class="chart-card">
                            <div class="chart-header">
                                <h4><i class="fa fa-line-chart"></i> Xu hướng văn bản</h4>
                            </div>
                            <div class="chart-body">
                                <canvas id="docChart" width="400" height="200"></canvas>
                                <div class="chart-stats">
                                    <div class="stat-badge">Tháng này: <span class="vb-thang-nay">0</span></div>
                                    <div class="stat-badge">Tháng trước: <span class="vb-thang-truoc">0</span></div>
                                    <div class="stat-badge">Tăng trưởng: <span class="tang-truong">0%</span></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Detailed Stats Cards -->
                    <div class="dashboard-grid">
                        <!-- Nhân sự card chi tiết -->
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

                        <!-- Khách hàng card chi tiết -->
                        <div class="dashboard-card">
                            <div class="card-header bg-success-gradient">
                                <i class="fa fa-handshake-o mr-2"></i> Khách hàng & Hỗ trợ
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
                                    <span class="stat-value danh-gia">
                                        <span class="rating-stars" id="rating-stars"></span>
                                    </span>
                                </div>
                            </div>
                        </div>

                        <!-- Văn bản card chi tiết -->
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

                    <!-- AI Prediction Section -->
                    <div class="ai-section">
                        <div class="ai-header">
                            <div class="ai-title">
                                <i class="fa fa-robot"></i>
                                <h3>Trợ lý AI thông minh</h3>
                            </div>
                            <div class="ai-controls">
                                <select id="employee-select" class="employee-select">
                                    <option value="">Chọn nhân viên...</option>
                                </select>
                                <button class="btn-ai" id="train_ai_button">
                                    <i class="fa fa-brain"></i> Huấn luyện AI
                                </button>
                                <button class="btn-ai" id="predict_button">
                                    <i class="fa fa-magic"></i> Dự đoán
                                </button>
                            </div>
                        </div>

                        <!-- Kết quả dự đoán -->
                        <div id="prediction_result" class="prediction-result"></div>
                    </div>
                </div>
            `;
            
            this.$el.html(html);
            this._initEventHandlers();
            this._loadEmployees();
        },

        _initEventHandlers: function() {
            this.$('#train_ai_button').click(this.train_ai.bind(this));
            this.$('#predict_button').click(this.predict_staff.bind(this));
            this.$('#refresh-btn').click(() => this.load_data());
        },

        _getCurrentDateTime: function() {
            var now = new Date();
            return now.toLocaleDateString('vi-VN', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        _loadEmployees: function() {
            var self = this;
            rpc.query({
                model: 'nhan_vien',
                method: 'search_read',
                fields: ['id', 'ho_va_ten'],
            }).then(function(employees) {
                var select = self.$('#employee-select');
                select.empty().append('<option value="">Chọn nhân viên...</option>');
                employees.forEach(function(emp) {
                    select.append(`<option value="${emp.id}">${emp.ho_va_ten}</option>`);
                });
            }).catch(function(error) {
                console.error("Error loading employees:", error);
            });
        },

        load_data: function(silent) {
            var self = this;
            if (!silent) {
                this.$el.find('.o_dashboard').addClass('loading');
            }
            
            rpc.query({
                route: '/dashboard/data',
            }).then(function(data) {
                self.update_display(data);
                if (!silent) {
                    self.$el.find('.o_dashboard').removeClass('loading');
                }
            }).catch(function(error) {
                console.error("Error loading data:", error);
                if (!silent) {
                    self.$el.find('.o_dashboard').removeClass('loading');
                }
            });
        },

        update_display: function(data) {
            if (data.error) {
                console.error("Data error:", data.error);
                return;
            }
            
            this.$('.tong-nv').text(data.nhan_su.tong || 0);
            this.$('.nv-duoi30').text(data.nhan_su.duoi30 || 0);
            this.$('.nv-30-45').text(data.nhan_su['30_45'] || 0);
            this.$('.nv-tren45').text(data.nhan_su.tren45 || 0);
            this.$('.tuoi-tb').text(data.nhan_su.tuoi_tb || 0);
            
            this.$('.tong-kh').text(data.khach_hang.tong || 0);
            this.$('.tong-ht').text(data.khach_hang.ho_tro.tong || 0);
            this.$('.ht-moi').text(data.khach_hang.ho_tro.moi || 0);
            this.$('.ht-cho').text(data.khach_hang.ho_tro.cho || 0);
            this.$('.danh-gia').text(data.khach_hang.ho_tro.danh_gia || 0);
            this._updateRatingStars(data.khach_hang.ho_tro.danh_gia || 0);
            
            this.$('.tong-vb').text(data.van_ban.tong || 0);
            this.$('.vb-thang-nay').text(data.van_ban.thang_nay || 0);
            this.$('.vb-thang-truoc').text(data.van_ban.thang_truoc || 0);
            this.$('.tang-truong').text((data.van_ban.tang_truong || 0) + '%');
            
            this._updateCharts(data);
        },

        _updateRatingStars: function(rating) {
            var stars = '';
            for (var i = 1; i <= 5; i++) {
                if (i <= Math.round(rating)) {
                    stars += '<i class="fa fa-star star-filled"></i>';
                } else {
                    stars += '<i class="fa fa-star-o star-empty"></i>';
                }
            }
            this.$('#rating-stars').html(stars);
        },

        _updateCharts: function(data) {
            this._createAgeChart(data);
            this._createDocumentChart(data);
        },

        _createAgeChart: function(data) {
            var ctx = document.getElementById('ageChart');
            if (!ctx) return;
            
            ctx = ctx.getContext('2d');
            
            if (this.ageChart) {
                this.ageChart.destroy();
            }
            
            this.ageChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Dưới 30', '30-45', 'Trên 45'],
                    datasets: [{
                        data: [
                            data.nhan_su.duoi30 || 0,
                            data.nhan_su['30_45'] || 0,
                            data.nhan_su.tren45 || 0
                        ],
                        backgroundColor: ['#4e73df', '#1cc88a', '#f6c23e'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '70%',
                    plugins: { legend: { display: false } }
                }
            });
        },

        _createDocumentChart: function(data) {
            var ctx = document.getElementById('docChart');
            if (!ctx) return;
            
            ctx = ctx.getContext('2d');
            
            if (this.docChart) {
                this.docChart.destroy();
            }
            
            this.docChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Tháng trước', 'Tháng này'],
                    datasets: [{
                        label: 'Số lượng văn bản',
                        data: [data.van_ban.thang_truoc || 0, data.van_ban.thang_nay || 0],
                        borderColor: '#4e73df',
                        backgroundColor: 'rgba(78, 115, 223, 0.05)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } }
                }
            });
        },

        train_ai: function() {
            var self = this;
            var resultDiv = this.$('#prediction_result');
            
            resultDiv.html('<div class="loading-spinner"><i class="fa fa-spinner fa-spin"></i> Đang huấn luyện AI model...</div>');
            
            // Gọi route đã thêm vào controllers.py
            rpc.query({
                route: '/ai/train_model',
            }).then(function(result) {
                console.log("Train result:", result);
                
                if (result && result.params) {
                    if (result.params.type === 'danger') {
                        resultDiv.html(`
                            <div class="alert alert-danger">
                                <i class="fa fa-exclamation-circle"></i> <strong>${result.params.title}</strong>
                                <br><small>${result.params.message}</small>
                            </div>
                        `);
                    } else {
                        resultDiv.html(`
                            <div class="alert alert-success">
                                <i class="fa fa-check-circle"></i> <strong>${result.params.title}</strong>
                                <br><small>${result.params.message.replace(/\n/g, '<br>')}</small>
                            </div>
                        `);
                    }
                } else {
                    resultDiv.html(`
                        <div class="alert alert-success">
                            <i class="fa fa-check-circle"></i> <strong>Huấn luyện thành công!</strong>
                            <br><small>Model AI đã được huấn luyện và sẵn sàng sử dụng.</small>
                        </div>
                    `);
                }
            }).catch(function(error) {
                console.error("Train AI error:", error);
                
                let errorMessage = 'Không xác định';
                if (error.message) {
                    errorMessage = error.message;
                } else if (error.data && error.data.message) {
                    errorMessage = error.data.message;
                } else if (error.data && error.data.arguments && error.data.arguments[0]) {
                    errorMessage = error.data.arguments[0];
                }
                
                resultDiv.html(`
                    <div class="alert alert-danger">
                        <i class="fa fa-exclamation-circle"></i> <strong>Lỗi huấn luyện AI</strong>
                        <br><small>${errorMessage}</small>
                        <br><br>
                        <strong>Thông tin:</strong>
                        <ul>
                            <li>Model đã được huấn luyện thành công từ AI Model Manager</li>
                            <li>Vui lòng làm mới trang và thử lại dự đoán</li>
                        </ul>
                    </div>
                `);
            });
        },

        predict_staff: function() {
            var nv_id = this.$('#employee-select').val();
            if (!nv_id) {
                alert("Vui lòng chọn nhân viên!");
                return;
            }
            this.call_predict(parseInt(nv_id));
        },

        call_predict: function(nv_id) {
            var self = this;
            var resultDiv = this.$('#prediction_result');
            
            resultDiv.html('<div class="loading-spinner"><i class="fa fa-spinner fa-spin"></i> Đang xử lý dự đoán...</div>');
            
            rpc.query({
                route: '/ai/predict/' + nv_id,
            }).then(function(result) {
                if (result.error) {
                    resultDiv.html(`<div class="alert alert-danger">Lỗi: ${result.error}</div>`);
                } else {
                    self._renderPredictionResult(result);
                }
            }).catch(function(error) {
                console.error("Predict error:", error);
                resultDiv.html('<div class="alert alert-danger">Lỗi kết nối đến AI service</div>');
            });
        },

        _renderPredictionResult: function(result) {
            var statusClass = '';
            var statusIcon = '';
            
            if (result.du_doan > 15) {
                statusClass = 'critical';
                statusIcon = '🔴';
            } else if (result.du_doan > 10) {
                statusClass = 'high';
                statusIcon = '🟡';
            } else if (result.du_doan > 5) {
                statusClass = 'medium';
                statusIcon = '🟢';
            } else if (result.du_doan > 0) {
                statusClass = 'low';
                statusIcon = '🔵';
            } else {
                statusClass = 'none';
                statusIcon = '⚪';
            }
            
            var resultHtml = `
                <div class="prediction-card">
                    <div class="prediction-header">
                        <i class="fa fa-robot"></i>
                        <h4>Kết quả dự đoán cho <span class="employee-name">${result.nhan_vien}</span></h4>
                        <span class="status-badge ${statusClass}">${statusIcon} ${result.khuyen_nghi.split('!')[0]}</span>
                    </div>
                    <div class="prediction-body">
                        <div class="prediction-stats">
                            <div class="prediction-stat">
                                <span class="stat-label">Dự đoán khối lượng</span>
                                <span class="stat-value">${result.du_doan} <small>công việc/ngày</small></span>
                            </div>
                            <div class="prediction-stat">
                                <span class="stat-label">Độ tin cậy</span>
                                <span class="stat-value confidence-${Math.floor(result.do_tin_cay/25)*25}">${result.do_tin_cay}%</span>
                            </div>
                        </div>
                        <div class="workload-history">
                            <h5>Lịch sử 4 tuần gần nhất:</h5>
                            <div class="trend-bars">
                                ${result.lich_su.map((value, index) => `
                                    <div class="trend-bar" style="height: ${Math.min(value * 5, 100)}px">
                                        <span class="bar-value">${value}</span>
                                    </div>
                                `).join('')}
                            </div>
                            <div class="trend-labels">
                                <span>Tuần 4</span>
                                <span>Tuần 3</span>
                                <span>Tuần 2</span>
                                <span>Tuần 1</span>
                            </div>
                        </div>
                        <div class="recommendation">
                            <div class="rec-icon ${statusClass}">
                                ${statusIcon}
                            </div>
                            <div class="rec-text">${result.khuyen_nghi}</div>
                        </div>
                    </div>
                </div>
            `;
            this.$('#prediction_result').html(resultHtml);
        }
    });

    // Load Chart.js
    if (typeof Chart === 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
        document.head.appendChild(script);
    }

    core.action_registry.add('dashboard', Dashboard);
    return Dashboard;
});