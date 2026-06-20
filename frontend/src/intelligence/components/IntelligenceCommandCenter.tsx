import { Bell, TrendingUp, ShieldAlert, Zap } from "lucide-react";

import { useIntelligence } from "@/intelligence/hooks/useIntelligence";
import { useWebSocket } from "@/intelligence/hooks/useWebSocket";
import { ActionItem, IntelligenceEvent, RelatedEntity, SuggestedAction } from "@/intelligence/services/intelligenceApi";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { intelligenceApi } from "@/intelligence/services/intelligenceApi";

interface KPICardProps {
  title: string;
  count: number;
  newCount?: number;
  urgentCount?: number;
  color: "red" | "green" | "orange" | "blue";
  icon: React.ElementType;
}

function KPICard({ title, count, newCount, urgentCount, color, icon: Icon }: KPICardProps) {
  const colorClasses = {
    red: "border-l-red-500",
    green: "border-l-green-500",
    orange: "border-l-orange-500",
    blue: "border-l-blue-500",
  };

  return (
    <Card className={`border-l-4 ${colorClasses[color]}`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium uppercase text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-muted-foreground" />
          <span className="text-3xl font-bold">{count}</span>
          {newCount ? (
            <span className="rounded-full bg-red-500 px-2 py-0.5 text-xs text-white">
              {newCount} new
            </span>
          ) : null}
          {urgentCount ? (
            <span className="rounded-full bg-orange-500 px-2 py-0.5 text-xs text-white">
              {urgentCount} urgent
            </span>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

function PriorityQueue({
  items,
  onExecute,
  onDismiss,
}: {
  items: ActionItem[];
  onExecute: (id: string) => void;
  onDismiss: (id: string) => void;
}) {
  if (items.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        No pending actions. Intelligence core is quiet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((item, index) => (
        <PriorityItem
          key={item.id}
          item={item}
          index={index}
          onExecute={onExecute}
          onDismiss={onDismiss}
        />
      ))}
    </div>
  );
}

function PriorityItem({
  item,
  index,
  onExecute,
  onDismiss,
}: {
  item: ActionItem;
  index: number;
  onExecute: (id: string) => void;
  onDismiss: (id: string) => void;
}) {
  const priorityClass =
    item.urgency > 7 ? "border-l-red-500" : item.urgency > 4 ? "border-l-yellow-500" : "border-l-green-500";

  return (
    <Card className={`border-l-4 ${priorityClass}`}>
      <CardContent className="pt-4">
        <div className="mb-2 flex items-center gap-3 text-sm">
          <span className="rounded-full bg-muted px-2 py-0.5 font-medium">#{index + 1}</span>
          <span className="font-semibold text-red-600">Urgency: {item.urgency}/10</span>
          <span className="flex gap-1">
            {item.source_modules?.map((source) => (
              <span
                key={source}
                className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700 dark:bg-blue-900 dark:text-blue-100"
              >
                {source}
              </span>
            ))}
          </span>
        </div>

        <h3 className="mb-2 text-lg font-semibold">{item.title}</h3>

        {item.description ? (
          <p className="mb-3 text-sm text-muted-foreground">{item.description}</p>
        ) : null}

        {item.why_matters ? (
          <div className="mb-3 rounded-md bg-muted p-3 text-sm italic">
            <strong>AI Insight:</strong> {item.why_matters}
          </div>
        ) : null}

        {item.related_entities && item.related_entities.length > 0 ? (
          <div className="mb-3 text-sm">
            <strong>Related:</strong>{" "}
            {item.related_entities.map((entity) => (
              <EntityLink key={`${entity.type}-${entity.id}`} entity={entity} />
            ))}
          </div>
        ) : null}

        <div className="flex flex-wrap gap-2">
          {item.suggested_actions?.map((action) => (
            <SuggestedActionCard
              key={action.id}
              action={action}
              onExecute={onExecute}
              onDismiss={onDismiss}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function EntityLink({ entity }: { entity: RelatedEntity }) {
  return (
    <a
      href={`/intelligence/entity/${entity.type}/${entity.id}`}
      className="mr-2 inline-block rounded bg-accent px-2 py-0.5 text-xs hover:underline"
    >
      {entity.name} ({entity.type})
    </a>
  );
}

function SuggestedActionCard({
  action,
  onExecute,
  onDismiss,
}: {
  action: SuggestedAction;
  onExecute: (id: string) => void;
  onDismiss: (id: string) => void;
}) {
  return (
    <div className="flex items-center gap-2 rounded-md border bg-card p-2">
      <span className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium uppercase text-primary">
        {action.type}
      </span>
      <span className="text-sm">{action.title}</span>
      <Button size="sm" onClick={() => onExecute(action.id)}>
        Execute
      </Button>
      <Button size="sm" variant="outline" onClick={() => onDismiss(action.id)}>
        Dismiss
      </Button>
    </div>
  );
}

function RealtimeFeed({ events }: { events: IntelligenceEvent[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Live Intelligence</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="max-h-80 space-y-2 overflow-y-auto pr-2">
          {events.length === 0 ? (
            <p className="text-sm text-muted-foreground">No live events yet.</p>
          ) : (
            events.slice(-10).map((event, index) => (
              <FeedItem key={`${event.id}-${index}`} event={event} />
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function FeedItem({ event }: { event: IntelligenceEvent }) {
  const priorityClass =
    event.priority === "urgent" || event.priority === "high"
      ? "bg-red-50 dark:bg-red-950"
      : "bg-transparent";

  return (
    <div className={`flex items-center gap-2 rounded p-2 text-xs ${priorityClass}`}>
      <span className="text-muted-foreground">
        {new Date(event.timestamp).toLocaleTimeString()}
      </span>
      <span className="font-semibold text-primary">{event.source}</span>
      <span className="text-muted-foreground">{event.type}</span>
      <span className="ml-auto rounded bg-muted px-1.5 py-0.5 uppercase">{event.priority}</span>
    </div>
  );
}

export function IntelligenceCommandCenter() {
  const { today, loading, refresh } = useIntelligence();
  const { events, connected } = useWebSocket("/api/v1/intelligence/ws");

  const handleExecute = async (id: string) => {
    try {
      await intelligenceApi.executeAction(id);
      refresh();
    } catch (err) {
      console.error("Failed to execute action", err);
    }
  };

  const handleDismiss = async (id: string) => {
    try {
      await intelligenceApi.dismissAction(id, "dismissed_by_user");
      refresh();
    } catch (err) {
      console.error("Failed to dismiss action", err);
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading intelligence dashboard...</div>;
  }

  if (!today?.enabled) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        Intelligence core is disabled. Enable it via ENABLE_INTELLIGENCE_CORE to see the dashboard.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Marketing Intelligence Center</h1>
        <div className="flex items-center gap-3">
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              connected
                ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-100"
                : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
            }`}
          >
            {connected ? "Live" : "Offline"}
          </span>
          <Button variant="outline" onClick={refresh}>
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Alerts"
          count={today?.alerts?.count || 0}
          newCount={today?.alerts?.new || undefined}
          color="red"
          icon={Bell}
        />
        <KPICard
          title="Opportunities"
          count={today?.opportunities?.count || 0}
          urgentCount={today?.opportunities?.urgent || undefined}
          color="green"
          icon={TrendingUp}
        />
        <KPICard
          title="Threats"
          count={today?.threats?.count || 0}
          color="orange"
          icon={ShieldAlert}
        />
        <KPICard
          title="Active Workflows"
          count={today?.workflows?.active || 0}
          color="blue"
          icon={Zap}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h2 className="mb-4 text-lg font-semibold">
            Priority Queue ({today?.priority_queue?.length || 0})
          </h2>
          <PriorityQueue
            items={today?.priority_queue || []}
            onExecute={handleExecute}
            onDismiss={handleDismiss}
          />
        </div>

        <div>
          <RealtimeFeed events={events} />
        </div>
      </div>
    </div>
  );
}
