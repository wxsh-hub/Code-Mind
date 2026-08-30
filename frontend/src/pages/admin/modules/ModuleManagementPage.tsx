import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { toast } from "sonner";
import {
  getModules,
  createModule,
  deleteModule,
  getFeatures,
  createFeature,
  deleteFeature,
  Module,
  Feature,
} from "@/services/moduleService";

export function ModuleManagementPage() {
  const [modules, setModules] = useState<Module[]>([]);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModuleOpen, setCreateModuleOpen] = useState(false);
  const [createFeatureOpen, setCreateFeatureOpen] = useState(false);
  const [newModule, setNewModule] = useState({ name: "", description: "" });
  const [newFeature, setNewFeature] = useState({
    featureCode: "",
    featureName: "",
    moduleName: "",
    description: "",
  });

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const [modulesData, featuresData] = await Promise.all([
        getModules(),
        getFeatures(),
      ]);
      setModules(modulesData || []);
      setFeatures(featuresData || []);
    } catch (error) {
      toast.error("无法加载模块和功能数据");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 创建模块
  const handleCreateModule = async () => {
    if (!newModule.name.trim()) {
      toast.error("模块名称不能为空");
      return;
    }

    try {
      await createModule(newModule);
      toast.success(`模块 ${newModule.name} 已创建`);
      setCreateModuleOpen(false);
      setNewModule({ name: "", description: "" });
      loadData();
    } catch (error) {
      toast.error("创建模块失败，请重试");
    }
  };

  // 删除模块
  const handleDeleteModule = async (name: string) => {
    if (!confirm(`确定要删除模块 ${name} 吗？相关的功能和向量也会被删除。`)) {
      return;
    }

    try {
      await deleteModule(name);
      toast.success(`模块 ${name} 已删除`);
      loadData();
    } catch (error) {
      toast.error("删除模块失败，请重试");
    }
  };

  // 创建功能
  const handleCreateFeature = async () => {
    if (!newFeature.featureCode.trim() || !newFeature.featureName.trim()) {
      toast.error("功能编号和名称不能为空");
      return;
    }

    try {
      await createFeature(newFeature);
      toast.success(`功能 ${newFeature.featureName} 已创建`);
      setCreateFeatureOpen(false);
      setNewFeature({
        featureCode: "",
        featureName: "",
        moduleName: "",
        description: "",
      });
      loadData();
    } catch (error) {
      toast.error("创建功能失败，请重试");
    }
  };

  // 删除功能
  const handleDeleteFeature = async (code: string) => {
    if (!confirm(`确定要删除功能 ${code} 吗？相关的向量也会被删除。`)) {
      return;
    }

    try {
      await deleteFeature(code);
      toast.success(`功能 ${code} 已删除`);
      loadData();
    } catch (error) {
      toast.error("删除功能失败，请重试");
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">模块管理</h1>

      <Tabs defaultValue="modules">
        <TabsList>
          <TabsTrigger value="modules">模块列表</TabsTrigger>
          <TabsTrigger value="features">功能列表</TabsTrigger>
        </TabsList>

        {/* 模块列表 */}
        <TabsContent value="modules">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>模块列表</CardTitle>
                <Button onClick={() => setCreateModuleOpen(true)}>
                  + 新建模块
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-4">加载中...</div>
              ) : modules.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground">
                  暂无模块
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>模块名称</TableHead>
                      <TableHead>描述</TableHead>
                      <TableHead>创建时间</TableHead>
                      <TableHead>操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {modules.map((mod) => (
                      <TableRow key={mod.id}>
                        <TableCell className="font-medium">{mod.name}</TableCell>
                        <TableCell>{mod.description || "-"}</TableCell>
                        <TableCell>{mod.createdAt || "-"}</TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-500"
                            onClick={() => handleDeleteModule(mod.name)}
                          >
                            删除
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 功能列表 */}
        <TabsContent value="features">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>功能列表</CardTitle>
                <Button onClick={() => setCreateFeatureOpen(true)}>
                  + 新建功能
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-4">加载中...</div>
              ) : features.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground">
                  暂无功能
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>功能编号</TableHead>
                      <TableHead>功能名称</TableHead>
                      <TableHead>所属模块</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {features.map((feat) => (
                      <TableRow key={feat.id}>
                        <TableCell className="font-medium">
                          {feat.featureCode}
                        </TableCell>
                        <TableCell>{feat.featureName}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{feat.moduleName}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              feat.status === "active" ? "default" : "secondary"
                            }
                          >
                            {feat.status || "active"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-500"
                            onClick={() => handleDeleteFeature(feat.featureCode)}
                          >
                            删除
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 创建模块对话框 */}
      <Dialog open={createModuleOpen} onOpenChange={setCreateModuleOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建模块</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>模块名称</Label>
              <Input
                value={newModule.name}
                onChange={(e) =>
                  setNewModule({ ...newModule, name: e.target.value })
                }
                placeholder="请输入模块名称"
              />
            </div>
            <div>
              <Label>描述</Label>
              <Input
                value={newModule.description}
                onChange={(e) =>
                  setNewModule({ ...newModule, description: e.target.value })
                }
                placeholder="请输入模块描述"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateModuleOpen(false)}>
              取消
            </Button>
            <Button onClick={handleCreateModule}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 创建功能对话框 */}
      <Dialog open={createFeatureOpen} onOpenChange={setCreateFeatureOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建功能</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>功能编号</Label>
              <Input
                value={newFeature.featureCode}
                onChange={(e) =>
                  setNewFeature({ ...newFeature, featureCode: e.target.value })
                }
                placeholder="如：F001"
              />
            </div>
            <div>
              <Label>功能名称</Label>
              <Input
                value={newFeature.featureName}
                onChange={(e) =>
                  setNewFeature({ ...newFeature, featureName: e.target.value })
                }
                placeholder="请输入功能名称"
              />
            </div>
            <div>
              <Label>所属模块</Label>
              <select
                className="w-full p-2 border rounded"
                value={newFeature.moduleName}
                onChange={(e) =>
                  setNewFeature({ ...newFeature, moduleName: e.target.value })
                }
              >
                <option value="">请选择模块</option>
                {modules.map((mod) => (
                  <option key={mod.name} value={mod.name}>
                    {mod.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>描述</Label>
              <Input
                value={newFeature.description}
                onChange={(e) =>
                  setNewFeature({ ...newFeature, description: e.target.value })
                }
                placeholder="请输入功能描述"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCreateFeatureOpen(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreateFeature}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
