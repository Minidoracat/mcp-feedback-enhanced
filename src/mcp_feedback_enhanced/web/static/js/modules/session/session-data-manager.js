/**
 * MCP Feedback Enhanced - 會話數據管理模組
 * ========================================
 * 
 * 負責會話數據的存儲、更新和狀態管理
 */

(function() {
    'use strict';

    // 確保命名空間存在
    window.MCPFeedback = window.MCPFeedback || {};
    window.MCPFeedback.Session = window.MCPFeedback.Session || {};

    const TimeUtils = window.MCPFeedback.Utils.Time;
    const StatusUtils = window.MCPFeedback.Utils.Status;

    /**
     * 會話數據管理器
     */
    function SessionDataManager(options) {
        options = options || {};

        // 會話數據
        this.currentSession = null;
        this.sessionHistory = [];
        this.lastStatusUpdate = null;

        // 統計數據
        this.sessionStats = {
            todayCount: 0,
            averageDuration: 0
        };

        // 設定管理器
        this.settingsManager = options.settingsManager || null;

        // 回調函數
        this.onSessionChange = options.onSessionChange || null;
        this.onHistoryChange = options.onHistoryChange || null;
        this.onStatsChange = options.onStatsChange || null;
        this.onDataChanged = options.onDataChanged || null;

        // 初始化：載入歷史記錄並清理過期資料
        // 注意：loadFromServer 是異步的，會在載入完成後自動觸發更新
        this.loadFromServer();

        console.log('📊 SessionDataManager 初始化完成');
    }

    /**
     * 更新當前會話
     */
    SessionDataManager.prototype.updateCurrentSession = function(sessionData) {
        console.log('📊 更新當前會話:', sessionData);

        if (this.currentSession && this.currentSession.session_id === sessionData.session_id) {
            // 合併數據，保留重要資訊
            this.currentSession = this.mergeSessionData(this.currentSession, sessionData);
        } else {
            // 新會話或不同會話 ID - 需要處理舊會話
            if (this.currentSession && this.currentSession.session_id) {
                console.log('📊 檢測到會話 ID 變更，處理舊會話:', this.currentSession.session_id, '->', sessionData.session_id);

                // 將舊會話加入歷史記錄，保持其原有狀態
                const oldSession = Object.assign({}, this.currentSession);

                // 完全保持舊會話的原有狀態，不做任何修改
                // 讓服務器端負責狀態轉換，前端只負責顯示
                console.log('📊 保持舊會話的原有狀態:', oldSession.status);

                oldSession.completed_at = TimeUtils.getCurrentTimestamp();

                // 計算持續時間
                if (oldSession.created_at && !oldSession.duration) {
                    oldSession.duration = oldSession.completed_at - oldSession.created_at;
                }

                console.log('📊 將舊會話加入歷史記錄:', oldSession);
                this.addSessionToHistory(oldSession);
            }

            // 設置新會話
            this.currentSession = this.normalizeSessionData(sessionData);
        }

        // 觸發回調
        if (this.onSessionChange) {
            this.onSessionChange(this.currentSession);
        }

        return this.currentSession;
    };

    /**
     * 獲取實時會話列表
     */
    SessionDataManager.prototype.fetchRealtimeSessions = function(lang) {
        return fetch('/api/all-sessions?lang=' + lang)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('獲取實時會話狀態失敗: ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                if (data && Array.isArray(data.sessions)) {
                    return data.sessions;
                }
                throw new Error('實時會話狀態回應格式錯誤');
            });
    };

    /**
     * 從歷史文件獲取會話列表
     */
    SessionDataManager.prototype.fetchHistorySessions = function(lang) {
        return fetch('/api/load-session-history?lang=' + lang)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('伺服器回應錯誤: ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                if (data && Array.isArray(data.sessions)) {
                    return data.sessions;
                }
                return [];
            });
    };

    /**
     * 按 session_id 合併會話，優先使用實時數據，保留歷史中的完整記錄
     */
    SessionDataManager.prototype.mergeSessionsById = function(historySessions, realtimeSessions) {
        const sessionMap = new Map();

        historySessions.forEach(function(session) {
            if (session && session.session_id) {
                sessionMap.set(session.session_id, session);
            }
        });

        realtimeSessions.forEach(function(session) {
            if (!session || !session.session_id) {
                return;
            }

            const existing = sessionMap.get(session.session_id);
            if (existing) {
                // 實時資料覆蓋狀態類欄位，保留歷史資料中的補充欄位
                sessionMap.set(session.session_id, Object.assign({}, existing, session));
            } else {
                sessionMap.set(session.session_id, session);
            }
        });

        return Array.from(sessionMap.values()).sort(function(a, b) {
            const aTime = a.created_at || a.saved_at || 0;
            const bTime = b.created_at || b.saved_at || 0;
            return bTime - aTime;
        });
    };

    /**
     * 合併會話數據
     */
    SessionDataManager.prototype.mergeSessionData = function(existingData, newData) {
        const merged = Object.assign({}, existingData, newData);

        // 確保重要欄位不會被覆蓋為空值
        if (!merged.created_at && existingData.created_at) {
            merged.created_at = existingData.created_at;
        }

        if (!merged.status && existingData.status) {
            merged.status = existingData.status;
        }

        return merged;
    };

    /**
     * 標準化會話數據
     */
    SessionDataManager.prototype.normalizeSessionData = function(sessionData) {
        const normalized = Object.assign({}, sessionData);

        // 補充缺失的時間戳
        if (!normalized.created_at) {
            if (this.lastStatusUpdate && this.lastStatusUpdate.created_at) {
                normalized.created_at = this.lastStatusUpdate.created_at;
            } else {
                normalized.created_at = TimeUtils.getCurrentTimestamp();
            }
        }

        // 補充缺失的狀態
        if (!normalized.status) {
            normalized.status = 'waiting';
        }

        // 標準化時間戳
        if (normalized.created_at) {
            normalized.created_at = TimeUtils.normalizeTimestamp(normalized.created_at);
        }

        return normalized;
    };

    /**
     * 更新狀態資訊
     */
    SessionDataManager.prototype.updateStatusInfo = function(statusInfo) {
        console.log('📊 更新狀態資訊:', statusInfo);

        this.lastStatusUpdate = statusInfo;

        if (statusInfo.session_id || statusInfo.created_at) {
            const sessionData = {
                session_id: statusInfo.session_id || (this.currentSession && this.currentSession.session_id),
                status: statusInfo.status,
                created_at: statusInfo.created_at,
                project_directory: statusInfo.project_directory || this.getProjectDirectory(),
                summary: statusInfo.summary || this.getAISummary()
            };

            // 檢查會話是否完成
            if (StatusUtils.isCompletedStatus(statusInfo.status)) {
                this.handleSessionCompleted(sessionData);
            } else {
                this.updateCurrentSession(sessionData);
            }
        }
    };

    /**
     * 處理會話完成
     */
    SessionDataManager.prototype.handleSessionCompleted = function(sessionData) {
        console.log('📊 處理會話完成:', sessionData);

        // 優先使用用戶最後互動時間作為完成時間
        if (this.currentSession &&
            this.currentSession.session_id === sessionData.session_id &&
            this.currentSession.last_user_interaction) {
            sessionData.completed_at = this.currentSession.last_user_interaction;
            console.log('📊 使用用戶最後互動時間作為完成時間:', sessionData.completed_at);
        } else if (!sessionData.completed_at) {
            sessionData.completed_at = TimeUtils.getCurrentTimestamp();
            console.log('📊 使用當前時間作為完成時間:', sessionData.completed_at);
        }

        // 計算持續時間
        if (sessionData.created_at && !sessionData.duration) {
            sessionData.duration = sessionData.completed_at - sessionData.created_at;
        }

        // 確保包含用戶訊息（如果當前會話有的話）
        if (this.currentSession &&
            this.currentSession.session_id === sessionData.session_id &&
            this.currentSession.user_messages) {
            sessionData.user_messages = this.currentSession.user_messages;
            console.log('📊 會話完成時包含', sessionData.user_messages.length, '條用戶訊息');
        }

        // 將完成的會話加入歷史記錄
        this.addSessionToHistory(sessionData);

        // 如果是當前會話完成，保持引用但標記為完成
        if (this.currentSession && this.currentSession.session_id === sessionData.session_id) {
            this.currentSession = Object.assign(this.currentSession, sessionData);
            if (this.onSessionChange) {
                this.onSessionChange(this.currentSession);
            }
        }
    };

    /**
     * 新增會話到歷史記錄
     */
    SessionDataManager.prototype.addSessionToHistory = function(sessionData) {
        console.log('📊 新增會話到歷史記錄:', sessionData);

        // 只有已完成的會話才加入歷史記錄
        if (!StatusUtils.isCompletedStatus(sessionData.status)) {
            console.log('📊 跳過未完成的會話:', sessionData.session_id);
            return false;
        }

        // 新增儲存時間戳記
        sessionData.saved_at = TimeUtils.getCurrentTimestamp();

        // 確保 user_messages 陣列存在（向後相容）
        if (!sessionData.user_messages) {
            sessionData.user_messages = [];
        }

        // 避免重複新增
        const existingIndex = this.sessionHistory.findIndex(s => s.session_id === sessionData.session_id);
        if (existingIndex !== -1) {
            // 合併用戶訊息記錄
            const existingSession = this.sessionHistory[existingIndex];
            if (existingSession.user_messages && sessionData.user_messages) {
                sessionData.user_messages = this.mergeUserMessages(existingSession.user_messages, sessionData.user_messages);
            }
            this.sessionHistory[existingIndex] = sessionData;
        } else {
            this.sessionHistory.unshift(sessionData);
        }

        // 限制歷史記錄數量
        if (this.sessionHistory.length > 10) {
            this.sessionHistory = this.sessionHistory.slice(0, 10);
        }

        // 保存到伺服器端
        this.saveToServer();

        this.updateStats();

        // 觸發回調
        if (this.onHistoryChange) {
            this.onHistoryChange(this.sessionHistory);
        }

        return true;
    };

    /**
     * 合併用戶訊息記錄
     */
    SessionDataManager.prototype.mergeUserMessages = function(existingMessages, newMessages) {
        const merged = existingMessages.slice(); // 複製現有訊息

        // 新增不重複的訊息（基於時間戳記去重）
        newMessages.forEach(function(newMsg) {
            const exists = merged.some(function(existingMsg) {
                return existingMsg.timestamp === newMsg.timestamp;
            });
            if (!exists) {
                merged.push(newMsg);
            }
        });

        // 按時間戳記排序
        merged.sort(function(a, b) {
            return a.timestamp - b.timestamp;
        });

        return merged;
    };

    /**
     * 新增用戶訊息到當前會話
     */
    SessionDataManager.prototype.addUserMessage = function(messageData) {
        console.log('📊 新增用戶訊息:', messageData);

        // 檢查隱私設定
        if (!this.isUserMessageRecordingEnabled()) {
            console.log('📊 用戶訊息記錄已停用，跳過記錄');
            return false;
        }

        // 檢查是否有當前會話
        if (!this.currentSession || !this.currentSession.session_id) {
            console.warn('📊 沒有當前會話，無法記錄用戶訊息');
            return false;
        }

        // 確保當前會話有 user_messages 陣列
        if (!this.currentSession.user_messages) {
            this.currentSession.user_messages = [];
        }

        // 建立用戶訊息記錄
        const userMessage = this.createUserMessageRecord(messageData);

        // 新增到當前會話
        this.currentSession.user_messages.push(userMessage);

        // 記錄用戶最後互動時間
        this.currentSession.last_user_interaction = TimeUtils.getCurrentTimestamp();

        // 發送用戶消息到服務器端
        this.sendUserMessageToServer(userMessage);

        // 立即保存當前會話到伺服器
        this.saveCurrentSessionToServer();

        console.log('📊 用戶訊息已記錄到當前會話:', this.currentSession.session_id);
        return true;
    };

    /**
     * 發送用戶消息到服務器端
     */
    SessionDataManager.prototype.sendUserMessageToServer = function(userMessage) {
        const lang = window.i18nManager ? window.i18nManager.getCurrentLanguage() : 'zh-TW';
        fetch('/api/add-user-message?lang=' + lang, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userMessage)
        })
        .then(function(response) {
            if (response.ok) {
                console.log('📊 用戶消息已發送到服務器端');
            } else {
                console.warn('📊 發送用戶消息到服務器端失敗:', response.status);
            }
        })
        .catch(function(error) {
            console.warn('📊 發送用戶消息到服務器端出錯:', error);
        });
    };

    /**
     * 建立用戶訊息記錄
     */
    SessionDataManager.prototype.createUserMessageRecord = function(messageData) {
        const timestamp = TimeUtils.getCurrentTimestamp();
        const privacyLevel = this.getUserMessagePrivacyLevel();

        const record = {
            timestamp: timestamp,
            submission_method: messageData.submission_method || 'manual',
            type: 'feedback'
        };

        // 根據隱私等級決定記錄內容
        if (privacyLevel === 'full') {
            record.content = messageData.content || '';
            record.images = this.processImageDataForRecord(messageData.images || []);
        } else if (privacyLevel === 'basic') {
            record.content_length = (messageData.content || '').length;
            record.image_count = (messageData.images || []).length;
            record.has_content = !!(messageData.content && messageData.content.trim());
        } else if (privacyLevel === 'disabled') {
            // 停用記錄時，只記錄最基本的時間戳記和提交方式
            record.privacy_note = 'Content recording disabled by user privacy settings';
        }

        return record;
    };

    /**
     * 處理圖片資料用於記錄
     */
    SessionDataManager.prototype.processImageDataForRecord = function(images) {
        if (!Array.isArray(images)) {
            return [];
        }

        return images.map(function(img) {
            return {
                name: img.name || 'unknown',
                size: img.size || 0,
                type: img.type || 'unknown'
            };
        });
    };

    /**
     * 檢查是否啟用用戶訊息記錄
     */
    SessionDataManager.prototype.isUserMessageRecordingEnabled = function() {
        if (!this.settingsManager) {
            return true; // 預設啟用
        }

        // 檢查總開關
        const recordingEnabled = this.settingsManager.get('userMessageRecordingEnabled', true);
        if (!recordingEnabled) {
            return false;
        }

        // 檢查隱私等級（disabled 等級視為停用記錄）
        const privacyLevel = this.settingsManager.get('userMessagePrivacyLevel', 'full');
        return privacyLevel !== 'disabled';
    };

    /**
     * 獲取用戶訊息隱私等級
     */
    SessionDataManager.prototype.getUserMessagePrivacyLevel = function() {
        if (!this.settingsManager) {
            return 'full'; // 預設完整記錄
        }
        return this.settingsManager.get('userMessagePrivacyLevel', 'full');
    };

    /**
     * 清空所有會話的用戶訊息記錄
     */
    SessionDataManager.prototype.clearAllUserMessages = function() {
        console.log('📊 清空所有會話的用戶訊息記錄...');

        // 清空當前會話的用戶訊息
        if (this.currentSession && this.currentSession.user_messages) {
            this.currentSession.user_messages = [];
        }

        // 清空歷史會話的用戶訊息
        this.sessionHistory.forEach(function(session) {
            if (session.user_messages) {
                session.user_messages = [];
            }
        });

        // 保存到伺服器端
        this.saveToServer();

        console.log('📊 所有用戶訊息記錄已清空');
        return true;
    };

    /**
     * 清空指定會話的用戶訊息記錄
     */
    SessionDataManager.prototype.clearSessionUserMessages = function(sessionId) {
        console.log('📊 清空會話用戶訊息記錄:', sessionId);

        // 查找並清空指定會話的用戶訊息
        const session = this.sessionHistory.find(function(s) {
            return s.session_id === sessionId;
        });

        if (session && session.user_messages) {
            session.user_messages = [];
            this.saveToServer();
            console.log('📊 會話用戶訊息記錄已清空:', sessionId);
            return true;
        }

        console.warn('📊 找不到指定會話或該會話沒有用戶訊息記錄:', sessionId);
        return false;
    };

    /**
     * 獲取當前會話
     */
    SessionDataManager.prototype.getCurrentSession = function() {
        return this.currentSession;
    };

    /**
     * 獲取會話歷史
     */
    SessionDataManager.prototype.getSessionHistory = function() {
        return this.sessionHistory.slice(); // 返回副本
    };

    /**
     * 根據 ID 查找會話（包含完整的用戶消息數據）
     */
    SessionDataManager.prototype.findSessionById = function(sessionId) {
        // 先檢查當前會話
        if (this.currentSession && this.currentSession.session_id === sessionId) {
            console.log('📊 從當前會話獲取數據:', sessionId, '用戶消息數量:', this.currentSession.user_messages ? this.currentSession.user_messages.length : 0);
            return this.currentSession;
        }

        // 再檢查歷史記錄
        const historySession = this.sessionHistory.find(s => s.session_id === sessionId);
        if (historySession) {
            console.log('📊 從歷史記錄獲取數據:', sessionId, '用戶消息數量:', historySession.user_messages ? historySession.user_messages.length : 0);
            return historySession;
        }

        console.warn('📊 找不到會話:', sessionId);
        return null;
    };

    /**
     * 更新統計資訊
     */
    SessionDataManager.prototype.updateStats = function() {
        // 計算今日會話數
        const todayStart = TimeUtils.getTodayStartTimestamp();
        const todaySessions = this.sessionHistory.filter(function(session) {
            return session.created_at && session.created_at >= todayStart;
        });
        this.sessionStats.todayCount = todaySessions.length;

        // 計算今日平均持續時間
        const todayCompletedSessions = todaySessions.filter(function(s) {
            // 過濾有效的持續時間：大於 0 且小於 24 小時（86400 秒）
            return s.duration && s.duration > 0 && s.duration < 86400;
        });

        if (todayCompletedSessions.length > 0) {
            const totalDuration = todayCompletedSessions.reduce(function(sum, s) {
                // 確保持續時間是合理的數值
                const duration = Math.min(s.duration, 86400); // 最大 24 小時
                return sum + duration;
            }, 0);
            this.sessionStats.averageDuration = Math.round(totalDuration / todayCompletedSessions.length);
        } else {
            this.sessionStats.averageDuration = 0;
        }

        // 觸發回調
        if (this.onStatsChange) {
            this.onStatsChange(this.sessionStats);
        }
    };

    /**
     * 獲取統計資訊
     */
    SessionDataManager.prototype.getStats = function() {
        return Object.assign({}, this.sessionStats);
    };

    /**
     * 清空會話數據
     */
    SessionDataManager.prototype.clearCurrentSession = function() {
        this.currentSession = null;
        if (this.onSessionChange) {
            this.onSessionChange(null);
        }
    };

    /**
     * 清空歷史記錄
     */
    SessionDataManager.prototype.clearHistory = function() {
        this.sessionHistory = [];

        // 清空伺服器端資料
        this.clearServerData();

        this.updateStats();
        if (this.onHistoryChange) {
            this.onHistoryChange(this.sessionHistory);
        }
    };

    /**
     * 獲取專案目錄（輔助方法）
     */
    SessionDataManager.prototype.getProjectDirectory = function() {
        // 嘗試從多個來源獲取專案目錄
        const sources = [
            () => document.querySelector('.session-project')?.textContent?.replace('專案: ', ''),
            () => document.querySelector('.project-info')?.textContent?.replace('專案目錄: ', ''),
            () => this.currentSession?.project_directory
        ];

        for (const source of sources) {
            try {
                const result = source();
                if (result && result !== '未知') {
                    return result;
                }
            } catch (error) {
                // 忽略錯誤，繼續嘗試下一個來源
            }
        }

        return '未知';
    };

    /**
     * 獲取 AI 摘要（輔助方法）
     */
    SessionDataManager.prototype.getAISummary = function() {
        // 嘗試從多個來源獲取 AI 摘要
        const sources = [
            () => {
                const element = document.querySelector('.session-summary');
                const text = element?.textContent;
                return text && text !== 'AI 摘要: 載入中...' ? text.replace('AI 摘要: ', '') : null;
            },
            () => {
                const element = document.querySelector('#combinedSummaryContent');
                return element?.textContent?.trim();
            },
            () => this.currentSession?.summary
        ];

        for (const source of sources) {
            try {
                const result = source();
                if (result && result !== '暫無摘要') {
                    return result;
                }
            } catch (error) {
                // 忽略錯誤，繼續嘗試下一個來源
            }
        }

        return '暫無摘要';
    };

    /**
     * 從伺服器載入會話歷史（包含實時狀態）
     */
    SessionDataManager.prototype.loadFromServer = function() {
        const self = this;
        const lang = window.i18nManager ? window.i18nManager.getCurrentLanguage() : 'zh-TW';

        Promise.allSettled([
            self.fetchRealtimeSessions(lang),
            self.fetchHistorySessions(lang)
        ]).then(function(results) {
            const realtimeResult = results[0];
            const historyResult = results[1];

            const realtimeSessions = realtimeResult.status === 'fulfilled' ? realtimeResult.value : [];
            const historySessions = historyResult.status === 'fulfilled' ? historyResult.value : [];

            if (realtimeResult.status === 'rejected') {
                console.warn('📊 獲取實時會話狀態失敗:', realtimeResult.reason);
            }
            if (historyResult.status === 'rejected') {
                console.warn('📊 載入歷史文件失敗:', historyResult.reason);
            }

            self.sessionHistory = self.mergeSessionsById(historySessions, realtimeSessions);
            console.log('📊 初始化會話資料完成：歷史', historySessions.length, '個，實時', realtimeSessions.length, '個，合併後', self.sessionHistory.length, '個');

            self.cleanupExpiredSessions();
            self.updateStats();

            if (self.onHistoryChange) {
                self.onHistoryChange(self.sessionHistory);
            }

            if (self.onDataChanged) {
                self.onDataChanged();
            }
        });
    };

    /**
     * 從歷史文件載入會話數據（備用方案）
     */
    SessionDataManager.prototype.loadFromHistoryFile = function() {
        const self = this;

        const lang = window.i18nManager ? window.i18nManager.getCurrentLanguage() : 'zh-TW';
        fetch('/api/load-session-history?lang=' + lang)
            .then(function(response) {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('伺服器回應錯誤: ' + response.status);
                }
            })
            .then(function(data) {
                if (data && Array.isArray(data.sessions)) {
                    self.sessionHistory = data.sessions;
                    console.log('📊 從歷史文件載入', self.sessionHistory.length, '個會話');

                    // 載入完成後進行清理和統計更新
                    self.cleanupExpiredSessions();
                    self.updateStats();

                    // 觸發歷史記錄變更回調
                    if (self.onHistoryChange) {
                        self.onHistoryChange(self.sessionHistory);
                    }

                    // 觸發資料變更回調
                    if (self.onDataChanged) {
                        self.onDataChanged();
                    }
                } else {
                    console.warn('📊 歷史文件回應格式錯誤:', data);
                    self.sessionHistory = [];
                    self.updateStats();

                    if (self.onHistoryChange) {
                        self.onHistoryChange(self.sessionHistory);
                    }

                    if (self.onDataChanged) {
                        self.onDataChanged();
                    }
                }
            })
            .catch(function(error) {
                console.warn('📊 從歷史文件載入失敗:', error);
                self.sessionHistory = [];
                self.updateStats();

                if (self.onHistoryChange) {
                    self.onHistoryChange(self.sessionHistory);
                }

                if (self.onDataChanged) {
                    self.onDataChanged();
                }
            });
    };

    /**
     * 立即保存當前會話到伺服器
     */
    SessionDataManager.prototype.saveCurrentSessionToServer = function() {
        if (!this.currentSession) {
            console.log('📊 沒有當前會話，跳過即時保存');
            return;
        }

        console.log('📊 立即保存當前會話到伺服器:', this.currentSession.session_id);

        // 建立當前會話的快照（包含用戶訊息）
        const sessionSnapshot = Object.assign({}, this.currentSession);

        // 確保快照包含在歷史記錄中（用於即時保存）
        const updatedHistory = this.sessionHistory.slice();
        const existingIndex = updatedHistory.findIndex(s => s.session_id === sessionSnapshot.session_id);

        if (existingIndex !== -1) {
            // 更新現有會話，保留用戶訊息
            const existingSession = updatedHistory[existingIndex];
            if (existingSession.user_messages && sessionSnapshot.user_messages) {
                sessionSnapshot.user_messages = this.mergeUserMessages(existingSession.user_messages, sessionSnapshot.user_messages);
            }
            updatedHistory[existingIndex] = sessionSnapshot;
        } else {
            // 新增會話快照到歷史記錄開頭
            updatedHistory.unshift(sessionSnapshot);
        }

        // 保存包含當前會話的歷史記錄
        this.saveSessionSnapshot(updatedHistory);
    };

    /**
     * 保存會話快照到伺服器
     */
    SessionDataManager.prototype.saveSessionSnapshot = function(sessions) {
        const data = {
            sessions: sessions,
            lastCleanup: TimeUtils.getCurrentTimestamp()
        };

        const lang = window.i18nManager ? window.i18nManager.getCurrentLanguage() : 'zh-TW';
        fetch('/api/save-session-history?lang=' + lang, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(function(response) {
            if (response.ok) {
                console.log('📊 已保存會話快照到伺服器，包含', data.sessions.length, '個會話');
                return response.json();
            } else {
                throw new Error('伺服器回應錯誤: ' + response.status);
            }
        })
        .then(function(result) {
            if (result.messageCode && window.i18nManager) {
                const message = window.i18nManager.t(result.messageCode, result.params);
                console.log('📊 會話快照保存回應:', message);
            } else {
                console.log('📊 會話快照保存回應:', result.message);
            }
        })
        .catch(function(error) {
            console.error('📊 保存會話快照到伺服器失敗:', error);
        });
    };

    /**
     * 保存會話歷史到伺服器
     */
    SessionDataManager.prototype.saveToServer = function() {
        const data = {
            sessions: this.sessionHistory,
            lastCleanup: TimeUtils.getCurrentTimestamp()
        };

        const lang = window.i18nManager ? window.i18nManager.getCurrentLanguage() : 'zh-TW';
        fetch('/api/save-session-history?lang=' + lang, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(function(response) {
            if (response.ok) {
                console.log('📊 已保存', data.sessions.length, '個會話到伺服器');
                return response.json();
            } else {
                throw new Error('伺服器回應錯誤: ' + response.status);
            }
        })
        .then(function(result) {
            if (result.messageCode && window.i18nManager) {
                const message = window.i18nManager.t(result.messageCode, result.params);
                console.log('📊 伺服器保存回應:', message);
            } else {
                console.log('📊 伺服器保存回應:', result.message);
            }
        })
        .catch(function(error) {
            console.error('📊 保存會話歷史到伺服器失敗:', error);
        });
    };

    /**
     * 清空伺服器端的會話歷史
     */
    SessionDataManager.prototype.clearServerData = function() {
        const emptyData = {
            sessions: [],
            lastCleanup: TimeUtils.getCurrentTimestamp()
        };

        fetch('/api/save-session-history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(emptyData)
        })
        .then(function(response) {
            if (response.ok) {
                console.log('📊 已清空伺服器端的會話歷史');
            } else {
                throw new Error('伺服器回應錯誤: ' + response.status);
            }
        })
        .catch(function(error) {
            console.error('📊 清空伺服器端會話歷史失敗:', error);
        });
    };



    /**
     * 清理過期的會話
     */
    SessionDataManager.prototype.cleanupExpiredSessions = function() {
        if (!this.settingsManager) {
            return;
        }

        const retentionHours = this.settingsManager.get('sessionHistoryRetentionHours', 72);
        const retentionMs = retentionHours * 60 * 60 * 1000;
        const now = TimeUtils.getCurrentTimestamp();

        const originalCount = this.sessionHistory.length;
        this.sessionHistory = this.sessionHistory.filter(function(session) {
            const sessionAge = now - (session.saved_at || session.completed_at || session.created_at || 0);
            return sessionAge < retentionMs;
        });

        const cleanedCount = originalCount - this.sessionHistory.length;
        if (cleanedCount > 0) {
            console.log('📊 清理了', cleanedCount, '個過期會話');
            this.saveToServer();
        }
    };

    /**
     * 檢查會話是否過期
     */
    SessionDataManager.prototype.isSessionExpired = function(session) {
        if (!this.settingsManager) {
            return false;
        }

        const retentionHours = this.settingsManager.get('sessionHistoryRetentionHours', 72);
        const retentionMs = retentionHours * 60 * 60 * 1000;
        const now = TimeUtils.getCurrentTimestamp();
        const sessionTime = session.saved_at || session.completed_at || session.created_at || 0;

        return (now - sessionTime) > retentionMs;
    };

    /**
     * 匯出會話歷史
     */
    SessionDataManager.prototype.exportSessionHistory = function() {
        const self = this;
        const exportData = {
            exportedAt: new Date().toISOString(),
            sessionCount: this.sessionHistory.length,
            sessions: this.sessionHistory.map(function(session) {
                const sessionData = {
                    session_id: session.session_id,
                    created_at: session.created_at,
                    completed_at: session.completed_at,
                    duration: session.duration,
                    status: session.status,
                    project_directory: session.project_directory,
                    ai_summary: session.summary || session.ai_summary,
                    saved_at: session.saved_at
                };

                // 包含用戶訊息記錄（如果存在且允許匯出）
                if (session.user_messages && self.isUserMessageRecordingEnabled()) {
                    sessionData.user_messages = session.user_messages;
                    sessionData.user_message_count = session.user_messages.length;
                }

                return sessionData;
            })
        };

        const filename = 'session-history-' + new Date().toISOString().split('T')[0] + '.json';
        this.downloadJSON(exportData, filename);

        console.log('📊 匯出了', this.sessionHistory.length, '個會話');
        return filename;
    };

    /**
     * 匯出單一會話
     */
    SessionDataManager.prototype.exportSingleSession = function(sessionId) {
        const session = this.sessionHistory.find(function(s) {
            return s.session_id === sessionId;
        });

        if (!session) {
            console.error('📊 找不到會話:', sessionId);
            return null;
        }

        const sessionData = {
            session_id: session.session_id,
            created_at: session.created_at,
            completed_at: session.completed_at,
            duration: session.duration,
            status: session.status,
            project_directory: session.project_directory,
            ai_summary: session.summary || session.ai_summary,
            saved_at: session.saved_at
        };

        // 包含用戶訊息記錄（如果存在且允許匯出）
        if (session.user_messages && this.isUserMessageRecordingEnabled()) {
            sessionData.user_messages = session.user_messages;
            sessionData.user_message_count = session.user_messages.length;
        }

        const exportData = {
            exportedAt: new Date().toISOString(),
            session: sessionData
        };

        const shortId = sessionId.substring(0, 8);
        const filename = 'session-' + shortId + '-' + new Date().toISOString().split('T')[0] + '.json';
        this.downloadJSON(exportData, filename);

        console.log('📊 匯出會話:', sessionId);
        return filename;
    };

    /**
     * 下載 JSON 檔案
     */
    SessionDataManager.prototype.downloadJSON = function(data, filename) {
        try {
            const jsonString = JSON.stringify(data, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('📊 下載檔案失敗:', error);
        }
    };

    /**
     * 清理資源
     */
    SessionDataManager.prototype.cleanup = function() {
        this.currentSession = null;
        this.sessionHistory = [];
        this.lastStatusUpdate = null;
        this.sessionStats = {
            todayCount: 0,
            averageDuration: 0
        };

        console.log('📊 SessionDataManager 清理完成');
    };

    // 將 SessionDataManager 加入命名空間
    window.MCPFeedback.Session.DataManager = SessionDataManager;

    console.log('✅ SessionDataManager 模組載入完成');

})();
