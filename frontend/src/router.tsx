import * as React from "react";
import { Navigate, createBrowserRouter } from "react-router-dom";

import { Loading } from "@/components/common/Loading";
import { useAuthStore } from "@/stores/authStore";

/**
 * 把命名导出的页面包装成可懒加载组件。
 *
 * 此前所有页面都是顶部静态 import，导致打开登录页也要先下载整包
 * （含 @antv/g6、recharts、代码高亮、Markdown 渲染等只在个别页面用到的依赖），
 * 首屏 3.5MB。改为按路由切分后，登录页只需加载自己那一小片。
 */
function lazyPage<T extends Record<string, unknown>>(
  loader: () => Promise<T>,
  name: keyof T
) {
  return React.lazy(() =>
    loader().then((module) => ({
      default: module[name] as React.ComponentType
    }))
  );
}

const LoginPage = lazyPage(() => import("@/pages/LoginPage"), "LoginPage");
const EngineGate = lazyPage(() => import("@/components/common/EngineGate"), "EngineGate");
const ChangeLogsPage = lazyPage(() => import("@/pages/ChangeLogsPage"), "ChangeLogsPage");
const DocPreviewPage = lazyPage(() => import("@/pages/DocPreviewPage"), "DocPreviewPage");
const NotFoundPage = lazyPage(() => import("@/pages/NotFoundPage"), "NotFoundPage");
const AdminLayout = lazyPage(() => import("@/pages/admin/AdminLayout"), "AdminLayout");
const DashboardPage = lazyPage(() => import("@/pages/admin/dashboard/DashboardPage"), "DashboardPage");
const KnowledgeListPage = lazyPage(
  () => import("@/pages/admin/knowledge/KnowledgeListPage"),
  "KnowledgeListPage"
);
const KnowledgeDocumentsPage = lazyPage(
  () => import("@/pages/admin/knowledge/KnowledgeDocumentsPage"),
  "KnowledgeDocumentsPage"
);
const KnowledgeChunksPage = lazyPage(
  () => import("@/pages/admin/knowledge/KnowledgeChunksPage"),
  "KnowledgeChunksPage"
);
const KnowledgeGraphPage = lazyPage(
  () => import("@/pages/admin/knowledge-graph/KnowledgeGraphPage"),
  "KnowledgeGraphPage"
);
const BizChangeLogPage = lazyPage(
  () => import("@/pages/admin/change-logs/BizChangeLogPage"),
  "BizChangeLogPage"
);
const IntentTreePage = lazyPage(
  () => import("@/pages/admin/intent-tree/IntentTreePage"),
  "IntentTreePage"
);
const IntentListPage = lazyPage(
  () => import("@/pages/admin/intent-tree/IntentListPage"),
  "IntentListPage"
);
const IntentEditPage = lazyPage(
  () => import("@/pages/admin/intent-tree/IntentEditPage"),
  "IntentEditPage"
);
const RagTracePage = lazyPage(() => import("@/pages/admin/traces/RagTracePage"), "RagTracePage");
const RagTraceDetailPage = lazyPage(
  () => import("@/pages/admin/traces/RagTraceDetailPage"),
  "RagTraceDetailPage"
);
const SystemSettingsPage = lazyPage(
  () => import("@/pages/admin/settings/SystemSettingsPage"),
  "SystemSettingsPage"
);
const SampleQuestionPage = lazyPage(
  () => import("@/pages/admin/sample-questions/SampleQuestionPage"),
  "SampleQuestionPage"
);
const QueryTermMappingPage = lazyPage(
  () => import("@/pages/admin/query-term-mapping/QueryTermMappingPage"),
  "QueryTermMappingPage"
);
const AgentProfilePage = lazyPage(
  () => import("@/pages/admin/agents/AgentProfilePage"),
  "AgentProfilePage"
);
const AgentPromptPage = lazyPage(() => import("@/pages/admin/agents/AgentPromptPage"), "AgentPromptPage");
const UserListPage = lazyPage(() => import("@/pages/admin/users/UserListPage"), "UserListPage");
const ConflictReviewPage = lazyPage(
  () => import("@/pages/admin/conflict-review/ConflictReviewPage"),
  "ConflictReviewPage"
);
const ModuleManagementPage = lazyPage(
  () => import("@/pages/admin/modules/ModuleManagementPage"),
  "ModuleManagementPage"
);
const FeatureMetadataPage = lazyPage(
  () => import("@/pages/admin/feature-metadata/FeatureMetadataPage"),
  "FeatureMetadataPage"
);

