import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { useState } from "react";
import graphTotalImage from "@/assets/graph-total.png";
import functionCallsImage from "@/assets/function-calls.png";
import hierarchyImage from "@/assets/hierarchy.png";

const DemoSection = () => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const visualizations = [
    {
      title: "Complete Code Graph",
      description: "All components and relationships between code elements",
      image: graphTotalImage,
      badge: "Full Overview"
    },
    {
      title: "Function Call Analysis",
      description: "Direct and indirect function calls across directories",
      image: functionCallsImage,
      badge: "Call Chains"
    },
    {
      title: "Project Hierarchy",
      description: "Hierarchical structure of files and dependencies",
      image: hierarchyImage,
      badge: "File Structure"
    }
  ];

  return (
    <section className="py-20 px-4 bg-gradient-to-b from-background to-secondary/10">
      <div className="container mx-auto max-w-7xl">
        <div className="text-center mb-16">
          <h2 className="text-2xl sm:text-3xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-primary via-primary to-accent bg-clip-text text-transparent">
            See CodeGraphContext in Action
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-12">
            Watch how CodeGraphContext transforms complex codebases into interactive knowledge graphs
          </p>

          {/* YouTube Video */}
          <div className="max-w-4xl mx-auto mb-16">
            <div className="relative aspect-video rounded-lg overflow-hidden shadow-2xl border border-border/50">
                          <iframe
                              src="https://www.youtube.com/embed/KYYSdxhg1xU?autoplay=1&mute=1&loop=1&playlist=KYYSdxhg1xU"
                              title="CodeGraphContext Demo"
                              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                              allowFullScreen
                              className="w-full h-full"
                          />

            </div>
          </div>
        </div>

        {/* Visualization Examples */}
        <div className="mb-12">
          <h3 className="text-3xl font-bold text-center mb-8">
            Interactive Visualizations
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
            {visualizations.map((viz, index) => (
              <Card key={index} className="group hover:shadow-xl transition-all duration-300 border-border/50 overflow-hidden w-full">
                <Dialog>
                  <DialogTrigger asChild>
                    <div className="relative cursor-pointer md:flex md:items-center lg:block">
                      <img
                        src={viz.image}
                        alt={viz.title}
                        className="w-full md:w-1/2 lg:w-full h-40 sm:h-48 md:h-32 lg:h-40 object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                      <Badge className="absolute top-2 left-2 text-xs bg-primary/90 text-primary-foreground">
                        {viz.badge}
                      </Badge>
                      <div className="absolute inset-0 md:left-0 md:right-1/2 lg:right-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300 flex items-center justify-center">
                        <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-white/90 rounded-full p-1.5 sm:p-2">
                          <svg className="w-4 h-4 sm:w-6 sm:h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                          </svg>
                        </div>
                      </div>
                      <CardContent className="md:w-1/2 lg:w-full p-4 sm:p-6 md:flex md:flex-col md:justify-center lg:block">
                        <h4 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 group-hover:text-primary transition-colors">
                          {viz.title}
                        </h4>
                        <p className="text-sm sm:text-base text-muted-foreground">
                          {viz.description}
                        </p>
                      </CardContent>
                    </div>
                  </DialogTrigger>
                  <DialogContent className="max-w-5xl w-full">
                    <div className="relative">
                      <img
                        src={viz.image}
                        alt={viz.title}
                        className="w-full h-auto max-h-[80vh] object-contain"
                      />
                      <div className="mt-4 text-center">
                        <h4 className="text-xl font-semibold mb-2">{viz.title}</h4>
                        <p className="text-muted-foreground">{viz.description}</p>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </Card>
            ))}
          </div>
        </div>

        <div className="text-center">
          <p className="text-lg text-muted-foreground">
            Transform your codebase into an intelligent, queryable knowledge graph
          </p>
        </div>
      </div>
    </section>
  );
};

export default DemoSection;
