import { useEffect, useState } from "react";
import { FileText, Plus } from "lucide-react";

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
import { reportsApi, topicsApi } from "@/services/api";
import type { Report, Topic } from "@/types";

export function Reports() {
  const [reports, setReports] = useState<Report[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [title, setTitle] = useState("");
  const [format, setFormat] = useState("markdown");
  const [topicId, setTopicId] = useState("");

  const fetchReports = async () => {
    const { data } = await reportsApi.list();
    setReports(data);
  };

  useEffect(() => {
    fetchReports();
    topicsApi.list().then(({ data }) => setTopics(data));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await reportsApi.create({
      title,
      report_type: "analysis",
      format,
      topic_id: Number(topicId),
    });
    setTitle("");
    fetchReports();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Reports</h2>
        <p className="text-muted-foreground">Generate and download reports</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Generate Report</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="flex gap-4">
            <Input
              placeholder="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
            <Select value={format} onValueChange={setFormat}>
              <SelectTrigger className="w-[160px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="markdown">Markdown</SelectItem>
                <SelectItem value="pdf">PDF</SelectItem>
                <SelectItem value="docx">DOCX</SelectItem>
                <SelectItem value="pptx">PPTX</SelectItem>
              </SelectContent>
            </Select>
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
            <Button type="submit">
              <Plus className="mr-2 h-4 w-4" />
              Generate
            </Button>
          </form>
        </CardContent>
      </Card>
      <div className="grid gap-4">
        {reports.map((report) => (
          <Card key={report.id}>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>{report.title}</CardTitle>
                <CardDescription>
                  {report.format.toUpperCase()} • {report.status}
                </CardDescription>
              </div>
              {report.download_url && (
                <a href={report.download_url} download>
                  <Button size="sm" variant="outline">
                    <FileText className="mr-2 h-4 w-4" />
                    Download
                  </Button>
                </a>
              )}
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  );
}
