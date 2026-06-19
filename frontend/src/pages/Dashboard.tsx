import {
    Activity,
    AlertTriangle,
    Bot,
    DollarSign,
    FileText,
    Lightbulb,
    Newspaper,
    Radio,
    Target,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Legend,
    Line,
    LineChart,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { useDashboardSocket } from "@/dashboard/hooks/useDashboardSocket";
import {
    alertRulesApi,
    alertsApi,
    competitorsApi,
    dashboardApi,
    factsApi,
    intelligenceItemsApi,
    intelligenceSourcesApi,
    topicsApi,
} from "@/services/api";
import type { AlertRule, DashboardStats, Fact, IntelligenceItem, UsageCostsResponse } from "@/types";

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#22c55e",
  negative: "#ef4444",
  neutral: "#6b7280",
};

const COST_COLORS = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"];

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 4,
  }).format(value);
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    topics: 0,
    competitors: 0,
    sources: 0,
    alert_rules: 0,
    open_alerts: 0,
    items: 0,
    facts: 0,
  });
  const [costs, setCosts] = useState<UsageCostsResponse | null>(null);
  const [latestItems, setLatestItems] = useState<IntelligenceItem[]>([]);
  const [latestFacts, setLatestFacts] = useState<Fact[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [sentimentData, setSentimentData] = useState<{ name: string; value: number }[]>([]);
  const [loading, setLoading] = useState(true);

  const { snapshot: liveSnapshot, connected } = useDashboardSocket();

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const [snapshotRes, topics, competitors, sources, alertRules, alertsRes, itemsRes, factsRes] =
          await Promise.all([
            dashboardApi.snapshot(),
            topicsApi.list(),
            competitorsApi.list(),
            intelligenceSourcesApi.list(),
            alertRulesApi.list(),
            alertsApi.list(),
            intelligenceItemsApi.list({ is_noise: false }),
            factsApi.list(),
          ]);

        const snapshot = snapshotRes.data;
        setStats(snapshot.stats);
        setCosts(snapshot.costs);

        const items: IntelligenceItem[] = itemsRes.data;
        const facts: Fact[] = factsRes.data;
        const rules: AlertRule[] = alertRules.data;
        const alertsList: any[] = alertsRes.data;

        // Override counts with the authoritative static snapshot so the UI is
        // consistent on first load; live updates take over afterwards.
        setStats({
          topics: topics.data.length,
          competitors: competitors.data.length,
          sources: sources.data.length,
          alert_rules: rules.length,
          open_alerts: alertsList.filter((a) => a.status === "open").length,
          items: items.length,
          facts: facts.length,
        });
        setLatestItems(items.slice(0, 5));
        setLatestFacts(facts.slice(0, 5));
        setAlerts(alertsList.slice(0, 5));

        const sentimentCounts: Record<string, number> = {};
        items.forEach((item) => {
          const key = item.sentiment || "neutral";
          sentimentCounts[key] = (sentimentCounts[key] || 0) + 1;
        });
        setSentimentData(
          Object.entries(sentimentCounts).map(([name, value]) => ({ name, value }))
        );
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  useEffect(() => {
    if (liveSnapshot) {
      setStats(liveSnapshot.stats);
      if (liveSnapshot.costs) {
        setCosts(liveSnapshot.costs);
      }
    }
  }, [liveSnapshot]);

  const costSummary = useMemo(() => {
    if (!costs) {
      return { total: 0, tokens: 0, dailyAverage: 0 };
    }
    const total = costs.daily.reduce((sum, d) => sum + d.total_cost, 0);
    const tokens = costs.daily.reduce((sum, d) => sum + d.total_tokens, 0);
    const dailyAverage = costs.daily.length ? total / costs.daily.length : 0;
    return { total, tokens, dailyAverage };
  }, [costs]);

  const statCards = [
    { title: "Topics", value: stats.topics, icon: Target },
    { title: "Competitors", value: stats.competitors, icon: Activity },
    { title: "Sources", value: stats.sources, icon: Radio },
    { title: "Alert Rules", value: stats.alert_rules, icon: AlertTriangle },
    { title: "Open Alerts", value: stats.open_alerts, icon: AlertTriangle },
    { title: "Intelligence Items", value: stats.items, icon: Newspaper },
    { title: "Facts", value: stats.facts, icon: Lightbulb },
  ];

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        Loading dashboard...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">
            Live overview of your market intelligence workspace
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div
            className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs ${
              connected
                ? "border-green-200 bg-green-50 text-green-700"
                : "border-muted-foreground/20 bg-muted text-muted-foreground"
            }`}
          >
            <span className={`h-2 w-2 rounded-full ${connected ? "bg-green-500" : "bg-gray-400"}`} />
            {connected ? "Live" : "Offline"}
          </div>
          <Button variant="outline" asChild>
            <a href="/ask">
              <Bot className="mr-2 h-4 w-4" />
              Ask Comrade
            </a>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{card.value}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Spend (30d)</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(costSummary.total)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tokens (30d)</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Intl.NumberFormat("en-US").format(costSummary.tokens)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Daily Average</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(costSummary.dailyAverage)}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Daily AI Costs</CardTitle>
            <CardDescription>Input, output, and total cost over the last 30 days</CardDescription>
          </CardHeader>
          <CardContent className="h-[260px]">
            {costs && costs.daily.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={costs.daily} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  <Legend />
                  <Line type="monotone" dataKey="input_cost" name="Input" stroke="#3b82f6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="output_cost" name="Output" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="total_cost" name="Total" stroke="#10b981" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground">No cost data yet.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cost by Provider</CardTitle>
            <CardDescription>Total spend per AI provider over the last 30 days</CardDescription>
          </CardHeader>
          <CardContent className="h-[260px]">
            {costs && costs.by_provider.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={costs.by_provider} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="provider_type" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  <Bar dataKey="total_cost" name="Total cost">
                    {costs.by_provider.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COST_COLORS[index % COST_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground">No provider cost data yet.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Newspaper className="h-5 w-5 text-primary" />
              Latest Intelligence
            </CardTitle>
            <CardDescription>Recent curated items from your newsfeed</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {latestItems.map((item) => (
              <div key={item.id} className="rounded-md border p-3">
                <p className="text-sm font-medium line-clamp-1">{item.title}</p>
                <p className="text-xs text-muted-foreground">
                  {item.source_name || item.item_type} · {item.sentiment || "neutral"} ·{" "}
                  {new Date(item.fetched_at).toLocaleDateString()}
                </p>
              </div>
            ))}
            {latestItems.length === 0 && (
              <p className="text-sm text-muted-foreground">No intelligence items yet.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-primary" />
              Latest Facts
            </CardTitle>
            <CardDescription>Recently extracted structured facts</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {latestFacts.map((fact) => (
              <div key={fact.id} className="rounded-md border p-3">
                <p className="text-sm font-medium line-clamp-1">{fact.title}</p>
                <p className="text-xs text-muted-foreground">
                  {fact.fact_type} · {fact.confidence || "medium"} ·{" "}
                  {new Date(fact.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
            {latestFacts.length === 0 && (
              <p className="text-sm text-muted-foreground">No facts extracted yet.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-primary" />
              Recent Alerts
            </CardTitle>
            <CardDescription>Latest triggered alert rules</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {alerts.map((alert) => (
              <div key={alert.id} className="rounded-md border p-3">
                <p className="text-sm font-medium">{alert.title}</p>
                <p className="text-xs text-muted-foreground">
                  {alert.severity} · {alert.status} ·{" "}
                  {new Date(alert.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
            {alerts.length === 0 && (
              <p className="text-sm text-muted-foreground">No alerts yet.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Sentiment Distribution
            </CardTitle>
            <CardDescription>Across curated intelligence items</CardDescription>
          </CardHeader>
          <CardContent className="h-[220px]">
            {sentimentData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sentimentData}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={80}
                    label
                  >
                    {sentimentData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={SENTIMENT_COLORS[entry.name] || "#8884d8"}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground">No sentiment data yet.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
