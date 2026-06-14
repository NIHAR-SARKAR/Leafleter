import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { topicsApi, providersApi, reportsApi, alertRulesApi } from "@/services/api";

export function Dashboard() {
  const [stats, setStats] = useState({
    topics: 0,
    providers: 0,
    reports: 0,
    alertRules: 0,
  });
  const [usage, setUsage] = useState<{ name: string; cost: number }[]>([]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [topics, providers, reports, alertRules] = await Promise.all([
          topicsApi.list(),
          providersApi.list(),
          reportsApi.list(),
          alertRulesApi.list(),
        ]);
        setStats({
          topics: topics.data.length,
          providers: providers.data.length,
          reports: reports.data.length,
          alertRules: alertRules.data.length,
        });
        setUsage([
          { name: "OpenAI", cost: 12.5 },
          { name: "Claude", cost: 8.2 },
          { name: "Gemini", cost: 3.1 },
        ]);
      } catch (error) {
        console.error(error);
      }
    };
    fetchStats();
  }, []);

  const statCards = [
    { title: "Topics", value: stats.topics },
    { title: "Providers", value: stats.providers },
    { title: "Reports", value: stats.reports },
    { title: "Alert Rules", value: stats.alertRules },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Overview of your market intelligence workspace
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => (
          <Card key={card.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{card.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>AI Usage Cost</CardTitle>
            <CardDescription>Estimated spend by provider</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={usage}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="cost" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest actions in your workspace</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Activity feed will be populated as you use the platform.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
