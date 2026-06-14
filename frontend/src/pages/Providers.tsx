import { Plus, TestTube } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { providersApi } from "@/services/api";
import type { AzureProviderConfig, Provider } from "@/types";
import { toast } from 'react-hot-toast';

const AZURE_API_PATTERNS: {
  value: AzureProviderConfig["api_pattern"];
  label: string;
}[] = [
  { value: "azure_openai_legacy", label: "Legacy (deployment-specific)" },
  { value: "azure_openai_v1", label: "OpenAI v1" },
  { value: "azure_responses", label: "Responses API" },
  { value: "azure_ai_foundry", label: "Azure AI Foundry" },
];

const REASONING_EFFORTS: { value: AzureProviderConfig["reasoning_effort"]; label: string }[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

const VERBOSITY_LEVELS: { value: AzureProviderConfig["verbosity"]; label: string }[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

export function Providers() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [types, setTypes] = useState<string[]>([]);

  // Common fields
  const [name, setName] = useState("");
  const [providerType, setProviderType] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [apiBase, setApiBase] = useState("");
  const [apiVersion, setApiVersion] = useState("");
  const [region, setRegion] = useState("");

  // Azure-specific config fields
  const [deployment, setDeployment] = useState("");
  const [apiPattern, setApiPattern] = useState<AzureProviderConfig["api_pattern"]>(undefined);
  const [useResponsesApi, setUseResponsesApi] = useState<boolean | undefined>(undefined);
  const [modelName, setModelName] = useState("");
  const [responsesApiVersion, setResponsesApiVersion] = useState("");
  const [v1ApiVersion, setV1ApiVersion] = useState("");
  const [reasoningEffort, setReasoningEffort] = useState<AzureProviderConfig["reasoning_effort"]>(undefined);
  const [verbosity, setVerbosity] = useState<AzureProviderConfig["verbosity"]>(undefined);

  const isAzure = providerType === "azure_openai";

  const fetchProviders = async () => {
    const { data } = await providersApi.list();
    setProviders(Array.isArray(data) ? data : []);
  };

  useEffect(() => {
    fetchProviders();
    providersApi.types().then(({ data }) => setTypes(data));
  }, []);

  const resetForm = () => {
    setName("");
    setProviderType("");
    setApiKey("");
    setApiBase("");
    setApiVersion("");
    setRegion("");
    setDeployment("");
    setApiPattern(undefined);
    setUseResponsesApi(undefined);
    setModelName("");
    setResponsesApiVersion("");
    setV1ApiVersion("");
    setReasoningEffort(undefined);
    setVerbosity(undefined);
  };

  const buildConfig = (): Record<string, unknown> | undefined => {
    if (!isAzure) return undefined;

    const config: Record<string, unknown> = {};
    if (deployment.trim()) config.deployment = deployment.trim();
    if (apiPattern) config.api_pattern = apiPattern;
    if (useResponsesApi !== undefined) config.use_responses_api = useResponsesApi;
    if (modelName.trim()) config.model_name = modelName.trim();
    if (responsesApiVersion.trim()) config.responses_api_version = responsesApiVersion.trim();
    if (v1ApiVersion.trim()) config.v1_api_version = v1ApiVersion.trim();
    if (reasoningEffort) config.reasoning_effort = reasoningEffort;
    if (verbosity) config.verbosity = verbosity;

    return Object.keys(config).length > 0 ? config : undefined;
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await providersApi.create({
      name,
      provider_type: providerType,
      api_key: apiKey || undefined,
      api_base: apiBase || undefined,
      api_version: apiVersion || undefined,
      region: region || undefined,
      config: buildConfig(),
      models: [],
    });
    resetForm();
    fetchProviders();
  };

  const handleTest = async (id: number) => {
    try {
      const { data } = await providersApi.test(id);
      data.success ? toast.success(`✔ Connection successful`): toast.error("Connection test failed !");
    } catch (error) {
      toast.error("Connection test failed");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">AI Providers</h2>
        <p className="text-muted-foreground">Manage your AI provider connections</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Add Provider</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  placeholder="Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="type">Type</Label>
                <Select value={providerType} onValueChange={setProviderType} required>
                  <SelectTrigger id="type">
                    <SelectValue placeholder="Type" />
                  </SelectTrigger>
                  <SelectContent>
                    {types.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="api_key">API Key</Label>
                <Input
                  id="api_key"
                  type="password"
                  placeholder="API Key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="api_base">Endpoint (API Base)</Label>
                <Input
                  id="api_base"
                  placeholder="https://..."
                  value={apiBase}
                  onChange={(e) => setApiBase(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="api_version">API Version</Label>
                <Input
                  id="api_version"
                  placeholder="2024-12-01-preview"
                  value={apiVersion}
                  onChange={(e) => setApiVersion(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="region">Region</Label>
                <Input
                  id="region"
                  placeholder="Region"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                />
              </div>
            </div>

            {isAzure && (
              <div className="rounded-md border p-4 space-y-4">
                <h4 className="text-sm font-semibold">Azure OpenAI Settings</h4>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="deployment">Deployment / Model</Label>
                    <Input
                      id="deployment"
                      placeholder="gpt-4o"
                      value={deployment}
                      onChange={(e) => setDeployment(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="api_pattern">API Pattern</Label>
                    <Select
                      value={apiPattern}
                      onValueChange={(value) => setApiPattern(value as AzureProviderConfig["api_pattern"])}
                    >
                      <SelectTrigger id="api_pattern">
                        <SelectValue placeholder="Auto-detect" />
                      </SelectTrigger>
                      <SelectContent>
                        {AZURE_API_PATTERNS.map((p) => (
                          <SelectItem key={p.value} value={p.value!}>
                            {p.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="model_name">Model Name (in body)</Label>
                    <Input
                      id="model_name"
                      placeholder="gpt-4o"
                      value={modelName}
                      onChange={(e) => setModelName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="use_responses_api">Use Responses API</Label>
                    <Select
                      value={useResponsesApi === undefined ? "auto" : String(useResponsesApi)}
                      onValueChange={(value) =>
                        setUseResponsesApi(value === "auto" ? undefined : value === "true")
                      }
                    >
                      <SelectTrigger id="use_responses_api">
                        <SelectValue placeholder="Auto" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="auto">Auto</SelectItem>
                        <SelectItem value="true">Yes</SelectItem>
                        <SelectItem value="false">No</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="responses_api_version">Responses API Version</Label>
                    <Input
                      id="responses_api_version"
                      placeholder="2025-04-01-preview"
                      value={responsesApiVersion}
                      onChange={(e) => setResponsesApiVersion(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="v1_api_version">V1 API Version</Label>
                    <Input
                      id="v1_api_version"
                      placeholder="2024-12-01-preview"
                      value={v1ApiVersion}
                      onChange={(e) => setV1ApiVersion(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reasoning_effort">Reasoning Effort</Label>
                    <Select
                      value={reasoningEffort || "default"}
                      onValueChange={(value) =>
                        setReasoningEffort(
                          value === "default" ? undefined : (value as AzureProviderConfig["reasoning_effort"])
                        )
                      }
                    >
                      <SelectTrigger id="reasoning_effort">
                        <SelectValue placeholder="Default" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="default">Default</SelectItem>
                        {REASONING_EFFORTS.map((r) => (
                          <SelectItem key={r.value} value={r.value!}>
                            {r.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="verbosity">Verbosity</Label>
                    <Select
                      value={verbosity || "default"}
                      onValueChange={(value) =>
                        setVerbosity(
                          value === "default" ? undefined : (value as AzureProviderConfig["verbosity"])
                        )
                      }
                    >
                      <SelectTrigger id="verbosity">
                        <SelectValue placeholder="Default" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="default">Default</SelectItem>
                        {VERBOSITY_LEVELS.map((v) => (
                          <SelectItem key={v.value} value={v.value!}>
                            {v.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            )}

            <Button type="submit">
              <Plus className="mr-2 h-4 w-4" />
              Add
            </Button>
          </form>
        </CardContent>
      </Card>
      <div className="grid gap-4">
        {providers.map((provider) => (
          <Card key={provider.id}>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>{provider.name}</CardTitle>
                <CardDescription>{provider.provider_type}</CardDescription>
              </div>
              <Button size="sm" variant="outline" onClick={() => handleTest(provider.id)}>
                <TestTube className="mr-2 h-4 w-4" />
                Test
              </Button>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                {(provider.models ?? []).length} models •{" "}
                {provider.is_active ? "Active" : "Inactive"}
                {provider.api_base && ` • ${provider.api_base}`}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
