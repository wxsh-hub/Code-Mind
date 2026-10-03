import * as React from "react";

import { Loading } from "@/components/common/Loading";
import { useEngineStore } from "@/stores/engineStore";

/**
 * 两个聊天页各自懒加载。
 *
 * 此前是顶部静态 import，于是 EngineGate 一旦被路由引入，AgentChatPage 与
 * ChatPage 及其依赖（Markdown 渲染、代码高亮、会话侧栏）都会打进主包——
 * 连登录页也要一并下载。改为动态 import 后，两者各自成片，
 * 且只在对应引擎档位下才加载其中一个。
 */
const AgentChatPage = React.lazy(() =>
  import("@/pages/AgentChatPage").then((module) => ({ default: module.AgentChatPage }))
);
const ChatPage = React.lazy(() =>
  import("@/pages/ChatPage").then((module) => ({ default: module.ChatPage }))
);

export function EngineGate() {
  const engineType = useEngineStore((state) => state.engineType);
  const initialize = useEngineStore((state) => state.initialize);

  React.useEffect(() => {
    initialize().catch(() => null);
  }, [initialize]);

  if (!engineType) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <Loading />
      </div>
    );
  }

  return (
    <React.Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-white">
          <Loading />
        </div>
      }
    >
      {engineType === "agent" ? <AgentChatPage /> : <ChatPage />}
    </React.Suspense>
  );
}
