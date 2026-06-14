import { Globe, Search as SearchIcon } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
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
import api from "@/services/api";

export function Search() {
  const [query, setQuery] = useState("");
  const [engine, setEngine] = useState("serpapi");
  const [results, setResults] = useState<any[]>([]);
  const [url, setUrl] = useState("");
  const [crawlResult, setCrawlResult] = useState<any>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const { data } = await api.post("/search", {
      query,
      engine_type: engine,
      num_results: 10,
    });
    setResults(data.results);
  };

  const handleCrawl = async (e: React.FormEvent) => {
    e.preventDefault();
    const { data } = await api.post("/search/crawl", { url });
    setCrawlResult(data);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Search Intelligence</h2>
        <p className="text-muted-foreground">Web search, crawl, and sitemap parsing</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Web Search</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-4">
            <Input
              placeholder="Search query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              required
            />
            <Select value={engine} onValueChange={setEngine}>
              <SelectTrigger className="w-[160px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="serpapi">SerpApi</SelectItem>
                <SelectItem value="bing">Bing</SelectItem>
                <SelectItem value="tavily">Tavily</SelectItem>
                <SelectItem value="google_cse">Google CSE</SelectItem>
                <SelectItem value="duckduckgo">DuckDuckGo</SelectItem>
              </SelectContent>
            </Select>
            <Button type="submit">
              <SearchIcon className="mr-2 h-4 w-4" />
              Search
            </Button>
          </form>
          <div className="mt-4 space-y-2">
            {results.map((r, idx) => (
              <div key={idx} className="rounded-md border p-3">
                <a
                  href={r.url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-primary hover:underline"
                >
                  {r.title}
                </a>
                <p className="text-sm text-muted-foreground">{r.snippet}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Crawl URL</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCrawl} className="flex gap-4">
            <Input
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
            <Button type="submit">
              <Globe className="mr-2 h-4 w-4" />
              Crawl
            </Button>
          </form>
          {crawlResult && (
            <div className="mt-4 rounded-md border p-4">
              <h4 className="font-medium">{crawlResult.title}</h4>
              <p className="mt-2 line-clamp-6 text-sm text-muted-foreground">
                {crawlResult.text}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
