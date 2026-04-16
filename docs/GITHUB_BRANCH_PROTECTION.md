# GitHub 分支保护规则设置指南

## 🎯 目标
为 `main` 分支设置严格的保护规则，防止未经测试的代码直接推送到生产分支。

## 📋 设置步骤

### 1. 访问仓库设置
1. 打开 GitHub 仓库：`https://github.com/hsliuping/QuantScope`
2. 点击 **Settings** 标签页
3. 在左侧菜单中选择 **Branches**

### 2. 添加分支保护规则
1. 点击 **Add rule** 按钮
2. 在 **Branch name pattern** 中输入：`main`

### 3. 配置保护规则

#### 🔒 基础保护设置
- [x] **Require a pull request before merging**
  - [x] **Require approvals**: 设置为 `1`
  - [x] **Dismiss stale PR approvals when new commits are pushed**
  - [x] **Require review from code owners** (如果有 CODEOWNERS 文件)

#### 🧪 状态检查设置
- [x] **Require status checks to pass before merging**
  - [x] **Require branches to be up to date before merging**
  - 添加必需的状态检查（如果有 CI/CD 配置）：
    - [ ] `continuous-integration`
    - [ ] `build`
    - [ ] `test`

#### 🛡️ 高级保护设置
- [x] **Require conversation resolution before merging**
- [x] **Require signed commits**
- [x] **Require linear history**
- [x] **Include administrators** ⚠️ **重要：确保管理员也遵守规则**

#### 🚫 限制设置
- [x] **Restrict pushes that create files**
- [x] **Restrict force pushes**
- [x] **Allow deletions**: **取消勾选** ⚠️ **重要：防止意外删除**

### 4. 保存设置
点击 **Create** 按钮保存分支保护规则。

## 🔧 高级配置（可选）

### 自动合并设置
如果需要自动合并功能：
- [x] **Allow auto-merge**
- 配置合并策略：
  - [ ] Allow merge commits
  - [x] Allow squash merging
  - [ ] Allow rebase merging

### 删除头分支
- [x] **Automatically delete head branches**

## 📊 状态检查配置

### 添加 GitHub Actions 工作流
在 `.github/workflows/` 目录下创建 CI/CD 配置：

```yaml
# .github/workflows/ci.yml
name: CI
on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest tests/
      - name: Check code style
        run: |
          python scripts/syntax_checker.py
```

## 🚨 紧急情况处理

### 临时禁用保护规则
1. 访问 **Settings** > **Branches**
2. 找到 `main` 分支规则
3. 点击 **Edit** 
4. 临时取消勾选相关保护选项
5. **操作完成后立即重新启用！**

### 管理员绕过保护
即使启用了 "Include administrators"，仓库所有者仍可以：
1. 临时修改分支保护规则
2. 使用 `--force-with-lease` 强制推送
3. **强烈建议**: 建立内部审批流程，即使是管理员也要遵守

## 📝 保护规则验证

### 测试保护规则是否生效
```bash
# 1. 尝试直接推送到 main（应该被拒绝）
git checkout main
echo "test" > test.txt
git add test.txt
git commit -m "test commit"
git push origin main  # 应该失败

# 2. 通过 PR 流程（正确方式）
git checkout -b test-protection
git push origin test-protection
# 在 GitHub 上创建 PR 到 main 分支
```

## 🎯 最佳实践建议

### 1. 渐进式实施
- 先在测试仓库验证规则
- 逐步增加保护级别
- 团队培训和适应

### 2. 监控和审计
- 定期检查保护规则设置
- 监控尝试绕过保护的行为
- 记录所有强制推送操作

### 3. 文档和培训
- 为团队提供工作流培训
- 维护最新的操作指南
- 建立问题报告机制

## 🔗 相关资源

- [GitHub 分支保护官方文档](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [GitHub Actions 工作流语法](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [代码审查最佳实践](https://github.com/features/code-review/)

---

**重要提醒：分支保护规则是防止意外的最后一道防线，但不能替代良好的开发习惯和流程！**