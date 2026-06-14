import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { intelligenceApi } from "@/intelligence/services/intelligenceApi";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function EntityDetail() {
  const { entityType, entityId } = useParams<{ entityType: string; entityId: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!entityType || !entityId) return;
    setLoading(true);
    intelligenceApi
      .getEntity(entityType, entityId)
      .then((r) => setData(r.data))
      .finally(() => setLoading(false));
  }, [entityType, entityId]);

  if (loading) {
    return <div className="p-8 text-center">Loading entity intelligence...</div>;
  }

  if (!data?.entity) {
    return <div className="p-8 text-center">Entity not found.</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm uppercase text-muted-foreground">{data.entity.type}</span>
          <h1 className="text-2xl font-bold">{data.entity.name}</h1>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>AI Intelligence Brief</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="whitespace-pre-wrap text-sm">
            {JSON.stringify(data.entity.data, null, 2)}
          </pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Related Entities ({data.related_entities?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {data.related_entities?.map((rel: any) => (
              <div key={`${rel.type}-${rel.id}`} className="rounded border p-2">
                <span className="font-medium">{rel.name}</span>
                <span className="ml-2 text-sm text-muted-foreground">
                  {rel.relationship} ({rel.type})
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recommended Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {data.recommended_actions?.map((action: any) => (
              <div key={action.id} className="rounded border p-2">
                <div className="font-medium">{action.title}</div>
                <div className="text-sm text-muted-foreground">{action.description}</div>
                <div className="mt-2 flex gap-2">
                  <Button size="sm">Execute</Button>
                  <Button size="sm" variant="outline">
                    Dismiss
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
