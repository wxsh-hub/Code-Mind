# Java 编码规范

## 命名规范

### 类名
使用 PascalCase，如 `UserService`、`OrderController`

### 方法名
使用 camelCase，如 `getUserById`、`createOrder`

### 常量
使用 UPPER_SNAKE_CASE，如 `MAX_RETRY_COUNT`、`DEFAULT_TIMEOUT`

### 包名
全部小写，如 `com.company.project.module`

## 代码格式

### 缩进
使用 4 个空格，不要使用 Tab

### 行宽
每行不超过 120 个字符

### 大括号
左大括号不换行，右大括号独占一行

```java
if (condition) {
    // do something
} else {
    // do something else
}
```

## 异常处理

### 不要捕获通用异常
```java
// ❌ 错误
try {
    // ...
} catch (Exception e) {
    // ...
}

// ✅ 正确
try {
    // ...
} catch (IOException e) {
    // ...
}
```

### 不要忽略异常
```java
// ❌ 错误
try {
    // ...
} catch (IOException e) {
    // 空白
}

// ✅ 正确
try {
    // ...
} catch (IOException e) {
    log.error("Failed to read file", e);
    throw new ServiceException("File read failed", e);
}
```

## 注释规范

### 类注释
```java
/**
 * 用户服务类
 * <p>
 * 处理用户相关的业务逻辑，包括注册、登录、权限管理
 *
 * @author team
 * @since 1.0.0
 */
```

### 方法注释
```java
/**
 * 根据用户ID查询用户信息
 *
 * @param userId 用户ID
 * @return 用户信息，不存在返回null
 * @throws UserNotFoundException 用户不存在时抛出
 */
```

## 最佳实践

1. 使用 Optional 代替 null 检查
2. 使用 Stream API 进行集合操作
3. 使用 Builder 模式构建复杂对象
4. 避免使用魔法数字，定义为常量
5. 单一职责原则，每个方法只做一件事
