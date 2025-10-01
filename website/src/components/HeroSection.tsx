import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Github, Download, ExternalLink } from "lucide-react";
import heroGraph from "@/assets/hero-graph.jpg";
import { useState, useEffect } from "react";
import ShowDownloads from "./ShowDownloads";
import ShowStarGraph from "./ShowStarGraph";

const HeroSection = () => {
  const [stars, setStars] = useState(null);
  const [forks, setForks] = useState(null);
   const [version, setVersion] = useState("");
  useEffect(() => {
    async function fetchVersion() {
      try {
        const res = await fetch(
          "https://raw.githubusercontent.com/Shashankss1205/CodeGraphContext/main/README.md"
        );
        if (!res.ok) throw new Error("Failed to fetch README");

        const text = await res.text();
        const match = text.match(
          /\*\*Version:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)/i
        );
        setVersion(match ? match[1] : "N/A");
      } catch (err) {
        console.error(err);
        setVersion("N/A");
      }
    }

    fetchVersion();
  }, []);
  useEffect(() => {
    fetch("https://api.github.com/repos/Shashankss1205/CodeGraphContext")
      .then((response) => response.json())
      .then((data) => {
        setStars(data.stargazers_count);
        setForks(data.forks_count);
      })
      .catch((error) => console.error("Error fetching GitHub stats:", error));
  }, []);

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-30"
        style={{ backgroundImage: `url(${heroGraph})` }}
      />
      
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-background/90 via-background/80 to-background/90" />
      
      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 text-center max-w-5xl">
        <div className="animate-float-up">
          <Badge variant="secondary" className="mb-6 text-sm font-medium">
            <div className="w-2 h-2 bg-accent rounded-full mr-2 animate-graph-pulse" />
            Version {version} • MIT License
          </Badge>
          
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold mb-6 bg-gradient-primary bg-clip-text text-transparent leading-tight">
            CodeGraphContext
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-foreground mb-4 leading-relaxed">
            An MCP server that indexes local code into a
          </p>
          <p className="text-xl md:text-2xl text-accent font-semibold mb-8">
            knowledge graph for AI assistants
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Button size="lg" className="bg-gradient-primary hover:opacity-90 transition-all duration-300 shadow-glow" asChild>
              <a href="https://pypi.org/project/codegraphcontext/" target="_blank" rel="noopener noreferrer">
                <Download className="mr-2 h-5 w-5" />
                pip install codegraphcontext
              </a>
            </Button>
            
            <Button variant="outline" size="lg" asChild className="border-primary/30 hover:border-primary/60 transition-smooth">
              <a href="https://github.com/Shashankss1205/CodeGraphContext" target="_blank" rel="noopener noreferrer">
                <Github className="mr-2 h-5 w-5" />
                View on GitHub
                <ExternalLink className="ml-2 h-4 w-4" />
              </a>
            </Button>
          </div>
          
          {/* Stats */}
          <div className="flex flex-wrap justify-center gap-8 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-graph-node-1 rounded-full animate-graph-pulse" />
              {stars !== null ? <span>{stars} GitHub Stars</span> : <span>Loading...</span>}
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-graph-node-2 rounded-full animate-graph-pulse" style={{animationDelay: '0.5s'}} />
              {forks !== null ? <span>{forks} Forks</span> : <span>Loading...</span>}
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-graph-node-3 rounded-full animate-graph-pulse" style={{animationDelay: '1s'}} />
              <span><ShowDownloads /></span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Floating Graph Nodes */}
      <div className="absolute top-20 left-10 w-8 h-8 graph-node animate-graph-pulse" style={{animationDelay: '0.2s'}} />
      <div className="absolute top-40 right-20 w-6 h-6 graph-node animate-graph-pulse" style={{animationDelay: '0.8s'}} />
      <div className="absolute bottom-32 left-20 w-10 h-10 graph-node animate-graph-pulse" style={{animationDelay: '1.2s'}} />
      <div className="absolute bottom-20 right-10 w-7 h-7 graph-node animate-graph-pulse" style={{animationDelay: '0.6s'}} />
    </section>
  );
};

export default HeroSection;