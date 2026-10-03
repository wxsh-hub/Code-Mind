import * as React from "react";
import { BookOpen, Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

interface AgentGuideDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** 引导到「接入你自己的 AI」弹窗；由外层关闭本弹窗后再打开 */
  onOpenSkillExport?: () => void;
}

/** 左侧菜单的一项，body 用 ReactNode 以便插入代码、按钮等富文本 */
interface GuideSection {
  id: string;
  label: string;
  title: string;
  body: React.ReactNode;
}

function P({ children }: { children: React.ReactNode }) {
  return <p className="text-sm leading-relaxed text-muted-foreground">{children}</p>;
}

function Steps({ items }: { items: Array<{ title: string; desc: string }> }) {
  return (
    <ol className="space-y-3">
      {items.map((item, index) => (
        <li key={item.title} className="flex gap-3">
          <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium">
            {index + 1}
          </span>
          <div>
            <p className="text-sm font-medium">{item.title}</p>
            <p className="mt-0.5 text-sm leading-relaxed text-muted-foreground">{item.desc}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

function Field({ label, desc }: { label: string; desc: string }) {
  return (
    <div className="flex flex-col gap-1 border-b border-border/60 py-2.5 last:border-b-0 sm:flex-row sm:gap-4">
      <span className="w-32 shrink-0 font-mono text-xs text-foreground">{label}</span>
      <span className="text-sm leading-relaxed text-muted-foreground">{desc}</span>
    </div>
  );
}

/** 后台菜单的一项：左菜单名、右说明，长说明自动换行 */
function MenuRef({ name, desc }: { name: string; desc: string }) {
  return (
    <div className="flex flex-col gap-1 border-b border-border/60 py-2.5 last:border-b-0 sm:flex-row sm:gap-4">
      <span className="w-32 shrink-0 text-sm font-medium text-foreground">{name}</span>
      <span className="text-sm leading-relaxed text-muted-foreground">{desc}</span>
    </div>
  );
}

function Callout({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border/70 bg-muted/40 px-3.5 py-3 text-sm leading-relaxed text-muted-foreground">
      {children}
    </div>
  );
}

export function AgentGuideDialog({ open, onOpenChange, onOpenSkillExport }: AgentGuideDialogProps) {
  const [activeId, setActiveId] = React.useState("start");

  // 每次打开回到第一节，避免上次停在末尾让新用户以为没内容
  React.useEffect(() => {
    if (open) setActiveId("start");
  }, [open]);

  const sections: GuideSection[] = [
    {
      id: "start",
      label: "快速上手",
      title: "三步开始用",
      body: (
        <div className="space-y-4">
          <Steps
            items={[
              {
                title: "直接在下面输入框提问",
                desc: "用大白话问就行，不用讲究措辞。比如「订单支付回调怎么验签」「新员工入职要走哪些流程」。"
              },
              {
                title: "等它先去查资料，再回答",
                desc: "它不会凭记忆瞎答，而是先从企业知识库里检索相关文档，再根据文档作答。你会在回答里看到它查了哪些内容。"
              },
              {
                title: "不满意就追问",
                desc: "同一个对话里接着问，它记得上文。答案不对时补一句「是 XX 场景的」，比重新开一个对话效果好。"
              }
            ]}
          />
          <Callout>
            左侧栏存着你的历史对话，随时可以点回去接着聊。找不着对话时按{" "}
            <kbd className="rounded border border-border bg-background px-1.5 py-0.5 font-mono text-xs">
              Ctrl
            </kbd>{" "}
            +{" "}
            <kbd className="rounded border border-border bg-background px-1.5 py-0.5 font-mono text-xs">
              K
            </kbd>{" "}
            搜索。
          </Callout>
        </div>
      )
    },
    {
      id: "upload",
      label: "上传文档",
      title: "怎么把文档放进知识库",
      body: (
        <div className="space-y-4">
          <P>
            知识库里的文档由管理员上传。入口不在聊天页，在
            <span className="mx-1 font-medium text-foreground">管理后台</span>
            里，四步走：
          </P>
          <Steps
            items={[
              {
                title: "进入「知识库管理」",
                desc: "点右上角「管理后台」，在左侧菜单里选「知识库管理」。"
              },
              {
                title: "先创建知识库（已有则跳过）",
                desc: "点右上角「新建知识库」，填名称、选向量模型即可。一个项目建一个库，不要按文档建。"
              },
              {
                title: "点那一行的「管理」按钮",
                desc: "在知识库列表右侧操作列里。点知识库名字也能进，但按钮更好找。"
              },
              {
                title: "上传文件，等分块跑完",
                desc: "点「上传文档」选文件提交。传完状态列先显示 pending（灰点），要等它变成 success（绿点）才真正能被检索到，通常几秒到几十秒。"
              }
            ]}
          />
          <Callout>
            <span className="font-medium text-foreground">命名建议</span>：文件名按
            <span className="mx-1 font-mono text-xs text-foreground">项目名-模块-文档名-日期</span>
            来起，例如
            <span className="mx-1 font-mono text-xs text-foreground">
              订单中心-支付-回调验签说明-20261002
            </span>
            。这样后台列表一眼能看出归属，回答引用时显示的也是这个名字。
          </Callout>
          <P>
            传上去之后想改内容，回到同一个文档页可以
            <span className="mx-1 font-medium text-foreground">查看和编辑分块</span>
            ——AI 是按分块检索的，改分块比重新上传整篇更快。
          </P>
        </div>
      )
    },
    {
      id: "ask",
      label: "怎么问",
      title: "这样问，答案更准",
      body: (
        <div className="space-y-4">
          <P>
            检索是按关键词匹配文档的，所以问题里带上
            <span className="mx-1 font-medium text-foreground">具体名词</span>
            命中率最高。
          </P>
          <div className="space-y-2">
            <Field label="推荐" desc="订单中心支付回调的验签流程是什么" />
            <Field label="避免" desc="这个东西怎么弄" />
            <Field label="推荐" desc="离职员工的账号多久回收" />
            <Field label="避免" desc="离职相关的规定" />
          </div>
          <Callout>
            想让它多想几步，打开输入框左下角的
            <span className="mx-1 font-medium text-foreground">深度思考</span>
            开关。简单问题不用开，开了反而慢。
          </Callout>
        </div>
      )
    },
    {
      id: "read",
      label: "看懂回答",
      title: "回答里的四段是什么",
      body: (
        <div className="space-y-4">
          <P>每轮回答拆成四段，可以逐段核对它有没有胡来：</P>
          <div className="space-y-2">
            <Field label="提问" desc="你原话的复述，确认它没听岔。" />
            <Field label="思考" desc="它打算怎么答、为什么要查这个。这段是它的推理过程。" />
            <Field label="工具" desc="它实际调了哪个检索工具、拿回了哪些文档片段。怀疑答案时重点看这里。" />
            <Field label="答复" desc="最终给你的答案。有出处的地方可以点开看原文。" />
          </div>
          <Callout>
            页面底部写着「内容由 AI 生成，请仔细甄别」。涉及金额、合规、对外承诺的事，
            <span className="mx-1 font-medium text-foreground">以它引用的原文为准</span>
            ，别只看结论。
          </Callout>
        </div>
      )
    },
    {
      id: "kb",
      label: "知识从哪来",
      title: "知识库里的东西是谁放的",
      body: (
        <div className="space-y-4">
          <P>
            两部分：管理员上传的项目文档，以及 AI 自己在干活过程中整理并提交的内容。
            两者都进同一个知识库，回答时会一起检索。
          </P>
          <P>
            如果发现答案不对，很可能是库里的文档本身过时了。你可以在
            <span className="mx-1 font-medium text-foreground">管理后台</span>
            里找到对应文档更新，或者直接告诉管理员。
          </P>
          <Callout>
            想自己往库里放文档，看「上传文档」那一节，四个步骤写全了。
          </Callout>
        </div>
      )
    },
    {
      id: "admin",
      label: "管理后台",
      title: "后台里都有什么",
      body: (
        <div className="space-y-5">
          <P>
            点右上角
            <span className="mx-1 font-medium text-foreground">管理后台</span>
            进入。这个系统不止是问答——上传文档、配置检索范围、排查问题都在后台做。
            菜单分两组，上面是日常用的，下面是设置类。
          </P>

          <section className="space-y-1">
            <p className="text-sm font-medium">日常</p>
            <div>
              <MenuRef
                name="知识库管理"
                desc="最常用。建库、传文档、看分块。传完要等分块跑完才能被检索到。"
              />
              <MenuRef
                name="分块管理"
                desc="文档被切成的每一段。切得不好（比如表格被拆散）可以在这里手动改。"
              />
              <MenuRef
                name="意图管理"
                desc="配置「用户问什么 → 去哪些库查」的对应关系。改这里对答案准确度影响最直接。"
              />
              <MenuRef
                name="数据通道"
                desc="文档入库前的流水线：清洗、增强、打标签。格式杂乱的历史文档走这里处理。"
              />
              <MenuRef
                name="关键词映射"
                desc="同义词归一。用户嘴里的说法和文档里写的不一致时，在这加一条映射就能搜到。"
              />
              <MenuRef
                name="链路追踪"
                desc="每次问答走了哪些步骤、每步花多久。排查「为什么答得慢」「为什么没查到」看这里。"
              />
              <MenuRef
                name="矛盾审核"
                desc="审核 AI 提出的文档冲突，确认哪条该下架。"
              />
              <MenuRef
                name="智能体管理"
                desc="改 AI 的人设和提示词。默认助手整套可用，只改你要动的那条。"
              />
              <MenuRef
                name="模块管理 / 功能元数据标记"
                desc="给知识打业务标签，供上面的检索范围过滤使用。"
              />
              <MenuRef name="审计日志" desc="谁在什么时候改了哪个知识库。" />
            </div>
          </section>

          <section className="space-y-1">
            <p className="text-sm font-medium">设置</p>
            <div>
              <MenuRef name="用户管理" desc="加人、改角色。普通用户看不到后台入口。" />
              <MenuRef name="示例问题" desc="聊天页「试试这些开场」里的推荐问法，从这维护。" />
              <MenuRef name="系统设置" desc="模型档位、检索参数、限流。改动会影响所有人，谨慎操作。" />
            </div>
          </section>

          <Callout>
            想改知识库内容但不确定怎么做，先看「知识库管理」。
            日常九成的事——传文档、改分块、看检索效果——都在那一个模块里完成。
          </Callout>
        </div>
      )
    },
    {
      id: "export",
      label: "接入你的 AI",
      title: "让 Claude、Codex 也能查这个库",
      body: (
        <div className="space-y-4">
          <P>
            下载一份说明文档，放进你平时用的 AI 编程工具里，它就能一边写代码一边查你们团队的知识库，
            不用再来这个页面问。
          </P>
          <P>
            文档里已经填好你的账号凭证，放到 Claude Code 的
            <span className="mx-1 font-mono text-xs text-foreground">CLAUDE.md</span>、Codex 的
            <span className="mx-1 font-mono text-xs text-foreground">AGENTS.md</span>
            或 Cursor 的
            <span className="mx-1 font-mono text-xs text-foreground">.cursor/rules/</span>
            下即可。点下面按钮看详细步骤。
          </P>
          {onOpenSkillExport ? (
            <Button
              onClick={() => {
                onOpenChange(false);
                onOpenSkillExport();
              }}
            >
              <Download className="mr-1.5 h-4 w-4" />
              获取接入说明
            </Button>
          ) : null}
        </div>
      )
    },
    {
      id: "faq",
      label: "常见问题",
      title: "遇到这些情况怎么办",
      body: (
        <div className="space-y-2">
          <Field
            label="答不上来"
            desc="说明知识库里没这方面的文档。换个说法再问一次；仍然不行就是真没有，找管理员补文档。"
          />
          <Field
            label="答案不对"
            desc="先看「工具」那段它引用了哪些原文。如果原文本身过时，去后台「知识库管理」更新对应文档，问题在文档不在 AI。"
          />
          <Field label="回答一半停了" desc="网络抖动，重新发一次即可。旁边的对话记录不受影响。" />
          <Field label="想换新话题" desc="点左侧「新建对话」。同一个对话里话题跳来跳去，它容易混淆上下文。" />
          <Field label="凭证过期" desc="接入说明文档 30 天有效，过期后回到「接入你的 AI」重新下载一份。" />
        </div>
      )
    }
  ];

  const active = sections.find((section) => section.id === activeId) ?? sections[0];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* DialogContent 本身是 grid，行高用 grid-rows 显式给，flex-1 在 grid 容器里不生效 */}
      <DialogContent className="h-[80vh] max-w-4xl grid-rows-[auto_1fr] gap-0 overflow-hidden p-0">
        <DialogHeader className="border-b border-border/70 px-6 py-5">
          <DialogTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            使用说明
          </DialogTitle>
          <DialogDescription>第一次用的话，花两分钟看完「快速上手」就够。</DialogDescription>
        </DialogHeader>

        <div className="grid min-h-0 grid-cols-1 sm:grid-cols-[11rem_1fr]">
          <nav className="flex gap-1 overflow-x-auto border-b border-border/70 p-3 sm:flex-col sm:overflow-y-auto sm:border-b-0 sm:border-r">
            {sections.map((section) => (
              <button
                key={section.id}
                type="button"
                onClick={() => setActiveId(section.id)}
                className={cn(
                  "shrink-0 whitespace-nowrap rounded-lg px-3 py-2 text-left text-sm transition-colors",
                  section.id === activeId
                    ? "bg-muted font-medium text-foreground"
                    : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                )}
              >
                {section.label}
              </button>
            ))}
          </nav>

          <div className="min-h-0 overflow-y-auto px-6 py-5">
            <h3 className="mb-4 text-base font-semibold">{active.title}</h3>
            {active.body}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
