#!/usr/bin/env python3
"""
AI 集成完整示例
===============

演示如何在 MCP Feedback Enhanced 中使用 AI 分析功能。
"""

import asyncio
import os
import sys

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.mcp_feedback_enhanced.ai import AIAnalyzer, AIProvider


async def example_basic_analysis():
    """示例 1: 基础代码分析"""
    print("=" * 60)
    print("示例 1: 基础代码分析 (使用 Ollama)")
    print("=" * 60)

    # 模拟 Git Diff
    git_diff = """diff --git a/app.py b/app.py
index 1234567..abcdefg 100644
--- a/app.py
+++ b/app.py
@@ -15,8 +15,12 @@ def process_user_input(user_data):
     # 处理用户输入
-    result = eval(user_data)  # 危险! 不要使用 eval
-    return result
+    try:
+        # 使用 json.loads 替代 eval
+        result = json.loads(user_data)
+        return result
+    except json.JSONDecodeError:
+        return {"error": "Invalid JSON"}
"""

    git_status = """On branch main
Changes to be committed:
  modified:   app.py
"""

    # 创建分析器 (使用 Ollama)
    analyzer = AIAnalyzer(provider=AIProvider.OLLAMA)

    # 执行分析
    print("\n🤖 正在分析代码变更...")
    result = await analyzer.analyze_git_diff(
        git_diff=git_diff,
        git_status=git_status,
        project_context="这是一个 Python Flask Web 应用",
    )

    # 打印结果
    print("\n📊 分析结果:")
    print(f"  变更类型: {result.change_type.value}")
    print(f"  严重性: {result.severity.value}")
    print(f"  风险等级: {result.risk_level}")
    print(f"  破坏性变更: {'是' if result.breaking_changes else '否'}")
    print(f"\n📋 摘要:\n  {result.summary}")
    print(f"\n💬 建议的 Commit Message:")
    print(f"  标题: {result.commit_title}")
    print(f"  正文:\n{result.commit_body}")

    if result.issues_found:
        print(f"\n⚠️ 发现的问题:")
        for i, issue in enumerate(result.issues_found, 1):
            print(f"  {i}. {issue}")

    if result.suggestions:
        print(f"\n💡 优化建议:")
        for i, suggestion in enumerate(result.suggestions, 1):
            print(f"  {i}. {suggestion}")

    print(f"\n🎯 AI 置信度: {result.confidence_score:.1%}")


async def example_openai_analysis():
    """示例 2: 使用 OpenAI 进行分析"""
    print("\n\n")
    print("=" * 60)
    print("示例 2: 使用 OpenAI GPT-4 分析")
    print("=" * 60)

    # 检查 API 密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️ 未设置 OPENAI_API_KEY 环境变量，跳过此示例")
        return

    git_diff = """diff --git a/database.py b/database.py
index abc123..def456 100644
--- a/database.py
+++ b/database.py
@@ -10,7 +10,10 @@ class Database:
     def query(self, sql):
-        cursor = self.conn.cursor()
-        cursor.execute(sql)  # SQL 注入风险!
-        return cursor.fetchall()
+        # 使用参数化查询防止 SQL 注入
+        cursor = self.conn.cursor()
+        # 添加输入验证
+        if not self._is_safe_query(sql):
+            raise ValueError("Unsafe query detected")
+        cursor.execute(sql)
+        return cursor.fetchall()
"""

    # 创建 OpenAI 分析器
    analyzer = AIAnalyzer(provider=AIProvider.OPENAI, model="gpt-4-turbo-preview")

    print("\n🤖 正在使用 GPT-4 分析代码...")
    result = await analyzer.analyze_git_diff(
        git_diff=git_diff,
        git_status="modified: database.py",
        project_context="Python 数据库访问层，需要高安全性",
    )

    print(f"\n📊 GPT-4 分析结果:")
    print(f"  变更类型: {result.change_type.value}")
    print(f"  安全风险: {result.risk_level}")
    print(f"  Commit: {result.commit_title}")


