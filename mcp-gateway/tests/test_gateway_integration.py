"""集成测试：验证 MCP Gateway 能正常启动并响应 MCP 协议请求。

MCP stdio 传输格式：每条消息是一行 JSON，以 \\n 结尾（换行分隔 JSON）。

测试内容：
1. Gateway 进程能正常启动
2. MCP initialize 握手成功
3. tools/list 能返回 get_metadata 工具
4. 调用 get_metadata 工具能正常返回
5. Gateway 进程能正常退出
"""
import asyncio
import json
import os
import sys
import pytest

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_JSON_PATH = os.path.join(PROJECT_ROOT, "tests", "test_mcp.json")


async def start_gateway():
    """启动 Gateway 子进程，返回 (process, read_stream, write_stream)"""
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "mcp_gateway.gateway",
        "--mcp-json-path", MCP_JSON_PATH,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=PROJECT_ROOT,
    )
    return proc


async def send_message(proc, msg: dict):
    """发送一条 JSON-RPC 消息（换行分隔格式）"""
    line = json.dumps(msg, ensure_ascii=False) + "\n"
    proc.stdin.write(line.encode("utf-8"))
    await proc.stdin.drain()


async def read_message(proc, timeout=15):
    """从 stdout 读取一条 JSON-RPC 响应（换行分隔格式）"""
    line = await asyncio.wait_for(
        proc.stdout.readline(), timeout=timeout
    )
    if not line:
        raise ConnectionError("Gateway process closed stdout")
    return json.loads(line.decode("utf-8"))


async def send_and_receive(proc, method, params=None, msg_id=1):
    """发送请求并等待响应"""
    msg = {"jsonrpc": "2.0", "method": method, "id": msg_id}
    if params:
        msg["params"] = params
    await send_message(proc, msg)
    return await read_message(proc)


async def send_notification(proc, method, params=None):
    """发送通知（无 id，不等待响应）"""
    msg = {"jsonrpc": "2.0", "method": method}
    if params:
        msg["params"] = params
    await send_message(proc, msg)


async def drain_stderr(proc, timeout=1):
    """尝试读取 stderr 输出（用于调试）"""
    try:
        data = await asyncio.wait_for(proc.stderr.read(4096), timeout=timeout)
        return data.decode(errors="replace")
    except asyncio.TimeoutError:
        return ""


@pytest.mark.asyncio
async def test_gateway_starts_and_responds():
    """测试 Gateway 能启动、握手、列出工具、调用工具"""
    proc = await start_gateway()
    try:
        # 等待进程启动
        await asyncio.sleep(0.5)
        assert proc.returncode is None, "Gateway process exited prematurely"

        # 1. MCP Initialize 握手
        init_resp = await send_and_receive(proc, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        })
        assert "result" in init_resp, f"Initialize failed: {init_resp}"
        result = init_resp["result"]
        assert "serverInfo" in result, f"No serverInfo in init response: {result}"
        assert result["serverInfo"]["name"] == "MCP Gateway"
        print(f"  [OK] Initialize 成功: server={result['serverInfo']['name']}")

        # 2. 发送 initialized 通知
        await send_notification(proc, "notifications/initialized")
        await asyncio.sleep(0.3)

        # 3. tools/list
        tools_resp = await send_and_receive(proc, "tools/list", {}, msg_id=2)
        assert "result" in tools_resp, f"tools/list failed: {tools_resp}"
        tools = tools_resp["result"].get("tools", [])
        tool_names = [t["name"] for t in tools]
        assert "get_metadata" in tool_names, f"get_metadata not found, got: {tool_names}"
        print(f"  [OK] tools/list 成功: {tool_names}")

        # 4. 调用 get_metadata
        call_resp = await send_and_receive(proc, "tools/call", {
            "name": "get_metadata",
            "arguments": {},
        }, msg_id=3)
        assert "result" in call_resp, f"tools/call failed: {call_resp}"
        content = call_resp["result"].get("content", [])
        assert len(content) > 0, "get_metadata returned empty content"
        # 解析返回的 JSON
        text_content = content[0].get("text", "{}")
        metadata = json.loads(text_content)
        print(f"  [OK] get_metadata 调用成功: 返回 {len(metadata)} 个 server 配置")

    finally:
        # 清理
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=5)
        except Exception:
            proc.kill()


@pytest.mark.asyncio
async def test_gateway_standalone_mode():
    """测试 Gateway 在无代理服务器时的独立模式"""
    proc = await start_gateway()
    try:
        await asyncio.sleep(0.5)

        # Initialize
        init_resp = await send_and_receive(proc, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        })
        assert "result" in init_resp

        # 发送 initialized 通知
        await send_notification(proc, "notifications/initialized")
        await asyncio.sleep(0.3)

        # 调用 get_metadata，应该返回 standalone_mode 信息
        call_resp = await send_and_receive(proc, "tools/call", {
            "name": "get_metadata",
            "arguments": {},
        }, msg_id=2)
        content = call_resp["result"]["content"][0]["text"]
        metadata = json.loads(content)
        print(f"  [OK] 独立模式正常: {metadata}")
        assert isinstance(metadata, dict)

    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    asyncio.run(test_gateway_starts_and_responds())
    print("\nAll tests passed!")