/** 全屏加载态：懒加载分片抵达前的占位 */
function PageLoading() {
  return (
    <div className="flex h-screen items-center justify-center bg-white">
      <Loading />
    </div>
  );
}

/**
 * 包裹懒加载页面
 *
 * Suspense 放在每个路由元素内而非路由根：切到子路由时不至于把整棵已渲染的
 * 树换回加载态，仅替换待加载的那一段。
 */
function Page({ children }: { children: React.ReactNode }) {
  return <React.Suspense fallback={<PageLoading />}>{children}</React.Suspense>;
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role !== "admin") {
    return <Navigate to="/chat" replace />;
  }

  return <>{children}</>;
}

function RedirectIfAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }
  return <>{children}</>;
}

function HomeRedirect() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return <Navigate to={isAuthenticated ? "/chat" : "/login"} replace />;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <HomeRedirect />
  },
  {
    path: "/login",
    element: (
      <RedirectIfAuth>
        <Page>
          <LoginPage />
        </Page>
      </RedirectIfAuth>
    )
  },
  {
    path: "/chat",
    element: (
      <RequireAuth>
        <Page>
          <EngineGate />
        </Page>
      </RequireAuth>
    )
  },
  {
    path: "/chat/:sessionId",
    element: (
      <RequireAuth>
        <Page>
          <EngineGate />
        </Page>
      </RequireAuth>
    )
  },
  {
    path: "/change-logs",
    element: (
      <RequireAuth>
        <Page>
          <ChangeLogsPage />
        </Page>
      </RequireAuth>
    )
  },
  {
    path: "/preview/doc/:docId",
    element: (
      <RequireAuth>
        <Page>
          <DocPreviewPage />
        </Page>
      </RequireAuth>
    )
  },
  {
    path: "/admin",
    element: (
      <RequireAdmin>
        <Page>
          <AdminLayout />
        </Page>
      </RequireAdmin>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/admin/dashboard" replace />
      },
      {
        path: "dashboard",
        element: (
          <Page>
            <DashboardPage />
          </Page>
        )
      },
      {
        path: "knowledge",
        element: (
          <Page>
            <KnowledgeListPage />
          </Page>
        )
      },
      {
        path: "knowledge/:kbId",
        element: (
          <Page>
            <KnowledgeDocumentsPage />
          </Page>
        )
      },
      {
        path: "knowledge/:kbId/docs/:docId",
        element: (
          <Page>
            <KnowledgeChunksPage />
          </Page>
        )
      },
      {
        path: "knowledge-graph",
        element: (
          <Page>
            <KnowledgeGraphPage />
          </Page>
        )
      },
      {
        path: "intent-tree",
        element: (
          <Page>
            <IntentTreePage />
          </Page>
        )
      },
      {
        path: "intent-list",
        element: (
          <Page>
            <IntentListPage />
          </Page>
        )
      },
      {
        path: "intent-list/:id/edit",
        element: (
          <Page>
            <IntentEditPage />
          </Page>
        )
      },
      {
        path: "traces",
        element: (
          <Page>
            <RagTracePage />
          </Page>
        )
      },
      {
        path: "traces/:traceId",
        element: (
          <Page>
            <RagTraceDetailPage />
          </Page>
        )
      },
      {
        path: "change-logs",
        element: (
          <Page>
            <BizChangeLogPage />
          </Page>
        )
      },
      {
        path: "settings",
        element: (
          <Page>
            <SystemSettingsPage />
          </Page>
        )
      },
      {
        path: "sample-questions",
        element: (
          <Page>
            <SampleQuestionPage />
          </Page>
        )
      },
      {
        path: "mappings",
        element: (
          <Page>
            <QueryTermMappingPage />
          </Page>
        )
      },
      {
        path: "agents",
        element: (
          <Page>
            <AgentProfilePage />
          </Page>
        )
      },
      {
        path: "agents/:agentId",
        element: (
          <Page>
            <AgentPromptPage />
          </Page>
        )
      },
      {
        path: "users",
        element: (
          <Page>
            <UserListPage />
          </Page>
        )
      },
      {
        path: "conflict-review",
        element: (
          <Page>
            <ConflictReviewPage />
          </Page>
        )
      },
      {
        path: "modules",
        element: (
          <Page>
            <ModuleManagementPage />
          </Page>
        )
      },
      {
        path: "feature-metadata",
        element: (
          <Page>
            <FeatureMetadataPage />
          </Page>
        )
      }
    ]
  },
  {
    path: "*",
    element: (
      <Page>
        <NotFoundPage />
      </Page>
    )
  }
]);
