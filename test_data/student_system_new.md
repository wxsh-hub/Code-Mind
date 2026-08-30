# 学生管理系统 - 新版本

## 系统概述
本系统采用 Spring Boot 4.1 + PostgreSQL 16 + Redis 7 构建，支持学生信息管理、成绩管理、课程管理等功能。

## 技术栈
- 后端框架：Spring Boot 4.1
- 数据库：PostgreSQL 16 + pgvector
- 缓存：Redis 7
- 消息队列：RocketMQ 5.2
- 前端：React 18 + TypeScript

## 学生信息管理

### 数据结构
```json
{
  "student_id": "STU20260001",
  "name": "张三",
  "gender": "男",
  "birth_date": "2000-01-15",
  "phone": "13800138001",
  "email": "zhangsan@example.com",
  "class_id": "CS202601",
  "enrollment_date": "2026-09-01",
  "status": "active"
}
```

### 接口设计
| 接口 | 方法 | 路径 | 说明 |
|:---|:---|:---|:---|
| 创建学生 | POST | /api/student | 创建学生记录 |
| 查询学生 | GET | /api/student/{id} | 查询学生详情 |
| 更新学生 | PUT | /api/student/{id} | 更新学生信息 |
| 删除学生 | DELETE | /api/student/{id} | 删除学生记录 |
| 搜索学生 | GET | /api/student/search | 按姓名/学号搜索 |

### 搜索功能
支持多条件组合搜索：
- 按姓名模糊搜索
- 按学号精确搜索
- 按班级筛选
- 按入学时间范围筛选

### 分页查询
```json
{
  "page": 1,
  "size": 20,
  "sort": "enrollment_date",
  "order": "desc"
}
```

## 成绩管理

### 成绩录入
- 支持批量导入（Excel/CSV）
- 支持单条录入
- 自动计算 GPA

### 成绩查询
- 按学生查询所有成绩
- 按课程查询所有学生
- 按学期查询

### 成绩统计
- 平均分、最高分、最低分
- 及格率、优秀率
- GPA 计算

## 课程管理

### 课程信息
```json
{
  "course_id": "CS101",
  "name": "计算机导论",
  "credit": 3,
  "teacher": "李教授",
  "semester": "2026-1",
  "capacity": 60,
  "enrolled": 45
}
```

### 选课系统
- 学生自主选课
- 容量限制
- 时间冲突检测

## 权限管理

### 角色定义
- 管理员：全部权限
- 教师：成绩管理、课程管理
- 学生：查询个人信息、成绩

### 认证方式
使用 Sa-Token 进行认证，支持：
- 账号密码登录
- 手机验证码登录
- 单点登录（SSO）

## 部署信息

### 环境要求
- JDK 17+
- Maven 3.9+
- Node.js 18+
- PostgreSQL 16
- Redis 7

### 启动命令
```bash
# 后端
cd backend
mvn spring-boot:run

# 前端
cd frontend
npm install
npm run dev
```

### Docker 部署
```bash
docker-compose up -d
```

## 更新日志

### v2.0.0 (2026-08-30)
- 迁移到 Spring Boot 4.1
- 数据库从 MySQL 迁移到 PostgreSQL
- 缓存从 Memcached 迁移到 Redis
- 前端从 jQuery 迁移到 React 18
- 新增向量检索功能（pgvector）

### v1.0.0 (2025-01-01)
- 初始版本发布
