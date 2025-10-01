import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy, Terminal, Play, Settings } from "lucide-react";
import { toast } from "sonner";
import ShowStarGraph from "./ShowStarGraph";

const installSteps = [
  {
    step: "1",
    title: "Install",
    command: "pip install codegraphcontext",
    description: "Install CodeGraphContext using pip"
  },
  {
    step: "2", 
    title: "Setup",
    command: "cgc setup",
    description: "Interactive wizard to configure Neo4j database"
  },
  {
    step: "3",
    title: "Start",
    command: "cgc start",
    description: "Launch the MCP server and start indexing"
  }
];

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text);
  toast.success("Copied to clipboard!");
};

const InstallationSection = () => {
  return (
    <>
    <ShowStarGraph />
    <section className="py-24 px-4 bg-muted/20">
      <div className="container mx-auto max-w-5xl">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Get Started in Minutes
          </h2>
          <p className="text-xl text-muted-foreground">
            Simple installation with automated setup for Neo4j database configuration
          </p>
        </div>
        
        <div className="grid gap-6 mb-12">
          {installSteps.map((step, index) => (
            <Card 
              key={index}
              className="bg-gradient-card border-border/50 hover:border-primary/30 transition-smooth animate-float-up"
              style={{ animationDelay: `${index * 0.2}s` }}
            >
              <CardHeader className="pb-4">
                <div className="flex items-center gap-4">
                  <Badge variant="secondary" className="text-lg font-bold w-8 h-8 rounded-full flex items-center justify-center bg-primary/10">
                    {step.step}
                  </Badge>
                  <CardTitle className="text-xl">{step.title}</CardTitle>
                </div>
                <CardDescription className="text-base">
                  {step.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="code-block flex items-center justify-between group">
                  <code className="text-accent font-mono animate-code-highlight">
                    $ {step.command}
                  </code>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(step.command)}
                    className="opacity-0 group-hover:opacity-100 transition-all duration-200 hover:bg-primary/10"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        
        {/* Setup Options */}
        <Card className="bg-gradient-card border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <Settings className="h-6 w-6 text-primary" />
              Setup Options
            </CardTitle>
            <CardDescription>
              The setup wizard supports multiple Neo4j configurations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-graph-node-1/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Terminal className="h-6 w-6 text-graph-node-1" />
                </div>
                <h4 className="font-semibold mb-2">Docker (Recommended)</h4>
                <p className="text-sm text-muted-foreground">
                  Automated Neo4j setup using Docker containers
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-graph-node-2/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Play className="h-6 w-6 text-graph-node-2" />
                </div>
                <h4 className="font-semibold mb-2">Linux Binary</h4>
                <p className="text-sm text-muted-foreground">
                  Direct installation on Debian-based systems
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-graph-node-3/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Settings className="h-6 w-6 text-graph-node-3" />
                </div>
                <h4 className="font-semibold mb-2">Hosted Database</h4>
                <p className="text-sm text-muted-foreground">
                  Connect to Neo4j AuraDB or existing instance
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
    </>
  );
};

export default InstallationSection;