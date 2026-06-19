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
import { competitorsApi, schedulesApi, topicsApi } from "@/services/api";
import type { Competitor, Schedule, Topic } from "@/types";

const COMPETITOR_JOB_TYPES = ["competitor_snapshot", "competitor_feature_monitor"];

export function Schedules() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [name, setName] = useState("");
  const [jobType, setJobType] = useState("re_analysis");
  const [cron, setCron] = useState("0 9 * * *");
  const [topicId, setTopicId] = useState("");
  const [competitorId, setCompetitorId] = useState("");

  const fetchSchedules = async () => {
    const { data } = await schedulesApi.list();
    setSchedules(data);
  };

  useEffect(() => {
    fetchSchedules();
    topicsApi.list().then(({ data }) => setTopics(data));
    competitorsApi.list().then(({ data }) => setCompetitors(data));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const configuration: Record<string, unknown> = { user_id: 1 };
    if (COMPETITOR_JOB_TYPES.includes(jobType)) {
      configuration.competitor_id = competitorId ? Number(competitorId) : undefined;
    }
    await schedulesApi.create({
      name,
      job_type: jobType,
      cron_expression: cron,
      topic_id: topicId ? Number(topicId) : undefined,
      configuration,
    });
    setName("");
    setCompetitorId("");
    fetchSchedules();
  };

  const isCompetitorJob = COMPETITOR_JOB_TYPES.includes(jobType);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Schedules</h2>
        <p className="text-muted-foreground">Automate recurring tasks</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Create Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="flex flex-col gap-4 sm:flex-row">
            <Input
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <Select value={jobType} onValueChange={setJobType}>
              <SelectTrigger className="w-[220px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="re_analysis">Re-analysis</SelectItem>
                <SelectItem value="report_generation">Report</SelectItem>
                <SelectItem value="brand_monitor">Brand Monitor</SelectItem>
                <SelectItem value="competitor_snapshot">
                  Competitor Snapshot
                </SelectItem>
                <SelectItem value="competitor_feature_monitor">
                  Competitor Feature Monitor
                </SelectItem>
                <SelectItem value="intelligence_ingestion">
                  Intelligence Ingestion
                </SelectItem>
              </SelectContent>
            </Select>
            <Input
              placeholder="Cron"
              value={cron}
              onChange={(e) => setCron(e.target.value)}
              className="sm:w-40"
            />
            {!isCompetitorJob && (
              <Select value={topicId} onValueChange={setTopicId}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Topic" />
                </SelectTrigger>
                <SelectContent>
                  {topics.map((t) => (
                    <SelectItem key={t.id} value={String(t.id)}>
                      {t.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {isCompetitorJob && (
              <Select value={competitorId} onValueChange={setCompetitorId}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Competitor" />
                </SelectTrigger>
                <SelectContent>
                  {competitors.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <Button type="submit">
              <Plus className="mr-2 h-4 w-4" />
              Create
            </Button>
          </form>
        </CardContent>
      </Card>
      <div className="grid gap-4">
        {schedules.map((schedule) => (
          <Card key={schedule.id}>
            <CardHeader>
              <CardTitle>{schedule.name}</CardTitle>
              <CardDescription>
                {schedule.job_type} • {schedule.cron_expression} •{" "}
                {schedule.is_active ? "Active" : "Inactive"}
              </CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  );
}
