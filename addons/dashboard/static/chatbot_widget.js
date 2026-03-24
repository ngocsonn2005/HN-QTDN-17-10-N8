odoo.define('dashboard.chatbot_widget', function(require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var ChatbotWidget = AbstractAction.extend({
        
        events: {
            'click #send-message': '_onSendMessage',
            'keypress #chat-input': '_onKeyPress',
            'click #clear-chat': '_onClearChat',
        },

        init: function(parent, action) {
            this._super(parent, action);
            this.session_id = localStorage.getItem('chat_session_id') || null;
            this.current_model = 'openai_gpt4o_mini';
            this.messages = [];
            this.models = {}; // Thêm models để lưu danh sách model
        },

        start: function() {
            this._super.apply(this, arguments);
            this._renderWidget();
            this._loadModels(); // Thêm load models
            this._loadHistory();
            return Promise.resolve();
        },

        _renderWidget: function() {
            var html = `
                <div class="chatbot-widget">
                    <div class="chatbot-header">
                        <i class="fa fa-robot"></i>
                        <span>Trợ lý AI thông minh</span>
                        <button class="btn btn-sm btn-link" id="clear-chat">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                    <div class="chatbot-models" id="chatbot-models" style="padding:10px; border-bottom:1px solid #e3e6f0; background:#f8f9fc;">
                        <button class="btn btn-sm model-select active" data-model="openai_gpt4o_mini" style="background:#4e73df; color:white; border:none; border-radius:20px; padding:5px 12px; margin:2px;">
                            GPT-4o mini (OpenAI)
                        </button>
                        <button class="btn btn-sm model-select" data-model="gemini_pro" style="background:white; border:1px solid #e3e6f0; border-radius:20px; padding:5px 12px; margin:2px;">
                            Gemini 2.0 Flash (Google)
                        </button>
                    </div>
                    <div class="chat-messages" id="chat-messages-area" style="flex:1; overflow-y:auto; padding:20px; background:#f8f9fc;">
                        <div class="chat-message bot">
                            <div class="message-avatar" style="display:inline-block; width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#4e73df,#224abe); color:white; text-align:center; line-height:36px;">
                                <i class="fa fa-robot"></i>
                            </div>
                            <div class="message-content" style="display:inline-block; vertical-align:top; margin-left:10px; max-width:70%; background:white; padding:12px 16px; border-radius:18px;">
                                <div class="message-text">Xin chào! Tôi là trợ lý AI. Tôi có thể giúp gì cho bạn?</div>
                                <div class="message-time" style="font-size:0.7rem; opacity:0.7;">${new Date().toLocaleTimeString()}</div>
                            </div>
                        </div>
                    </div>
                    <div class="chat-input-area" style="display:flex; gap:10px; padding:15px; background:white; border-top:1px solid #e3e6f0;">
                        <input type="text" id="chat-input" class="form-control" style="flex:1; border-radius:25px; border:1px solid #e3e6f0; padding:10px 18px;" placeholder="Nhập câu hỏi của bạn..."/>
                        <button class="btn btn-primary" id="send-message" style="border-radius:50%; width:40px; height:40px;">
                            <i class="fa fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            `;
            this.$el.html(html);
            
            // Bind events cho model select
            var self = this;
            this.$('.model-select').on('click', function(e) {
                e.preventDefault();
                self.current_model = $(this).data('model');
                self.$('.model-select').removeClass('active').css({
                    'background': 'white',
                    'color': '#2e3b4e',
                    'border': '1px solid #e3e6f0'
                });
                $(this).addClass('active').css({
                    'background': '#4e73df',
                    'color': 'white',
                    'border': 'none'
                });
                console.log("Model changed to:", self.current_model);
            });
        },

        _loadModels: function() {
            var self = this;
            rpc.query({
                route: '/chatbot/models',
            }).then(function(result) {
                if (result.success && result.models) {
                    self.models = result.models;
                    self._updateModelsUI();
                }
            }).catch(function(error) {
                console.error("Error loading models:", error);
            });
        },

        _updateModelsUI: function() {
            var container = this.$('#chatbot-models');
            if (!container.length) return;
            
            var html = '';
            for (var key in this.models) {
                var activeClass = (key === this.current_model) ? 'active' : '';
                var activeStyle = (key === this.current_model) ? 
                    'background:#4e73df; color:white; border:none;' : 
                    'background:white; border:1px solid #e3e6f0; color:#2e3b4e;';
                html += `
                    <button class="btn btn-sm model-select ${activeClass}" data-model="${key}" 
                            style="border-radius:20px; padding:5px 12px; margin:2px; ${activeStyle}">
                        ${this._escapeHtml(this.models[key].label)}
                    </button>
                `;
            }
            container.html(html);
            
            // Re-bind events
            var self = this;
            this.$('.model-select').off('click').on('click', function(e) {
                e.preventDefault();
                self.current_model = $(this).data('model');
                self.$('.model-select').removeClass('active').css({
                    'background': 'white',
                    'color': '#2e3b4e',
                    'border': '1px solid #e3e6f0'
                });
                $(this).addClass('active').css({
                    'background': '#4e73df',
                    'color': 'white',
                    'border': 'none'
                });
                console.log("Model changed to:", self.current_model);
            });
        },

        _loadHistory: function() {
            var self = this;
            rpc.query({
                route: '/chatbot/history',
                params: {
                    session_id: this.session_id,
                    limit: 50
                }
            }).then(function(result) {
                if (result.success && result.messages && result.messages.length > 0) {
                    self.messages = result.messages;
                    self.session_id = result.session_id;
                    if (self.session_id) {
                        localStorage.setItem('chat_session_id', self.session_id);
                    }
                    self._updateMessages();
                }
            }).catch(function(error) {
                console.error("Error loading history:", error);
            });
        },

        _updateMessages: function() {
            var self = this;
            var chatArea = this.$('#chat-messages-area');
            if (!chatArea.length) return;
            
            chatArea.empty();
            for (var i = 0; i < this.messages.length; i++) {
                var msg = this.messages[i];
                var timeStr = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
                
                if (msg.is_bot) {
                    chatArea.append(`
                        <div class="chat-message bot">
                            <div class="message-avatar" style="display:inline-block; width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#4e73df,#224abe); color:white; text-align:center; line-height:36px;">
                                <i class="fa fa-robot"></i>
                            </div>
                            <div class="message-content" style="display:inline-block; vertical-align:top; margin-left:10px; max-width:70%; background:white; padding:12px 16px; border-radius:18px;">
                                <div class="message-text">${self._escapeHtml(msg.message)}</div>
                                <div class="message-time" style="font-size:0.7rem; opacity:0.7;">${timeStr}</div>
                            </div>
                        </div>
                    `);
                } else {
                    chatArea.append(`
                        <div class="chat-message user" style="text-align:right;">
                            <div class="message-content" style="display:inline-block; vertical-align:top; margin-right:10px; max-width:70%; background:#4e73df; color:white; padding:12px 16px; border-radius:18px;">
                                <div class="message-text">${self._escapeHtml(msg.message)}</div>
                                <div class="message-time" style="font-size:0.7rem; opacity:0.7;">${timeStr}</div>
                            </div>
                            <div class="message-avatar" style="display:inline-block; width:36px; height:36px; border-radius:50%; background:#1cc88a; color:white; text-align:center; line-height:36px;">
                                <i class="fa fa-user"></i>
                            </div>
                        </div>
                    `);
                }
            }
            this._scrollToBottom();
        },

        _onSendMessage: function(event) {
            event.preventDefault();
            var input = this.$('#chat-input');
            var message = input.val().trim();
            
            console.log("=== SEND MESSAGE ===");
            console.log("Message:", message);
            
            if (!message) {
                console.log("Empty message!");
                this._showError('Vui lòng nhập câu hỏi.');
                return;
            }
            
            input.val('');
            this._sendMessage(message);
        },

        _showError: function(message) {
            var chatArea = this.$('#chat-messages-area');
            chatArea.append(`
                <div class="chat-message bot">
                    <div class="message-avatar" style="display:inline-block; width:36px; height:36px; border-radius:50%; background:#dc3545; color:white; text-align:center; line-height:36px;">
                        <i class="fa fa-exclamation-triangle"></i>
                    </div>
                    <div class="message-content" style="display:inline-block; vertical-align:top; margin-left:10px; max-width:70%; background:#f8d7da; color:#721c24; padding:12px 16px; border-radius:18px;">
                        <div class="message-text">❌ ${this._escapeHtml(message)}</div>
                        <div class="message-time" style="font-size:0.7rem; opacity:0.7;">${new Date().toLocaleTimeString()}</div>
                    </div>
                </div>
            `);
            this._scrollToBottom();
            
            // Tự động xóa sau 5 giây
            setTimeout(function() {
                chatArea.find('.chat-message:last-child').fadeOut(300, function() {
                    $(this).remove();
                });
            }, 5000);
        },

        _onKeyPress: function(event) {
            if (event.keyCode === 13) {
                console.log("Enter key pressed!");
                event.preventDefault();
                var input = this.$('#chat-input');
                var message = input.val().trim();
                
                console.log("Message from input:", message);
                
                if (!message) {
                    this._showError('Vui lòng nhập câu hỏi.');
                    return;
                }
                
                input.val('');
                this._sendMessage(message);
            }
        },

        _onClearChat: function(event) {
            event.preventDefault();
            var self = this;
            if (confirm('Bạn có chắc muốn xóa lịch sử chat?')) {
                rpc.query({
                    route: '/chatbot/clear_history',
                    params: {
                        session_id: this.session_id
                    }
                }).then(function(result) {
                    if (result.success) {
                        self.messages = [];
                        self.session_id = null;
                        localStorage.removeItem('chat_session_id');
                        var chatArea = self.$('#chat-messages-area');
                        chatArea.html(`
                            <div class="chat-message bot">
                                <div class="message-avatar" style="display:inline-block; width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#4e73df,#224abe); color:white; text-align:center; line-height:36px;">
                                    <i class="fa fa-robot"></i>
                                </div>
                                <div class="message-content" style="display:inline-block; vertical-align:top; margin-left:10px; max-width:70%; background:white; padding:12px 16px; border-radius:18px;">
                                    <div class="message-text">Xin chào! Tôi là trợ lý AI. Tôi có thể giúp gì cho bạn?</div>
                                    <div class="message-time" style="font-size:0.7rem; opacity:0.7;">${new Date().toLocaleTimeString()}</div>
                                </div>
                            </div>
                        `);
                    }
                }).catch(function(error) {
                    console.error("Error clearing history:", error);
                });
            }
        },

        _sendMessage: function(message) {
            var self = this;
            var chatArea = this.$('#chat-messages-area');
            
            console.log("=== SENDING TO SERVER ===");
            console.log("Question:", message);
            console.log("Model:", this.current_model);
            console.log("Session ID:", this.session_id);
            
            // Thêm tin nhắn user
            chatArea.append(`
                <div class="chat-message user" style="text-align:right;">
                    <div class="message-content" style="display:inline-block; vertical-align:top; margin-right:10px; max-width:70%; background:#4e73df; color:white; padding:12px 16px; border-radius:18px;">
                        <div class="message-text">${this._escapeHtml(message)}</div>
                        <div class="message-time" style="font-size:0.7rem; opacity:0.7;">${new Date().toLocaleTimeString()}</div>
                    </div>
                    <div class="message-avatar" style="display:inline-block; width:36px; height:36px; border-radius:50%; background:#1cc88a; color:white; text-align:center; line-height:36px;">
                        <i class="fa fa-user"></i>
                    </div>
                </div>
            `);
            
            // Thêm loading
            var loadingId = 'loading-' + Date.now();
            chatArea.append(`
                <div class="chat-message bot" id="${loadingId}">
                    <div class="message-avatar" style="display:inline-block; width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#4e73df,#224abe); color:white; text-align:center; line-height:36px;">
                        <i class="fa fa-robot"></i>
                    </div>
                    <div class="message-content" style="display:inline-block; vertical-align:top; margin-left:10px; max-width:70%; background:white; padding:12px 16px; border-radius:18px;">
                        <div class="message-text">Đang suy nghĩ...</div>
                        <div class="message-time" style="font-size:0.7rem; opacity:0.7;">${new Date().toLocaleTimeString()}</div>
                    </div>
                </div>
            `);
            this._scrollToBottom();
            
            // Gọi API
            rpc.query({
                route: '/chatbot/ask',
                params: {
                    question: message,
                    model_key: this.current_model,
                    session_id: this.session_id
                }
            }).then(function(result) {
                console.log("=== SERVER RESPONSE ===");
                console.log(result);
                
                // Xóa loading
                self.$('#' + loadingId).remove();
                
                if (result && result.success) {
                    self.session_id = result.session_id;
                    if (self.session_id) {
                        localStorage.setItem('chat_session_id', self.session_id);
                    }
                    
                    chatArea.append(`
                        <div class="chat-message bot">
                            <div class="message-avatar" style="display:inline-block; width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#4e73df,#224abe); color:white; text-align:center; line-height:36px;">
                                <i class="fa fa-robot"></i>
                            </div>
                            <div class="message-content" style="display:inline-block; vertical-align:top; margin-left:10px; max-width:70%; background:white; padding:12px 16px; border-radius:18px;">
                                <div class="message-text">${self._escapeHtml(result.answer)}</div>
                                <div class="message-time" style="font-size:0.7rem; opacity:0.7;">${new Date().toLocaleTimeString()}</div>
                            </div>
                        </div>
                    `);
                    
                    self.messages.push({
                        message: message,
                        is_bot: false,
                        timestamp: new Date().toISOString()
                    });
                    self.messages.push({
                        message: result.answer,
                        is_bot: true,
                        timestamp: new Date().toISOString()
                    });
                } else {
                    var errorMsg = (result && result.error) ? result.error : 'Lỗi không xác định';
                    chatArea.append(`
                        <div class="chat-message bot">
                            <div class="message-avatar" style="display:inline-block; width:36px; height:36px; border-radius:50%; background:#dc3545; color:white; text-align:center; line-height:36px;">
                                <i class="fa fa-exclamation-triangle"></i>
                            </div>
                            <div class="message-content" style="display:inline-block; vertical-align:top; margin-left:10px; max-width:70%; background:#f8d7da; color:#721c24; padding:12px 16px; border-radius:18px;">
                                <div class="message-text">❌ ${self._escapeHtml(errorMsg)}</div>
                                <div class="message-time" style="font-size:0.7rem; opacity:0.7;">${new Date().toLocaleTimeString()}</div>
                            </div>
                        </div>
                    `);
                }
                self._scrollToBottom();
            }).catch(function(error) {
                console.error("=== REQUEST ERROR ===");
                console.error(error);
                self.$('#' + loadingId).remove();
                chatArea.append(`
                    <div class="chat-message bot">
                        <div class="message-avatar" style="display:inline-block; width:36px; height:36px; border-radius:50%; background:#dc3545; color:white; text-align:center; line-height:36px;">
                            <i class="fa fa-exclamation-triangle"></i>
                        </div>
                        <div class="message-content" style="display:inline-block; vertical-align:top; margin-left:10px; max-width:70%; background:#f8d7da; color:#721c24; padding:12px 16px; border-radius:18px;">
                            <div class="message-text">❌ Lỗi kết nối: ${self._escapeHtml(error.message || 'Không xác định')}</div>
                            <div class="message-time" style="font-size:0.7rem; opacity:0.7;">${new Date().toLocaleTimeString()}</div>
                        </div>
                    </div>
                `);
                self._scrollToBottom();
            });
        },

        _scrollToBottom: function() {
            var chatArea = this.$('#chat-messages-area');
            if (chatArea.length) {
                chatArea.scrollTop(chatArea[0].scrollHeight);
            }
        },

        _escapeHtml: function(text) {
            if (!text) return '';
            var div = document.createElement('div');
            div.appendChild(document.createTextNode(text));
            return div.innerHTML;
        }
    });

    core.action_registry.add('chatbot', ChatbotWidget);
    return ChatbotWidget;
});