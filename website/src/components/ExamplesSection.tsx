import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MessageCircle, Search, Eye, BarChart3, FileImage } from "lucide-react";

const examples = [
  {
    icon: MessageCircle,
    category: "Indexing",
    title: "Add Projects to Graph",
    examples: [
      "Please index the code in the `/path/to/my-project` directory.",
      "Add the project at `~/dev/my-app` to the code graph."
    ]
  },
  {
    icon: Search,
    category: "Analysis",
    title: "Code Relationships", 
    examples: [
      "Show me all functions that call `process_data()`",
      "Find the class hierarchy for `BaseProcessor`"
    ]
  },
  {
    icon: FileImage,
    category: "Export",
    title: "Graph Visualization",
    examples: [
      "Export a PNG visualization of my code graph",
      "Create an interactive HTML graph for my documentation"
    ]
  },
  {
    icon: Eye,
    category: "Monitoring",
    title: "Live Updates",
    examples: [
      "Watch the `/project` directory for changes.",
      "Keep the graph updated for my active development."
    ]
  },
  {
    icon: BarChart3,
    category: "Insights",
    title: "Code Quality",
    examples: [
      "Find dead code in my project",
      "Show the most complex functions by cyclomatic complexity"
    ]
  }
];

const ExamplesSection = () => {
  return (
    <section className="py-24 px-4">
      <div className="container mx-auto max-w-6xl">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-primary bg-clip-text text-transparent">
            Natural Language Interface
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Interact with your code graph using plain English. No complex queries or syntax to learn.
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {examples.map((example, index) => (
            <Card 
              key={index}
              className="bg-gradient-card border-border/50 hover:border-primary/30 transition-smooth group animate-float-up"
              style={{ animationDelay: `${index * 0.15}s` }}
            >
              <CardHeader>
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-3 rounded-xl bg-primary/10 border border-primary/20 group-hover:bg-primary/20 transition-smooth">
                    <example.icon className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <Badge variant="secondary" className="mb-2">
                      {example.category}
                    </Badge>
                    <CardTitle className="text-xl font-semibold">
                      {example.title}
                    </CardTitle>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {example.examples.map((exampleText, exampleIndex) => (
                    <div 
                      key={exampleIndex}
                      className="code-block border-l-4 border-l-accent/30 pl-4 hover:border-l-accent/60 transition-smooth"
                    >
                      <p className="text-sm text-muted-foreground italic">
                        "{exampleText}"
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        
        {/* CTA */}
        <div className="text-center mt-16">
          <Card className="bg-gradient-card border-primary/20 max-w-2xl mx-auto">
            <CardContent className="pt-8">
              <h3 className="text-2xl font-bold mb-4">
                Ready to enhance your AI assistant?
              </h3>
              <p className="text-muted-foreground mb-6">
                Start building intelligent code understanding today with CodeGraphContext
              </p>
              <div className="code-block max-w-md mx-auto">
                <code className="text-accent">
                  $ pip install codegraphcontext
                </code>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default ExamplesSection;