async def example_batch_analysis():
    """示例 3: 批量分析多个文件"""
    print("\n\n")
    print("=" * 60)
    print("示例 3: 批量分析多个文件变更")
    print("=" * 60)

    # 模拟多个文件的变更
    changes = [
        {
            "file": "frontend/app.js",
            "diff": """diff --git a/frontend/app.js
+++ b/frontend/app.js
@@ -5,3 +5,4 @@
-const API_URL = "http://api.example.com"
+const API_URL = process.env.REACT_APP_API_URL || "http://localhost:3000"
""",
        },
        {
            "file": "backend/auth.py",
            "diff": """diff --git a/backend/auth.py
+++ b/backend/auth.py
@@ -10,5 +10,8 @@
-def hash_password(password):
-    return hashlib.md5(password.encode()).hexdigest()
+def hash_password(password):
+    # 使用更安全的 bcrypt
+    import bcrypt
+    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
""",
        },
    ]

    analyzer = AIAnalyzer(provider=AIProvider.OLLAMA)

    print("\n🤖 开始批量分析...")

    # 并发分析多个文件
    tasks = []
    for change in changes:
        task = analyzer.analyze_git_diff(
            git_diff=change["diff"],
            git_status=f"modified: {change['file']}",
            project_context=f"分析文件: {change['file']}",
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    # 汇总结果
    print("\n📊 批量分析结果汇总:")
    for i, (change, result) in enumerate(zip(changes, results), 1):
        print(f"\n  {i}. {change['file']}")
        print(f"     类型: {result.change_type.value}")
        print(f"     风险: {result.risk_level}")
        print(f"     摘要: {result.summary}")


async def example_custom_prompt():
    """示例 4: 自定义分析提示词"""
    print("\n\n")
    print("=" * 60)
    print("示例 4: 自定义分析维度")
    print("=" * 60)

    # 创建自定义分析器类
    class SecurityFocusedAnalyzer(AIAnalyzer):
        """专注于安全性的 AI 分析器"""

        def _build_analysis_prompt(self, git_diff, git_status, project_context):
            """自定义提示词 - 强调安全性分析"""
            return f"""你是一个网络安全专家和代码审查员。

项目上下文: {project_context}

Git Diff:
```diff
{git_diff[:3000]}
```

请从安全角度深度分析这次代码变更，关注:
1. **安全漏洞**: SQL 注入、XSS、CSRF、命令注入等
2. **敏感信息**: API 密钥、密码、token 泄露
3. **访问控制**: 权限检查、认证绕过
4. **加密问题**: 弱加密算法、明文存储
5. **依赖安全**: 第三方库的已知漏洞

以 JSON 格式返回:
{{
  "change_type": "fix|feat|refactor|...",
  "severity": "high|medium|low",
  "summary": "安全角度的变更摘要",
  "commit_title": "提交标题",
  "commit_body": "详细说明",
  "issues_found": ["安全问题1", "安全问题2"],
  "suggestions": ["安全建议1", "安全建议2"],
  "affected_files": ["文件列表"],
  "risk_level": "high|medium|low",
  "breaking_changes": false,
  "confidence_score": 0.95
}}
"""

    analyzer = SecurityFocusedAnalyzer(provider=AIProvider.OLLAMA)

    git_diff = """diff --git a/login.py
+++ b/login.py
@@ -5,3 +5,5 @@
-password = request.form['password']
-if password == "admin123":
+password = request.form['password']
+hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
+if bcrypt.checkpw(password.encode(), stored_hash):
"""

    print("\n🔒 使用安全专注分析器...")
    result = await analyzer.analyze_git_diff(
        git_diff=git_diff,
        git_status="modified: login.py",
        project_context="用户认证系统",
    )

    print(f"\n🔍 安全分析结果:")
    print(f"  风险等级: {result.risk_level}")
    print(f"  发现问题: {len(result.issues_found)} 个")
    for issue in result.issues_found:
        print(f"    - {issue}")


async def main():
    """运行所有示例"""
    print("\n🚀 MCP Feedback Enhanced - AI 集成示例")
    print("=" * 60)

    try:
        # 示例 1: 基础分析 (Ollama)
        await example_basic_analysis()

        # 示例 2: OpenAI 分析 (需要 API 密钥)
        await example_openai_analysis()

        # 示例 3: 批量分析
        await example_batch_analysis()

        # 示例 4: 自定义提示词
        await example_custom_prompt()

        print("\n\n" + "=" * 60)
        print("✅ 所有示例运行完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
