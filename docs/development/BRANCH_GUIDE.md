# 分支管理指南

本文档说明了QuantScope项目的分支管理策略和工作流程。

## 🌳 分支结构

### 主要分支
- **main**: 主分支，包含稳定的生产代码
- **develop**: 开发分支，包含最新的开发功能
- **feature/***: 功能分支，用于开发新功能
- **hotfix/***: 热修复分支，用于紧急修复

### 分支命名规范
```
feature/功能名称          # 新功能开发
hotfix/修复描述          # 紧急修复
release/版本号           # 版本发布
docs/文档更新            # 文档更新
```

## 🔄 工作流程

### 1. 功能开发流程
```bash
# 1. 从develop创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# 2. 开发功能
# ... 编写代码 ...

# 3. 提交更改
git add .
git commit -m "feat: 添加新功能"

# 4. 推送分支
git push origin feature/new-feature

# 5. 创建Pull Request到develop
```

### 2. 热修复流程
```bash
# 1. 从main创建热修复分支
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix

# 2. 修复问题
# ... 修复代码 ...

# 3. 提交更改
git add .
git commit -m "fix: 修复关键问题"

# 4. 推送分支
git push origin hotfix/critical-fix

# 5. 创建PR到main和develop
```

### 3. 版本发布流程
```bash
# 1. 从develop创建发布分支
git checkout develop
git pull origin develop
git checkout -b release/v1.0.0

# 2. 准备发布
# ... 更新版本号、文档等 ...

# 3. 测试验证
# ... 运行测试 ...

# 4. 合并到main
git checkout main
git merge release/v1.0.0
git tag v1.0.0

# 5. 合并回develop
git checkout develop
git merge release/v1.0.0
```

## 📋 分支保护规则

### main分支
- 禁止直接推送
- 需要Pull Request
- 需要代码审查
- 需要通过所有测试

### develop分支
- 禁止直接推送
- 需要Pull Request
- 建议代码审查

## 🔍 代码审查

### 审查要点
- [ ] 代码质量和规范
- [ ] 功能完整性
- [ ] 测试覆盖率
- [ ] 文档更新
- [ ] 性能影响

### 审查流程
1. 创建Pull Request
2. 自动化测试运行
3. 代码审查
4. 修改反馈
5. 批准合并

## 🚀 最佳实践

### 提交规范
```
feat: 新功能
fix: 修复
docs: 文档
style: 格式
refactor: 重构
test: 测试
chore: 构建
```

### 分支管理
- 保持分支简洁
- 及时删除已合并分支
- 定期同步上游更改
- 避免长期存在的功能分支

### 冲突解决
```bash
# 1. 更新目标分支
git checkout develop
git pull origin develop

# 2. 切换到功能分支
git checkout feature/my-feature

# 3. 变基到最新develop
git rebase develop

# 4. 解决冲突
# ... 手动解决冲突 ...

# 5. 继续变基
git rebase --continue

# 6. 强制推送
git push --force-with-lease origin feature/my-feature
```

## 📊 分支状态监控

### 检查命令
```bash
# 查看所有分支
git branch -a

# 查看分支状态
git status

# 查看分支历史
git log --oneline --graph

# 查看远程分支
git remote show origin
```

### 清理命令
```bash
# 删除已合并的本地分支
git branch --merged | grep -v main | xargs git branch -d

# 删除远程跟踪分支
git remote prune origin

# 清理无用的引用
git gc --prune=now
```

## 🔧 工具配置

### Git配置
```bash
# 设置用户信息
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 设置默认分支
git config init.defaultBranch main

# 设置推送策略
git config push.default simple
```

### IDE集成
- 使用Git图形化工具
- 配置代码格式化
- 设置提交模板
- 启用分支保护

---

遵循这些指南可以确保项目的代码质量和开发效率。
