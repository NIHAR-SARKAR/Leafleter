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
import { competitorsApi } from "@/services/api";
import type { Competitor } from "@/types";

export function Competitors() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");

  const fetchCompetitors = async () => {
    const { data } = await competitorsApi.list();
    setCompetitors(data);
  };

  useEffect(() => {
    fetchCompetitors();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await competitorsApi.create({ name, website_url: website });
    setName("");
    setWebsite("");
    fetchCompetitors();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Competitors</h2>
        <p className="text-muted-foreground">Track competitor activity</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Add Competitor</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="flex gap-4">
            <Input
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <Input
              placeholder="Website URL"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
            />
            <Button type="submit">
              <Plus className="mr-2 h-4 w-4" />
              Add
            </Button>
          </form>
        </CardContent>
      </Card>
      <div className="grid gap-4 md:grid-cols-2">
        {competitors.map((competitor) => (
          <Card key={competitor.id}>
            <CardHeader>
              <CardTitle>{competitor.name}</CardTitle>
              <CardDescription>{competitor.website_url}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {competitor.industry || "No industry"}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
