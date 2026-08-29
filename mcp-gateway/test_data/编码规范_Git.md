# Git 提交规范

## 分支管理

### 分支命名
- 主分支：`main` / `master`
- 开发分支：`dev` / `develop`
- 功能分支：`feature/功能名称`
- 修复分支：`fix/问题描述`
- 发布分支：`release/版本号`

### 分支策略
1. `main` 分支保持稳定，随时可发布
2. 所有开发在 `dev` 分支进行
3. 功能分支从 `dev` 创建，完成后合并回 `dev`
4. 发布时从 `dev` 创建 `release` 分支

## Commit 规范

### 消息格式
```
<类型>: <简短描述>

<详细描述（可选）>
<关联 Issue（可选）>
```

### 类型
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例
```bash
# ✅ 正确
git commit -m "feat: 添加用户注册功能"
git commit -m "fix: 修复登录超时问题"
git commit -m "docs: 更新 API 文档"

# ❌ 错误
git commit -m "update"
git commit -m "fix bug"
git commit -m "提交"
```

## 提交流程

### 1. 拉取最新代码
```bash
git pull origin dev
```

### 2. 创建功能分支
```bash
git checkout -b feature/user-register
```

### 3. 开发并提交
```bash
git add .
git commit -m "feat: 添加用户注册功能"
```

### 4. 推送到远程
```bash
git push origin feature/user-register
```

### 5. 创建 Merge Request

## 代码审查

### 审查要点
1. 代码是否符合编码规范
2. 是否有安全隐患
3. 是否有性能问题
4. 测试是否充分
5. 文档是否更新

### 审查流程
1. 提交 MR 后自动通知审查人
2. 审查人在 24 小时内完成审查
3. 审查通过后合并到 `dev` 分支

## 常用命令

### 查看状态
```bash
git status
git log --oneline -10
```

### 暂存更改
```bash
git stash
git stash pop
```

### 合并分支
```bash
git checkout dev
git merge feature/user-register
```

### 解决冲突
```bash
# 编辑冲突文件
git add .
git commit -m "merge: 合并 feature/user-register"
```

## 最佳实践

1. 每次提交只做一件事
2. 提交前先运行测试
3. 不要提交敏感信息（密码、密钥）
4. 使用 `.gitignore` 忽略不需要的文件
5. 定期拉取远程代码，避免大冲突
