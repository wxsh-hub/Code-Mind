# 学生管理系统 - 旧版本

## 系统概述
本系统采用 Spring Boot 2.3 + MySQL 5.7 + Memcached 构建，支持学生信息管理、成绩管理等功能。

## 技术栈
- 后端框架：Spring Boot 2.3
- 数据库：MySQL 5.7
- 缓存：Memcached
- 消息队列：RabbitMQ
- 前端：jQuery + Bootstrap

## 学生信息管理

### 数据结构
```sql
CREATE TABLE students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_no VARCHAR(20) NOT NULL,
  name VARCHAR(50) NOT NULL,
  gender ENUM('男', '女') DEFAULT '男',
  birthday DATE,
  phone VARCHAR(20),
  email VARCHAR(100),
  class_name VARCHAR(50),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 接口设计
| 接口 | 方法 | 路径 | 说明 |
|:---|:---|:---|:---|
| 创建学生 | POST | /api/v1/student/add | 创建学生记录 |
| 查询学生 | GET | /api/v1/student/get?id=xxx | 查询学生详情 |
| 更新学生 | POST | /api/v1/student/update | 更新学生信息 |
| 删除学生 | POST | /api/v1/student/delete?id=xxx | 删除学生记录 |
| 搜索学生 | GET | /api/v1/student/list?keyword=xxx | 按姓名/学号搜索 |

### 搜索功能
支持简单关键词搜索：
- 按姓名模糊搜索
- 按学号精确搜索
- 不支持组合搜索

### 分页查询
```json
{
  "pageNum": 1,
  "pageSize": 20,
  "orderBy": "create_time",
  "orderDir": "DESC"
}
```

## 成绩管理

### 成绩录入
- 支持单条录入
- 不支持批量导入
- 手动计算 GPA

### 成绩查询
- 按学生查询所有成绩
- 不支持按课程查询
- 不支持按学期筛选

### 成绩统计
- 平均分
- 不支持及格率统计

## 课程管理

### 课程信息
```sql
CREATE TABLE courses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_no VARCHAR(20) NOT NULL,
  name VARCHAR(100) NOT NULL,
  credit INT DEFAULT 0,
  teacher VARCHAR(50),
  semester VARCHAR(20),
  capacity INT DEFAULT 0,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 选课系统
- 学生选课
- 无容量限制
- 无时间冲突检测

## 权限管理

### 角色定义
- 管理员：全部权限
- 教师：成绩管理
- 学生：查询

### 认证方式
使用 Basic Auth 进行认证，支持：
- 账号密码登录
- 不支持手机验证码
- 不支持单点登录

## 部署信息

### 环境要求
- JDK 8
- Maven 3.5
- MySQL 5.7
- Tomcat 8

### 启动命令
```bash
# 后端
cd backend
mvn package
java -jar target/student-system.jar

# 部署到 Tomcat
cp target/student-system.war /opt/tomcat/webapps/
```

## 更新日志

### v1.2.0 (2025-06-01)
- 修复成绩查询bug
- 优化搜索性能

### v1.0.0 (2024-01-01)
- 初始版本发布
