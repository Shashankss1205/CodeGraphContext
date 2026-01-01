import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy, Terminal, Play, Settings } from "lucide-react";
import { toast } from "sonner";
import ShowStarGraph from "@/components/ShowStarGraph";

const installSteps = [
  {
    step: "1",
    title: "Install",
    command: "pip install codegraphcontext",
    description: "Install CodeGraphContext using pip."
  },
  {
    step: "2",
    title: "Setup",
    command: "cgc mcp setup",
    description: "Interactive wizard to configure your IDE client."
  },
  {
    step: "3",
    title: "Start",
    command: "cgc mcp start",
    description: "Launch the MCP server and begin indexing."
  }
];

const setupOptions = [
  { icon: Terminal, title: "Docker (Recommended)", description: "Automated Neo4j setup using Docker containers.", color: "graph-node-1" },
  { icon: Play, title: "Linux Binary", description: "Direct installation on Debian-based systems.", color: "graph-node-2" },
  { icon: Settings, title: "Hosted Database", description: "Connect to Neo4j AuraDB or an existing instance.", color: "graph-node-3" }
];

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text);
  toast.success("Copied to clipboard!");
};

const InstallationSection = () => {
  return (
    <>
      <ShowStarGraph />
      <section className="py-24 px-4 bg-muted/20" data-aos="fade-in">
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-16" data-aos="fade-down">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-primary via-primary to-accent bg-clip-text text-transparent">
              Get Started in Minutes
            </h2>
            <p className="text-xl text-muted-foreground">
              Simple installation with automated setup for your database configuration.
            </p>
          </div>

          <div className="grid gap-6 mb-12">
            {installSteps.map((step, index) => (
              <div key={index} data-aos="fade-up" data-aos-delay={index * 100}>
                <Card className="transition-shadow duration-300 hover:shadow-lg bg-white/95 dark:bg-card/50">
                  <CardHeader className="pb-4">
                    <div className="flex items-center gap-4">
                      <Badge variant="secondary" className="text-lg font-bold w-9 h-9 flex items-center justify-center rounded-full bg-primary/10 text-primary">
                        {step.step}
                      </Badge>
                      <div>
                        <CardTitle className="text-xl">{step.title}</CardTitle>
                        <CardDescription>{step.description}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="p-3 rounded-md bg-muted/40 flex items-center justify-between group border shadow-inner">
                      <code className="text-accent font-mono text-sm">$ {step.command}</code>
                      <Button variant="ghost" size="icon" onClick={() => copyToClipboard(step.command)} className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8">
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>

          <div data-aos="fade-up" data-aos-delay="300">
            <Card className="bg-white/95 dark:bg-card/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-3"><Settings className="h-6 w-6 text-primary" />Setup Options</CardTitle>
                <CardDescription>The setup wizard supports multiple Neo4j configurations.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-6">
                  {setupOptions.map((option, index) => (
                    <div key={index} className="text-center p-4 rounded-lg bg-muted/30">
                      <div className={`w-12 h-12 bg-${option.color}/10 rounded-lg flex items-center justify-center mx-auto mb-3`}>
                        <option.icon className={`h-6 w-6 text-${option.color}`} />
                      </div>
                      <h4 className="font-semibold mb-2">{option.title}</h4>
                      <p className="text-sm text-muted-foreground">{option.description}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </>
  );
};

export default InstallationSection;

