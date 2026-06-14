import { useEffect, useState } from "react";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { alertRulesApi } from "@/services/api";
import type { AlertRule } from "@/types";

export function AlertRules() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [name, setName] = useState("");
  const [metric, setMetric] = useState("sentiment");
  const [condition, setCondition] = useState("lt");
  const [threshold, setThreshold] = useState("50");

  const fetchRules = async () => {
    const { data } = await alertRulesApi.list();
    setRules(data);
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await alertRulesApi.create({
      name,
      entity_type: "topic",
      condition,
      threshold: Number(threshold),
      metric,
      notification_channels: "email",
    });
    setName("");
    fetchRules();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Alert Rules</h2>
        <p className="text-muted-foreground">Monitor metrics and get notified</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Create Alert Rule</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="flex gap-4">
            <Input
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <Select value={metric} onValueChange={setMetric}>
              <SelectTrigger className="w-[160px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sentiment">Sentiment</SelectItem>
                <SelectItem value="reputation">Reputation</SelectItem>
                <SelectItem value="trends">Trends</SelectItem>
              </SelectContent>
            </Select>
            <Select value={condition} onValueChange={setCondition}>
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="lt">&lt;</SelectItem>
                <SelectItem value="gt">&gt;</SelectItem>
                <SelectItem value="eq">=</SelectItem>
              </SelectContent>
            </Select>
            <Input
              type="number"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              className="w-24"
            />
            <Button type="submit">
              <Plus className="mr-2 h-4 w-4" />
              Create
            </Button>
          </form>
        </CardContent>
      </Card>
      <div className="grid gap-4">
        {rules.map((rule) => (
          <Card key={rule.id}>
            <CardHeader>
              <CardTitle>{rule.name}</CardTitle>
              <CardDescription>
                {rule.metric} {rule.condition} {rule.threshold} •{" "}
                {rule.is_active ? "Active" : "Inactive"}
              </CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  );
}
