import { useEffect, useMemo, useState } from "react";

import { ActionItem, intelligenceApi } from "@/intelligence/services/intelligenceApi";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type ActionStatus = "pending" | "executed" | "dismissed" | "all";

export function ActionsView() {
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [filter, setFilter] = useState<ActionStatus>("pending");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const response = await intelligenceApi.listActions("all", 200);
      setActions(response.data.actions);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    if (filter === "all") return actions;
    return actions.filter((a) => a.status === filter);
  }, [actions, filter]);

  const counts = useMemo(() => {
    return {
      pending: actions.filter((a) => a.status === "pending" || !a.status).length,
      executed: actions.filter((a) => a.status === "executed").length,
      dismissed: actions.filter((a) => a.status === "dismissed").length,
      all: actions.length,
    };
  }, [actions]);

  const handleExecute = async (id: string) => {
    await intelligenceApi.executeAction(id);
    await load();
  };

  const handleDismiss = async (id: string) => {
    await intelligenceApi.dismissAction(id, "dismissed_by_user");
    await load();
  };

  if (loading) {
    return <div className="p-8 text-center">Loading actions...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Action Center</h1>
      </div>

      <div className="flex flex-wrap gap-2">
        {(["pending", "executed", "dismissed", "all"] as ActionStatus[]).map((status) => (
          <Button
            key={status}
            variant={filter === status ? "default" : "outline"}
            onClick={() => setFilter(status)}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)} ({counts[status]})
          </Button>
        ))}
      </div>

      <div className="space-y-4">
        {filtered.map((action) => (
          <ActionCard
            key={action.id}
            action={action}
            onExecute={handleExecute}
            onDismiss={handleDismiss}
          />
        ))}
      </div>
    </div>
  );
}

function ActionCard({
  action,
  onExecute,
  onDismiss,
}: {
  action: ActionItem;
  onExecute: (id: string) => void;
  onDismiss: (id: string) => void;
}) {
  const width = `${action.urgency * 10}%`;
  const bg = action.urgency > 7 ? "bg-red-500" : action.urgency > 4 ? "bg-yellow-500" : "bg-green-500";

  return (
    <Card>
      <div className={`h-1 w-full ${bg}`} style={{ width }} />
      <CardHeader>
        <div className="flex items-center justify-between">
          <span className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium uppercase text-primary">
            {action.type}
          </span>
          <span className="text-xs text-muted-foreground">{action.status || "pending"}</span>
        </div>
        <CardTitle className="text-lg">{action.title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {action.description ? <p className="text-sm text-muted-foreground">{action.description}</p> : null}

        <div className="grid grid-cols-2 gap-4 rounded-md bg-muted p-3 sm:grid-cols-4">
          <Stat label="Urgency" value={`${action.urgency}/10`} />
          <Stat label="Effort" value={`${action.effort}/10`} />
          <Stat label="Impact" value={`${action.impact_score}/10`} />
          <Stat
            label="Priority Score"
            value={action.priority_score?.toFixed(1) || "-"}
            highlight
          />
        </div>

        {action.why_matters ? (
          <p className="text-sm">
            <strong>Why this matters:</strong> {action.why_matters}
          </p>
        ) : null}
        {action.expected_outcome ? (
          <p className="text-sm">
            <strong>Expected outcome:</strong> {action.expected_outcome}
          </p>
        ) : null}

        <div className="flex gap-2">
          <Button
            onClick={() => onExecute(action.id)}
            disabled={Boolean(action.status && action.status !== "pending")}
          >
            Execute
          </Button>
          <Button
            variant="outline"
            onClick={() => onDismiss(action.id)}
            disabled={Boolean(action.status && action.status !== "pending")}
          >
            Dismiss
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="text-center">
      <span className={`block text-xl font-bold ${highlight ? "text-primary" : ""}`}>{value}</span>
      <span className="text-xs uppercase text-muted-foreground">{label}</span>
    </div>
  );
}
