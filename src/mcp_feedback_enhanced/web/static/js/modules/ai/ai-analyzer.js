/**
 * MCP Feedback Enhanced - AI 分析模块
 * ===================================
 *
 * 提供 AI 驱动的代码分析功能，集成到自动提交工作流中。
 */

(function() {
    'use strict';

    // 确保命名空间存在
    window.MCPFeedback = window.MCPFeedback || {};
    window.MCPFeedback.AI = window.MCPFeedback.AI || {};

    // 创建模块专用日志器
    const logger = window.MCPFeedback.Logger ?
        new window.MCPFeedback.Logger({ moduleName: 'AIAnalyzer' }) :
        console;

    /**
     * AI 分析器类
     */
    function AIAnalyzer(options) {
        options = options || {};

        // 配置
        this.apiEndpoint = options.apiEndpoint || '/api/ai/analyze-code';
        this.statusEndpoint = options.statusEndpoint || '/api/ai/status';

        // 状态
        this.isAnalyzing = false;
        this.lastAnalysis = null;

        // 回调
        this.onAnalysisStart = options.onAnalysisStart || null;
        this.onAnalysisComplete = options.onAnalysisComplete || null;
        this.onAnalysisError = options.onAnalysisError || null;

        logger.info('AIAnalyzer 初始化完成');
    }

    /**
     * 检查 AI 功能是否可用
     */
    AIAnalyzer.prototype.checkStatus = function() {
        const self = this;

        return fetch(this.statusEndpoint)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Failed to check AI status');
                }
                return response.json();
            })
            .then(function(data) {
                logger.info('AI 状态:', data);
                return data;
            })
            .catch(function(error) {
                logger.error('检查 AI 状态失败:', error);
                return {
                    enabled: false,
                    status: 'error',
                    error: error.message
                };
            });
    };

    /**
     * 分析代码变更
     */
    AIAnalyzer.prototype.analyzeCode = function(projectDir, context) {
        const self = this;

        if (this.isAnalyzing) {
            logger.warn('AI 分析正在进行中，请稍候');
            return Promise.reject(new Error('分析正在进行中'));
        }

        this.isAnalyzing = true;

        // 触发开始回调
        if (this.onAnalysisStart) {
            this.onAnalysisStart();
        }

        logger.info('开始 AI 代码分析...', { projectDir, context });

        return fetch(this.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_dir: projectDir,
                context: context || ''
            })
        })
        .then(function(response) {
            if (!response.ok) {
                throw new Error('AI 分析请求失败: ' + response.status);
            }
            return response.json();
        })
        .then(function(data) {
            self.isAnalyzing = false;

            if (!data.success) {
                throw new Error(data.error || '分析失败');
            }

            // 保存分析结果
            self.lastAnalysis = data.analysis;

            logger.info('AI 分析完成:', data.analysis);

            // 触发完成回调
            if (self.onAnalysisComplete) {
                self.onAnalysisComplete(data.analysis);
            }

            return data.analysis;
        })
        .catch(function(error) {
            self.isAnalyzing = false;

            logger.error('AI 分析失败:', error);

            // 触发错误回调
            if (self.onAnalysisError) {
                self.onAnalysisError(error);
            }

            throw error;
        });
    };

    /**
     * 获取上次分析结果
     */
    AIAnalyzer.prototype.getLastAnalysis = function() {
        return this.lastAnalysis;
    };

    /**
     * 清除分析结果
     */
    AIAnalyzer.prototype.clearAnalysis = function() {
        this.lastAnalysis = null;
    };

    /**
     * 格式化分析结果为 HTML
     */
    AIAnalyzer.prototype.formatAnalysisHTML = function(analysis) {
        if (!analysis) {
            return '<p>暂无分析结果</p>';
        }

        const severityBadge = this._getSeverityBadge(analysis.severity);
        const riskBadge = this._getRiskBadge(analysis.risk_level);

        let html = '<div class="ai-analysis-result">';

        // 标题和标签
        html += '<div class="ai-analysis-header">';
        html += '<h3>🤖 AI 代码分析报告</h3>';
        html += '<div class="ai-badges">';
        html += '<span class="badge badge-type">' + analysis.change_type + '</span>';
        html += severityBadge;
        html += riskBadge;
        if (analysis.breaking_changes) {
            html += '<span class="badge badge-breaking">⚠️ 破坏性变更</span>';
        }
        html += '</div>';
        html += '</div>';

        // 摘要
        html += '<div class="ai-section">';
        html += '<h4>📋 变更摘要</h4>';
        html += '<p>' + this._escapeHtml(analysis.summary) + '</p>';
        html += '</div>';

        // Commit Message 建议
        html += '<div class="ai-section ai-commit-suggestion">';
        html += '<h4>💬 Commit Message 建议</h4>';
        html += '<div class="commit-title">';
        html += '<strong>标题:</strong> <code>' + this._escapeHtml(analysis.commit_title) + '</code>';
        html += '<button class="btn-copy-commit" data-text="' + this._escapeHtml(analysis.commit_title) + '">📋 复制</button>';
        html += '</div>';
        if (analysis.commit_body) {
            html += '<div class="commit-body">';
            html += '<strong>正文:</strong><br>';
            html += '<pre>' + this._escapeHtml(analysis.commit_body) + '</pre>';
            html += '</div>';
        }
        html += '</div>';

        // 问题和建议
        if (analysis.issues_found && analysis.issues_found.length > 0) {
            html += '<div class="ai-section ai-issues">';
            html += '<h4>⚠️ 发现的问题</h4>';
            html += '<ul>';
            analysis.issues_found.forEach(function(issue) {
                html += '<li>' + self._escapeHtml(issue) + '</li>';
            });
            html += '</ul>';
            html += '</div>';
        }

        if (analysis.suggestions && analysis.suggestions.length > 0) {
            html += '<div class="ai-section ai-suggestions">';
            html += '<h4>💡 优化建议</h4>';
            html += '<ul>';
            analysis.suggestions.forEach(function(suggestion) {
                html += '<li>' + self._escapeHtml(suggestion) + '</li>';
            });
            html += '</ul>';
            html += '</div>';
        }

        // 置信度
        html += '<div class="ai-footer">';
        html += '<span class="ai-confidence">置信度: ' + (analysis.confidence_score * 100).toFixed(0) + '%</span>';
        html += '</div>';

        html += '</div>';

        return html;
    };

    /**
     * 获取严重性徽章
     */
    AIAnalyzer.prototype._getSeverityBadge = function(severity) {
        const badges = {
            'high': '<span class="badge badge-severity-high">🔴 高</span>',
            'medium': '<span class="badge badge-severity-medium">🟡 中</span>',
            'low': '<span class="badge badge-severity-low">🟢 低</span>'
        };
        return badges[severity] || badges['low'];
    };

    /**
     * 获取风险徽章
     */
    AIAnalyzer.prototype._getRiskBadge = function(risk) {
        const badges = {
            'high': '<span class="badge badge-risk-high">⚠️ 高风险</span>',
            'medium': '<span class="badge badge-risk-medium">⚡ 中风险</span>',
            'low': '<span class="badge badge-risk-low">✅ 低风险</span>'
        };
        return badges[risk] || badges['low'];
    };

    /**
     * HTML 转义
     */
    AIAnalyzer.prototype._escapeHtml = function(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    // 导出到全局命名空间
    window.MCPFeedback.AI.AIAnalyzer = AIAnalyzer;

    logger.info('✅ AI Analyzer 模块加载完成');

})();
