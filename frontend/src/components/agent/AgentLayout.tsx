import * as React from "react";
import { useNavigate } from "react-router-dom";

import { AgentGuideDialog } from "@/components/agent/AgentGuideDialog";
import { AgentSidebar } from "@/components/agent/AgentSidebar";
import { AgentSkillDialog } from "@/components/agent/AgentSkillDialog";
import { getAgentMeta } from "@/services/agentService";
import { useAuthStore } from "@/stores/authStore";
import type { AgentEngineMeta } from "@/types/agent";

export type AgentMetaState =
  | { status: "probing" }
  | { status: "online"; meta: AgentEngineMeta }
  | { status: "offline"; message: string };

// 进页拉一次 /agent/v1/meta 点亮徽标与框架信息块
function useAgentMeta(): AgentMetaState {
  const [state, setState] = React.useState<AgentMetaState>({ status: "probing" });

  React.useEffect(() => {
    let alive = true;
    getAgentMeta()
      .then((meta) => {
        if (alive) setState({ status: "online", meta });
      })
      .catch((error) => {
        if (alive) {
          setState({ status: "offline", message: (error as Error).message || "连接失败" });
        }
      });
    return () => {
      alive = false;
    };
  }, []);

  return state;
}

interface AgentHeaderProps {
  meta: AgentMetaState;
  onOpenGuide: () => void;
  onOpenSkill: () => void;
  canExportSkill: boolean;
}

function AgentHeader({ meta, onOpenGuide, onOpenSkill, canExportSkill }: AgentHeaderProps) {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role === "admin";

  const badgeName =
    meta.status === "online" ? meta.meta.framework : meta.status === "probing" ? "探测中" : "离线";

  return (
    <header className="agent-header">
      <div className="agent-brand">
        <span className="agent-wordmark">CodeMind</span>
        <span className="agent-brand-sep">/</span>
        <span className="agent-brand-tag">企业知识库</span>
      </div>

      <div className="agent-header-center">
        <span className="agent-badge">
          <span className="agent-dot" data-status={meta.status} aria-hidden="true" />
          <span className="agent-badge-name">{badgeName}</span>
        </span>
        {meta.status === "online" ? (
          <span className="agent-badge-model">{meta.meta.model || "未配模型"}</span>
        ) : null}
        {meta.status === "offline" ? (
          <span className="agent-badge-err" title={meta.message}>
            连接失败
          </span>
        ) : null}
      </div>

      <div className="agent-header-right">
        <button
          type="button"
          className="agent-head-btn"
          onClick={onOpenGuide}
          title="看看怎么提问、回答怎么读、知识从哪来"
        >
          <span className="agent-btn-glyph">?</span> 使用说明
        </button>
        {canExportSkill && (
          <button
            type="button"
            className="agent-head-btn"
            onClick={onOpenSkill}
            title="下载接入说明，放进你自己的 AI 工具目录，它就能读写这个知识库"
          >
            <span className="agent-btn-glyph">↓</span> 接入 AI
          </button>
        )}
        {/* 主行动按钮：实心高亮。此前与其它按钮同款描边，多数人注意不到后台入口 */}
        {isAdmin && (
          <button
            type="button"
            className="agent-head-btn agent-head-btn-primary"
            onClick={() => navigate("/admin/dashboard")}
          >
            <span className="agent-btn-glyph">⚙</span> 管理后台
          </button>
        )}
      </div>
    </header>
  );
}

interface AgentLayoutProps {
  children: React.ReactNode;
}

export function AgentLayout({ children }: AgentLayoutProps) {
  const meta = useAgentMeta();
  const user = useAuthStore((state) => state.user);
  const token = useAuthStore((state) => state.token);
  const [guideOpen, setGuideOpen] = React.useState(false);
  const [skillOpen, setSkillOpen] = React.useState(false);

  // 文档正文含 token，缺任一项就不给下载，避免导出半份不可用的说明
  const canExportSkill = Boolean(user && token);

  return (
    <div className="agent-app">
      <AgentHeader
        meta={meta}
        onOpenGuide={() => setGuideOpen(true)}
        onOpenSkill={() => setSkillOpen(true)}
        canExportSkill={canExportSkill}
      />
      <div className="agent-body">
        <AgentSidebar />
        <main className="agent-main">{children}</main>
      </div>
      <AgentGuideDialog
        open={guideOpen}
        onOpenChange={setGuideOpen}
        onOpenSkillExport={canExportSkill ? () => setSkillOpen(true) : undefined}
      />
      {canExportSkill && user && token ? (
        <AgentSkillDialog
          open={skillOpen}
          onOpenChange={setSkillOpen}
          username={user.username || String(user.userId)}
          token={token}
        />
      ) : null}
    </div>
  );
}
