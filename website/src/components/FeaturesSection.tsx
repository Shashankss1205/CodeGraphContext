import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { GitBranch, Eye, Zap, Terminal, Trash2, BarChart3, MonitorSmartphone, MessageSquare } from "lucide-react";

const features = [
  {
    icon: GitBranch,
    title: "Lightning-Fast Indexing",
    description: "Transform your Python codebase into a smart, searchable graph in seconds. Discover hidden relationships and dependencies instantly.",
    color: "graph-node-1"
  },
  {
    icon: Eye,
    title: "Deep Relationship Analysis",
    description: "Visualize callers, callees, hierarchies, and complex code flows with beautiful, interactive graphs. Ask questions in natural language.",
    color: "graph-node-2"
  },
  {
    icon: Zap,
    title: "Live Real-Time Updates",
    description: "Your graph stays fresh as you code. Automatic updates and instant feedback keep your context always up-to-date.",
    color: "graph-node-3"
  },
  {
    icon: Terminal,
    title: "Effortless Setup",
    description: "Get started with a guided wizard. One command configures everything—Neo4j, Docker, or cloud. No manual steps required.",
    color: "graph-node-1"
  },
  {
    icon: Trash2,
    title: "Dead Code Detection",
    description: "Automatically find unused or unreachable code to keep your project clean and maintainable.",
    color: "graph-node-4"
  },
  {
    icon: BarChart3,
    title: "Complexity Analysis",
    description: "Calculate cyclomatic complexity and identify the most complex functions for targeted refactoring.",
    color: "graph-node-5"
  },
  {
    icon: MonitorSmartphone,
    title: "Seamless IDE Integration",
    description: "Works out-of-the-box with VS Code, Cursor, Claude, Gemini CLI, and more for a smooth developer experience.",
    color: "graph-node-6"
  },
  {
    icon: MessageSquare,
    title: "Natural Language Queries",
    description: "Ask questions about your codebase in plain English and get instant, actionable answers.",
    color: "graph-node-7"
  }
];

const FeaturesSection = () => {
  return (
    <section className="py-24 px-4 bg-gradient-to-br from-primary/5 via-background to-primary/10">
      <div className="container mx-auto max-w-6xl">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-extrabold mb-6 bg-gradient-to-r from-primary to-graph-node-2 bg-clip-text text-transparent drop-shadow-lg animate-gradient-x">
            Powerful Features
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto animate-fade-in">
            Supercharge your codebase with an intelligent graph that AI assistants can explore, analyze, and understand.
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-8">
          {features.map((feature, index) => (
            <Card 
              key={index} 
              className={`bg-gradient-to-tr from-background via-white/60 to-${feature.color}/10 border border-${feature.color}/40 hover:border-primary/60 transition-all duration-300 group hover:shadow-2xl animate-float-up`}
              style={{ animationDelay: `${index * 0.12}s` }}
            >
              <CardHeader>
                <div className="flex items-center gap-4 mb-4">
                  <div className={`p-3 rounded-xl bg-${feature.color}/20 border border-${feature.color}/30 group-hover:bg-${feature.color}/40 transition-all duration-300 shadow-lg animate-bounce-slow`}>
                    <feature.icon className={`h-8 w-8 text-${feature.color} drop-shadow-lg`} />
                  </div>
                  <CardTitle className={`text-xl font-bold text-${feature.color} group-hover:text-primary transition-all duration-200 drop-shadow-md`}>{feature.title}</CardTitle>
                </div>
                <CardDescription className="text-base text-muted-foreground leading-relaxed animate-fade-in">
                  {feature.description}
                </CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;