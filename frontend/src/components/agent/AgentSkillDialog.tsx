import * as React from "react";
import { Download, FileText, KeyRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";
import { downloadAgentSkillDoc } from "@/utils/agentSkillDoc";

interface AgentSkillDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  username: string;
  token: string;
}

const CAPABILITIES = [
  "查知识库：让 AI 先检索团队文档再回答，答案有出处，不是凭记忆编",
  "建知识库：AI 可以为新项目单独建一个库",
  "传文档：按「项目名-模块-文档名-日期」命名后上传入库",
  "提矛盾：发现文档前后矛盾时，AI 标记过时的那一条，由你确认后下架"
];

const PLACEMENTS = [
  {
    tool: "Claude Code",
    path: "项目根目录的 CLAUDE.md",
    note: "全局生效可放 ~/.claude/CLAUDE.md"
  },
  {
    tool: "Codex",
    path: "项目根目录的 AGENTS.md",
    note: "全局生效可放 ~/.codex/AGENTS.md"
  },
  {
    tool: "Cursor",
    path: ".cursor/rules/ 目录下任意 .md",
    note: "仅对当前项目生效"
  }
];

export function AgentSkillDialog({ open, onOpenChange, username, token }: AgentSkillDialogProps) {
  const handleDownload = () => {
    downloadAgentSkillDoc({ username, token });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            接入你自己的 AI
          </DialogTitle>
          <DialogDescription>
            下载一份说明文档放进 AI 工具，它就能读写这个知识库。
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-2 text-sm">
          <section className="space-y-2">
            <p className="font-medium">你会下载到什么</p>
            <p className="leading-relaxed text-muted-foreground">
              一个 Markdown 文件，写着这个知识库所有接口怎么调。
              <span className="text-foreground">你的账号凭证已经填在里面</span>
              ，所以不用再配环境变量，AI 打开就能用。
            </p>
          </section>

          <section className="space-y-2">
            <p className="font-medium">它能做什么</p>
            <ul className="space-y-1.5">
              {CAPABILITIES.map((item) => (
                <li key={item} className="flex gap-2 leading-relaxed text-muted-foreground">
                  <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-muted-foreground" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="space-y-2">
            <p className="font-medium">放到哪里</p>
            <div className="divide-y divide-border/70 overflow-hidden rounded-xl border border-border/70">
              {PLACEMENTS.map(({ tool, path, note }) => (
                <div key={tool} className="flex flex-col gap-1 px-3.5 py-2.5 sm:flex-row sm:gap-4">
                  <span className="w-24 shrink-0 font-medium">{tool}</span>
                  <div className="min-w-0">
                    <p className="font-mono text-xs text-foreground">{path}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{note}</p>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs leading-relaxed text-muted-foreground">
              目标文件已存在就直接把内容追加到末尾，别覆盖原有内容。
            </p>
          </section>

          <section className="flex gap-2.5 rounded-xl border border-amber-500/30 bg-amber-500/5 px-3.5 py-3">
            <KeyRound className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
            <p className="text-xs leading-relaxed text-muted-foreground">
              文档里的凭证等同于你的账号密码，有效期 30 天。
              别把它提交到公开仓库，也不能转发给别人——过期后回到这里重新下载即可。
            </p>
          </section>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleDownload}>
            <Download className="mr-1.5 h-4 w-4" />
            下载说明文档
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
