# Code-Mind 应用镜像
#
# 构建上下文需包含 bootstrap-0.0.1-SNAPSHOT.jar：
#   docker build -t code-mind:latest -f Dockerfile .
#
# 镜像只装 jar，不含配置：application-server.yaml 里有 API Key，
# 打进镜像会让密钥随镜像流动，故运行时以卷挂载。
# 基础镜像用 JRE 而非 JDK：运行期不需要编译器，省约 200MB。

FROM eclipse-temurin:17-jre

LABEL maintainer="Code-Mind" \
      description="企业级 AI 知识管理平台"

WORKDIR /app

# 时区设为东八区：日志与数据库时间戳需与本地一致，基础镜像默认 UTC
ENV TZ=Asia/Shanghai

# 堆上限显式限定，避免默认按宿主机内存 1/4 取值挤占其他进程
ENV JAVA_OPTS="-Xms256m -Xmx512m -XX:+UseG1GC -Duser.timezone=Asia/Shanghai"

COPY bootstrap-0.0.1-SNAPSHOT.jar /app/app.jar

# 配置目录留作卷挂载点，镜像内为空
RUN mkdir -p /app/config /app/logs

EXPOSE 9090

# 用 sh -c 展开 $JAVA_OPTS：ENTRYPOINT 的 exec 形式不做变量替换
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app/app.jar \
  --spring.profiles.active=server \
  --spring.config.additional-location=file:/app/config/"]
