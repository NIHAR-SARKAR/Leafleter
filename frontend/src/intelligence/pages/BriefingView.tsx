import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { intelligenceApi } from "@/intelligence/services/intelligenceApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const titles: Record<string, string> = {
  daily: "Daily Intelligence Pulse",
  competitor: "Competitive Brief",
  opportunity: "Opportunity Radar",
  crisis: "Crisis Brief",
};

export function BriefingView() {
  const { briefType } = useParams<{ briefType: string }>();
  const [brief, setBrief] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!briefType) return;
    setLoading(true);
    intelligenceApi
      .getBrief(briefType)
      .then((r) => setBrief(r.data))
      .finally(() => setLoading(false));
  }, [briefType]);

  if (loading) {
    return <div className="p-8 text-center">Loading briefing...</div>;
  }

  if (brief?.error) {
    return <div className="p-8 text-center text-red-500">{brief.error}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="border-b pb-4">
        <h1 className="text-2xl font-bold">{titles[briefType || ""] || "Briefing"}</h1>
        <p className="text-sm text-muted-foreground">Generated: {brief?.generated_at}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Executive Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-base leading-relaxed">{brief?.executive_summary}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recommended Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {brief?.recommended_actions?.map((action: any) => (
              <div
                key={action.id}
                className={`rounded border p-3 ${
                  action.urgency > 7
                    ? "border-red-300 bg-red-50 dark:bg-red-950"
                    : action.urgency > 4
                    ? "border-yellow-300 bg-yellow-50 dark:bg-yellow-950"
                    : "border-green-300 bg-green-50 dark:bg-green-950"
                }`}
              >
                <div className="flex gap-2 text-sm text-muted-foreground">
                  <span>Urgency: {action.urgency}/10</span>
                  <span>Impact: {action.impact_score}/10</span>
                  <span>Effort: {action.effort}/10</span>
                </div>
                <h3 className="font-semibold">{action.title}</h3>
                <p className="text-sm">{action.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Overall Impact Score</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-4xl font-bold">{brief?.impact_score}/100</div>
        </CardContent>
      </Card>
    </div>
  );
}
