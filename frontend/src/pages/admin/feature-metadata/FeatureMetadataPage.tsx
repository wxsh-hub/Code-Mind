import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
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
  getFeatures,
  createFeature,
  deleteFeature,
  Module,
  Feature,
} from "@/services/moduleService";

export function FeatureMetadataPage() {
  const [modules, setModules] = useState<Module[]>([]);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
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
      toast.error("加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 创建功能
  const handleCreate = async () => {
    if (!newFeature.featureCode.trim() || !newFeature.featureName.trim()) {
      toast.error("功能编号和名称不能为空");
      return;
    }

    try {
      await createFeature(newFeature);
      toast.success(`功能 ${newFeature.featureName} 已创建`);
      setCreateOpen(false);
      setNewFeature({ featureCode: "", featureName: "", moduleName: "", description: "" });
      loadData();
    } catch (error) {
      toast.error("创建功能失败");
    }
  };

  // 删除功能
  const handleDelete = async (code: string) => {
    if (!confirm(`确定要删除功能 ${code} 吗？`)) return;

    try {
      await deleteFeature(code);
      toast.success(`功能 ${code} 已删除`);
      loadData();
    } catch (error) {
      toast.error("删除功能失败");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">功能元数据标记</h1>
        <Button onClick={() => setCreateOpen(true)}>+ 新建功能</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>功能列表</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-4">加载中...</div>
          ) : features.length === 0 ? (
            <div className="text-center py-4 text-muted-foreground">
              暂无功能，点击右上角创建
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>功能编号</TableHead>
                  <TableHead>功能名称</TableHead>
                  <TableHead>所属模块</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {features.map((feat) => (
                  <TableRow key={feat.id}>
                    <TableCell className="font-mono font-medium">
                      {feat.featureCode}
                    </TableCell>
                    <TableCell>{feat.featureName}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{feat.moduleName}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {feat.description || "-"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={feat.status === "active" ? "default" : "secondary"}>
                        {feat.status || "active"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-500"
                        onClick={() => handleDelete(feat.featureCode)}
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

      {/* 创建对话框 */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建功能</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>功能编号</Label>
              <Input
                value={newFeature.featureCode}
                onChange={(e) => setNewFeature({ ...newFeature, featureCode: e.target.value })}
                placeholder="如：F001"
              />
            </div>
            <div>
              <Label>功能名称</Label>
              <Input
                value={newFeature.featureName}
                onChange={(e) => setNewFeature({ ...newFeature, featureName: e.target.value })}
                placeholder="请输入功能名称"
              />
            </div>
            <div>
              <Label>所属模块</Label>
              <select
                className="w-full p-2 border rounded"
                value={newFeature.moduleName}
                onChange={(e) => setNewFeature({ ...newFeature, moduleName: e.target.value })}
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
                onChange={(e) => setNewFeature({ ...newFeature, description: e.target.value })}
                placeholder="请输入功能描述"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              取消
            </Button>
            <Button onClick={handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
