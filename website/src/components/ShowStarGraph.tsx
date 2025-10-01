import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExternalLink, Star, TrendingUp, RefreshCw } from "lucide-react";
import { useState, useCallback } from "react";

export default function ShowStarGraph() {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const baseStarHistoryImageUrl =
    "https://api.star-history.com/svg?repos=Shashankss1205/CodeGraphContext&type=Date";
  
  // Add cache busting parameter to force updates
  const starHistoryImageUrl = `${baseStarHistoryImageUrl}&t=${refreshKey}`;
  const starHistoryDarkImageUrl = `${baseStarHistoryImageUrl}&theme=dark&t=${refreshKey}`;
  
  const githubRepoUrl = "https://github.com/Shashankss1205/CodeGraphContext";
  const starHistoryUrl =
    "https://star-history.com/#Shashankss1205/CodeGraphContext&Date";

  const handleImageLoad = () => {
    setImageLoaded(true);
    setImageError(false);
    setIsRefreshing(false);
  };

  const handleImageError = () => {
    setImageError(true);
    setImageLoaded(false);
    setIsRefreshing(false);
  };

  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    setImageLoaded(false);
    setImageError(false);
    setRefreshKey(prev => prev + 1);
  }, []);

  return (
    <>
      <section className="px-4 bg-gradient-to-b from-secondary/10 to-background">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Star className="h-6 w-6 text-yellow-500 fill-yellow-500" />

              <h2 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-primary via-primary to-accent bg-clip-text text-transparent">
                Star History
              </h2>
              <TrendingUp className="h-6 w-6 text-green-500" />
            </div>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Track the growth and popularity of CodeGraphContext over time
            </p>
          </div>

          <Card className="w-full shadow-2xl border-border/50 bg-card/50 backdrop-blur-sm">
            <CardHeader className="text-center">
              <CardTitle className="flex items-center justify-center gap-2 text-2xl">
                <Star className="h-5 w-5 text-yellow-500 fill-yellow-500" />
                Repository Growth
                <Badge variant="outline" className="ml-2">
                  Updated Daily
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  className="ml-2 h-8 w-8 p-0"
                >
                  <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="relative">
                {(!imageLoaded && !imageError) || isRefreshing && (
                  <div className="w-full h-64 bg-muted rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-2"></div>
                      <p className="text-muted-foreground">
                        {isRefreshing ? 'Refreshing star history...' : 'Loading star history...'}
                      </p>
                    </div>
                  </div>
                )}

                {imageError && (
                  <div className="w-full h-64 bg-muted rounded-lg flex items-center justify-center border-2 border-dashed border-border">
                    <div className="text-center">
                      <Star className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                      <p className="text-muted-foreground mb-2">
                        Unable to load star history
                      </p>
                      <Button
                        variant="outline"
                        onClick={() => window.open(starHistoryUrl, "_blank")}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        View on Star History
                      </Button>
                    </div>
                  </div>
                )}

                <picture key={refreshKey}>
                  <source media="(prefers-color-scheme: dark)" srcSet={starHistoryDarkImageUrl} />
                  <source media="(prefers-color-scheme: light)" srcSet={starHistoryImageUrl} />
                  <img
                    src={starHistoryImageUrl}
                    alt="CodeGraphContext Star History"
                    className={`w-full h-auto rounded-lg transition-opacity duration-300 ${
                      imageLoaded && !isRefreshing ? "opacity-100" : "opacity-0 absolute inset-0"
                    } ${imageError ? "hidden" : "block"}`}
                    onLoad={handleImageLoad}
                    onError={handleImageError}
                  />
                </picture>
              </div>

              {imageLoaded && !isRefreshing && (
                <div className="mt-6 flex flex-col sm:flex-row gap-4 justify-center items-center">
                  <Button
                    variant="outline"
                    onClick={() => window.open(githubRepoUrl, "_blank")}
                    className="flex items-center gap-2"
                  >
                    <Star className="h-4 w-4" />
                    Star on GitHub
                    <ExternalLink className="h-4 w-4" />
                  </Button>

                  <Button
                    variant="ghost"
                    onClick={() => window.open(starHistoryUrl, "_blank")}
                    className="flex items-center gap-2"
                  >
                    <TrendingUp className="h-4 w-4" />
                    View Full History
                    <ExternalLink className="h-4 w-4" />
                  </Button>

                  <Button
                    variant="secondary"
                    onClick={handleRefresh}
                    disabled={isRefreshing}
                    className="flex items-center gap-2"
                  >
                    <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                    Refresh Graph
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="text-center mt-8">
            <p className="text-sm text-muted-foreground">
              Data provided by{" "}
              <a
                href="https://star-history.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                Star History
              </a>{" "}
              • Updated with a delay
            </p>
          </div>
        </div>
      </section>
      <br />
      <br />
    </>
  );
}
