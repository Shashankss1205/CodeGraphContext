import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy, Terminal, Play, Settings } from "lucide-react";
import { toast } from "sonner";

const installSteps = [
  {
    step: "1",
    title: "Install Instantly",
    command: "pip install codegraphcontext",
    description: "Get CodeGraphContext with a single pip command."
  },
  {
    step: "2", 
    title: "Guided Setup",
    command: "cgc setup",
    description: "Let the interactive wizard configure your Neo4j database and IDE for you."
  },
  {
    step: "3",
    title: "Start Exploring",
    command: "cgc start",
    description: "Launch the MCP server and begin indexing your codebase."
  }
];

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text);
  toast.success("Copied to clipboard!");
};

const InstallationSection = () => {
  return (
    <section className="py-24 px-4 bg-gradient-to-br from-primary/5 via-background to-primary/10">
      <div className="container mx-auto max-w-5xl">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-extrabold mb-6 bg-gradient-to-r from-primary to-graph-node-2 bg-clip-text text-transparent drop-shadow-lg animate-gradient-x">
            Get Started in Minutes
          </h2>
          <p className="text-xl text-muted-foreground animate-fade-in">
            Install, set up, and launch your code graph in just three steps. No manual config—just code.
          </p>
        </div>
        <div className="grid gap-6 mb-12">
          {installSteps.map((step, index) => (
            <Card 
              key={index}
              className="bg-gradient-to-tr from-background via-white/60 to-primary/5 border border-border/30 hover:border-primary/40 transition-all duration-300 group hover:shadow-2xl animate-float-up"
              style={{ animationDelay: `${index * 0.18}s` }}
            >
              <CardHeader className="pb-4">
                <div className="flex items-center gap-4">
                  <Badge variant="secondary" className="text-lg font-bold w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-primary/20 to-graph-node-2/20 shadow-md">
                    {step.step}
                  </Badge>
                  <CardTitle className="text-xl font-bold text-primary/90 group-hover:text-graph-node-2 transition-all duration-200">{step.title}</CardTitle>
                </div>
                <CardDescription className="text-base animate-fade-in">
                  {step.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="code-block flex items-center justify-between group">
                  <code className="text-accent font-mono animate-code-highlight text-lg">
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
        <Card className="bg-gradient-to-tr from-background via-white/60 to-primary/5 border border-border/30 shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 font-bold">
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
                <div className="w-12 h-12 bg-graph-node-1/10 rounded-lg flex items-center justify-center mx-auto mb-3 shadow-md">
                  <Terminal className="h-6 w-6 text-graph-node-1" />
                </div>
                <h4 className="font-semibold mb-2">Docker (Recommended)</h4>
                <p className="text-sm text-muted-foreground">
                  Automated Neo4j setup using Docker containers
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-graph-node-2/10 rounded-lg flex items-center justify-center mx-auto mb-3 shadow-md">
                  <Play className="h-6 w-6 text-graph-node-2" />
                </div>
                <h4 className="font-semibold mb-2">Linux Binary</h4>
                <p className="text-sm text-muted-foreground">
                  Direct installation on Debian-based systems
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-graph-node-3/10 rounded-lg flex items-center justify-center mx-auto mb-3 shadow-md">
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
  );
};

export default InstallationSection;