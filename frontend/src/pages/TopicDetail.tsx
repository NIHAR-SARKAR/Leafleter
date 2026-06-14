import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Play, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

import { topicsApi } from "@/services/api";
import type { Topic } from "@/types";

export function TopicDetail() {
  const { id } = useParams<{ id: string }>();
  const [topic, setTopic] = useState<Topic | null>(null);
  const [runs, setRuns] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [engine, setEngine] = useState("serpapi");

  const fetchTopic = async () => {
    const { data } = await topicsApi.get(Number(id));
    setTopic(data);
  };

  const fetchRuns = async () => {
    const { data } = await topicsApi.runs(Number(id));
    setRuns(data);
  };

  useEffect(() => {
    fetchTopic();
    fetchRuns();
  }, [id]);

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault();
    await topicsApi.addSource(Number(id), {
      source_type: "search",
      name: `Search: ${query}`,
      query,
      platform: engine,
    });
    setQuery("");
    fetchTopic();
  };

  const handleAnalyze = async () => {
    await topicsApi.analyze(Number(id), { analysis_types: ["sentiment", "trends"] });
    fetchRuns();
  };

  if (!topic) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{topic.name}</h2>
        <p className="text-muted-foreground">{topic.description}</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddSource} className="mb-4 flex gap-2">
              <Input
                placeholder="Search query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                required
              />
              <Input
                placeholder="Engine"
                value={engine}
                onChange={(e) => setEngine(e.target.value)}
                className="w-32"
              />
              <Button type="submit">
                <Plus className="mr-2 h-4 w-4" />
                Add
              </Button>
            </form>
            <div className="space-y-2">
              {topic.sources?.map((source) => (
                <div
                  key={source.id}
                  className="rounded-md border p-3 text-sm"
                >
                  <div className="font-medium">{source.name}</div>
                  <div className="text-muted-foreground">
                    {source.source_type} • {source.fetch_status}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Analysis</CardTitle>
            <CardDescription>Run AI analysis on this topic</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={handleAnalyze} className="w-full">
              <Play className="mr-2 h-4 w-4" />
              Run Analysis
            </Button>
            <div className="mt-4 space-y-2">
              {runs.map((run) => (
                <div key={run.id} className="rounded-md border p-2 text-sm">
                  <div className="font-medium">{run.analysis_type}</div>
                  <div className="text-muted-foreground">{run.status}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
