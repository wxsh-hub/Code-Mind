import { api } from "./api";

export interface Module {
  id: string;
  name: string;
  description?: string;
  createdBy?: string;
  createdAt?: string;
}

export interface Feature {
  id: string;
  featureCode: string;
  featureName: string;
  moduleName: string;
  description?: string;
  status?: string;
  createdAt?: string;
}

// 模块管理
export const getModules = async (): Promise<Module[]> => {
  return api.get<Module[], Module[]>("/modules");
};

export const getModule = async (name: string): Promise<Module> => {
  return api.get<Module, Module>(`/modules/${name}`);
};

export const createModule = async (data: {
  name: string;
  description?: string;
}): Promise<Module> => {
  return api.post<Module, Module>("/modules", data);
};

export const deleteModule = async (name: string): Promise<void> => {
  await api.delete(`/modules/${name}`);
};

// 功能管理
export const getFeatures = async (moduleName?: string): Promise<Feature[]> => {
  return api.get<Feature[], Feature[]>("/feature-metadata", {
    params: moduleName ? { module: moduleName } : undefined,
  });
};

export const getFeature = async (code: string): Promise<Feature> => {
  return api.get<Feature, Feature>(`/feature-metadata/${code}`);
};

export const createFeature = async (data: {
  featureCode: string;
  featureName: string;
  moduleName: string;
  description?: string;
}): Promise<Feature> => {
  return api.post<Feature, Feature>("/feature-metadata", data);
};

export const deleteFeature = async (code: string): Promise<void> => {
  await api.delete(`/feature-metadata/${code}`);
};
