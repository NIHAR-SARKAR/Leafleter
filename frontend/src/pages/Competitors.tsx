import { useEffect, useState } from "react";
import { Download, Loader2, Plus, RefreshCw, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { competitorsApi, organizationApi } from "@/services/api";
import type { Competitor, CompetitorFeature, CompetitorFeatureComparison } from "@/types";

export function Competitors() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");
  const [industry, setIndustry] = useState("");
  const [socialHandles, setSocialHandles] = useState("");

  const [features, setFeatures] = useState<CompetitorFeature[]>([]);
  const [featureName, setFeatureName] = useState("");
  const [featureDescription, setFeatureDescription] = useState("");

  const [selectedCompetitor, setSelectedCompetitor] = useState<Competitor | null>(null);
  const [comparison, setComparison] = useState<CompetitorFeatureComparison | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonOpen, setComparisonOpen] = useState(false);

  const fetchCompetitors = async () => {
    const { data } = await competitorsApi.list();
    setCompetitors(data);
  };

  const fetchOrganization = async () => {
    const { data } = await organizationApi.me();
    setFeatures(data.features || []);
  };

  useEffect(() => {
    fetchCompetitors();
    fetchOrganization();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await competitorsApi.create({
      name,
      website_url: website,
      industry,
      social_handles: socialHandles,
    });
    setName("");
    setWebsite("");
    setIndustry("");
    setSocialHandles("");
    fetchCompetitors();
  };

  const handleAddFeature = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!featureName.trim()) return;
    const updated = [
      ...features,
      { name: featureName, description: featureDescription, evidence: null, confidence: null },
    ];
    setFeatures(updated);
    setFeatureName("");
    setFeatureDescription("");
    await organizationApi.updateFeatures(updated);
    fetchOrganization();
  };

  const handleRemoveFeature = async (index: number) => {
    const updated = features.filter((_, i) => i !== index);
    setFeatures(updated);
    await organizationApi.updateFeatures(updated);
    fetchOrganization();
  };

  const handleCompare = async (competitor: Competitor) => {
    setSelectedCompetitor(competitor);
    setComparisonLoading(true);
    setComparisonOpen(true);
    try {
      const { data } = await competitorsApi.compare(competitor.id);
      setComparison(data);
    } catch (error) {
      setComparison(null);
    } finally {
      setComparisonLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!comparison?.id) return;
    const response = await competitorsApi.downloadComparison(comparison.id);
    const blob = new Blob([response.data], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${comparison.title.replace(/\s+/g, "_")}.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const renderComparisonContent = () => {
    if (comparisonLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Generating comparison report...
        </div>
      );
    }

    if (!comparison) {
      return (
        <div className="py-8 text-center text-muted-foreground">
          Unable to load comparison report.
        </div>
      );
    }

    if (comparison.status === "failed") {
      return (
        <div className="py-8 text-center text-destructive">
          Report generation failed. Please try again later.
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {comparison.comparison_summary && (
          <div>
            <h4 className="mb-2 font-semibold">Executive Summary</h4>
            <p className="text-sm text-muted-foreground">
              {comparison.comparison_summary}
            </p>
          </div>
        )}

        <div>
          <h4 className="mb-2 font-semibold">Competitor Features</h4>
          {comparison.their_features && comparison.their_features.length > 0 ? (
            <ul className="space-y-2">
              {comparison.their_features.map((feature, idx) => (
                <li key={idx} className="rounded-md border p-3 text-sm">
                  <div className="font-medium">{feature.name}</div>
                  {feature.description && (
                    <div className="text-muted-foreground">{feature.description}</div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No competitor features extracted yet.</p>
          )}
        </div>

        <div>
          <h4 className="mb-2 font-semibold">Our Features</h4>
          {comparison.our_features && comparison.our_features.length > 0 ? (
            <ul className="grid gap-2 sm:grid-cols-2">
              {comparison.our_features.map((feature, idx) => (
                <li key={idx} className="rounded-md border p-2 text-sm">
                  {feature.name}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              No company features configured. Add features above to enable comparison.
            </p>
          )}
        </div>

        {comparison.sources && comparison.sources.length > 0 && (
          <div>
            <h4 className="mb-2 font-semibold">Sources</h4>
            <ul className="space-y-1 text-sm">
              {comparison.sources.map((source, idx) => (
                <li key={idx} className="text-muted-foreground">
                  {source.name} ({source.source_type})
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Competitors</h2>
        <p className="text-muted-foreground">Track competitor activity and compare capabilities</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Our Company Features</CardTitle>
          <CardDescription>
            Define the capabilities you want to compare against competitors.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleAddFeature} className="flex flex-col gap-4 sm:flex-row">
            <Input
              placeholder="Feature name"
              value={featureName}
              onChange={(e) => setFeatureName(e.target.value)}
              required
              className="sm:w-1/3"
            />
            <Input
              placeholder="Description (optional)"
              value={featureDescription}
              onChange={(e) => setFeatureDescription(e.target.value)}
              className="flex-1"
            />
            <Button type="submit">
              <Plus className="mr-2 h-4 w-4" />
              Add
            </Button>
          </form>
          <div className="flex flex-wrap gap-2">
            {features.map((feature, index) => (
              <div
                key={index}
                className="flex items-center gap-2 rounded-full border bg-muted px-3 py-1 text-sm"
              >
                <span>{feature.name}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveFeature(index)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
            {features.length === 0 && (
              <p className="text-sm text-muted-foreground">No features added yet.</p>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add Competitor</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2">
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
            <Input
              placeholder="Industry"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
            />
            <Input
              placeholder="Social handles / keywords"
              value={socialHandles}
              onChange={(e) => setSocialHandles(e.target.value)}
            />
            <div className="sm:col-span-2">
              <Button type="submit">
                <Plus className="mr-2 h-4 w-4" />
                Add Competitor
              </Button>
            </div>
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
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {competitor.industry || "No industry"}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCompare(competitor)}
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Compare
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={comparisonOpen} onOpenChange={setComparisonOpen}>
        <DialogContent className="max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedCompetitor
                ? `Feature Comparison: ${selectedCompetitor.name}`
                : "Feature Comparison"}
            </DialogTitle>
            <DialogDescription>
              Compare competitor capabilities against your company features.
            </DialogDescription>
          </DialogHeader>

          {renderComparisonContent()}

          <DialogFooter>
            {comparison?.download_url && (
              <Button onClick={handleDownload} variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Download DOCX
              </Button>
            )}
            <Button onClick={() => setComparisonOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
