# 订单中心服务技术文档

## 一、服务概述

订单中心（order-center）是交易域的核心服务，负责订单的创建、支付回调处理、状态流转与超时关闭。上游为交易网关，下游对接支付中心、库存中心与履约中心。服务采用 Spring Boot 3 构建，注册到 Nacos 的 `trade` 命名空间。

服务对外提供 REST 接口，内部通过 RocketMQ 与库存、履约异步解耦。订单主表按用户 ID 哈希分 16 张表，分片键为 `user_id`。

## 二、配置说明

以下为生产环境的默认配置项，部署到新环境时需按实际情况覆盖。

```yaml
order:
  server:
    port: 8081
    context-path: /order-center
  timeout:
    pay-expire-minutes: 30      # 未支付订单超时关闭时间
    confirm-expire-days: 15     # 已发货订单自动确认收货天数
    refund-audit-hours: 48      # 退款申请人工审核时限
  mq:
    topic: order-status-change
    consumer-group: order-center-cg
  sharding:
    table-count: 16
    shard-key: user_id
```

关键配置项说明：

| 配置项 | 默认值 | 含义 | 可动态调整 |
|--------|--------|------|-----------|
| pay-expire-minutes | 30 | 未支付订单超时关闭分钟数 | 是 |
| confirm-expire-days | 15 | 发货后自动确认收货天数 | 是 |
| refund-audit-hours | 48 | 退款审核时限，超时自动通过 | 否 |
| table-count | 16 | 分表数量，修改需数据迁移 | 否 |
| shard-key | user_id | 分片键，不建议变更 | 否 |

## 三、核心接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建订单 | POST | /order-center/orders | 幂等，需传 requestId |
| 查询订单 | GET | /order-center/orders/{orderId} | 按订单号查询 |
| 取消订单 | PUT | /order-center/orders/{orderId}/cancel | 仅待支付状态可取消 |
| 支付回调 | POST | /order-center/callback/pay | 由支付中心回调，需验签 |
| 确认收货 | PUT | /order-center/orders/{orderId}/confirm | 已发货状态可操作 |

创建订单接口必须携带 `requestId` 做幂等控制，重复提交同一个 `requestId` 会返回首次创建的订单，不会产生新订单。`requestId` 的幂等窗口为 24 小时。

## 四、订单状态流转

订单共 7 个状态，流转规则如下：

1. `CREATED` 待支付 —— 订单创建后的初始状态
2. `PAID` 已支付 —— 收到支付中心回调且验签通过后进入
3. `SHIPPED` 已发货 —— 履约中心回传发货信息后进入
4. `CONFIRMED` 已确认收货 —— 用户主动确认或超时自动确认
5. `COMPLETED` 已完成 —— 确认收货后 7 天自动进入，此后不可退款
6. `CANCELLED` 已取消 —— 用户主动取消或超时未支付自动取消
7. `REFUNDED` 已退款 —— 退款流程走完后的终态

状态流转只能单向推进，不允许回退。`CANCELLED`、`COMPLETED`、`REFUNDED` 为终态，进入后不可再变更。

## 五、错误码

| 错误码 | 含义 | 处理建议 |
|--------|------|---------|
| E4001 | 订单不存在 | 检查 orderId 是否正确 |
| E4002 | 订单状态不允许该操作 | 查询当前状态后再操作 |
| E4003 | 重复提交 | 复用首次返回的 orderId |
| E4004 | 支付回调验签失败 | 检查支付中心密钥配置 |
| E5001 | 分片路由失败 | 检查 user_id 是否为空 |
| E5002 | MQ 发送失败 | 检查 RocketMQ 连接与 topic 是否创建 |

## 六、常见问题排查

### 6.1 订单重复创建

先确认调用方是否透传了 `requestId`。若已透传仍重复，检查 Redis 中幂等 key 是否被提前清理——幂等 key 的 TTL 应与业务窗口一致，为 24 小时。若 TTL 被误设为 1 小时，超过 1 小时的重试会产生新订单。

### 6.2 支付回调丢失

支付回调失败会进重试队列，重试间隔为 1 分钟、5 分钟、30 分钟、2 小时、6 小时，共 5 次。5 次仍失败则进入死信队列，需人工介入。排查时先看 `order-center` 日志中的 `callback` 关键字，再确认支付中心侧的回调记录。

### 6.3 状态流转卡住

若订单长时间停留在 `PAID` 状态，通常是履约中心没有回传发货信息。检查 MQ 消费位点是否滞后，再看 `order-status-change` topic 中是否有对应的发货消息。

### 6.4 分片查询慢

跨分片查询（如按订单号查询但未带 user_id）会广播到全部 16 张表，性能较差。正确做法是查询时携带 `user_id`，让路由精确定位到单表。若业务上确实无法提供 `user_id`，应改用订单号到分片的映射表。

## 七、代码示例

创建订单的核心逻辑：

```java
public OrderVO createOrder(CreateOrderRequest request) {
    // 1. 幂等校验，requestId 为幂等键
    String idempotentKey = "order:create:" + request.getRequestId();
    Boolean absent = redis.opsForValue()
            .setIfAbsent(idempotentKey, "1", Duration.ofHours(24));
    if (Boolean.FALSE.equals(absent)) {
        return queryByRequestId(request.getRequestId());
    }

    // 2. 按 user_id 路由到具体分片
    long shard = request.getUserId() % 16;
    OrderDO order = OrderDO.create(request, shard);
    orderMapper.insert(order);

    // 3. 发送状态变更消息，驱动下游
    mqProducer.send("order-status-change", order.getOrderId(), order.getStatus());
    return OrderVO.from(order);
}
```

## 八、依赖与部署

服务依赖以下中间件：

- MySQL 8.0 —— 订单主库，16 张分表
- Redis 7 —— 幂等控制与分布式锁
- RocketMQ 5 —— 状态变更消息
- Nacos —— 服务注册与配置中心

部署方式为 Docker + K8s，副本数 4，单副本资源配置为 2 核 4G。健康检查路径为 `/order-center/actuator/health`，就绪探针延迟 30 秒，存活探针延迟 60 秒。
