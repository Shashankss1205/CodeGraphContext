import { Button } from "@/components/ui/button";
import { Github, ExternalLink, Mail } from "lucide-react";
import { useEffect, useState } from "react";

const Footer = () => {
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

  return (
    <footer className="border-t border-border/50 py-16 px-4 bg-muted/10">
      <div className="container mx-auto max-w-6xl">
        <div className="grid md:grid-cols-3 gap-12">
          {/* Brand */}
          <div>
            <h3 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent mb-4">
              CodeGraphContext
            </h3>
            <p className="text-muted-foreground mb-6 leading-relaxed">
              Transform your codebase into an intelligent knowledge graph for AI
              assistants.
            </p>
            <div className="flex gap-4">
              <Button variant="outline" size="sm" asChild>
                <a
                  href="https://github.com/Shashankss1205/CodeGraphContext"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Github className="h-4 w-4 mr-2" />
                  GitHub
                </a>
              </Button>
              <Button variant="outline" size="sm" asChild>
                <a
                  href="https://pypi.org/project/codegraphcontext/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  PyPI
                </a>
              </Button>
            </div>
          </div>

          {/* Links */}
          <div>
            <h4 className="font-semibold mb-4">Resources</h4>
            <ul className="space-y-3 text-muted-foreground">
              <li>
                <a
                  href="https://github.com/Shashankss1205/CodeGraphContext/blob/main/README.md"
                  className="hover:text-foreground transition-smooth"
                >
                  Documentation
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/Shashankss1205/CodeGraphContext/blob/main/cookbook.md"
                  className="hover:text-foreground transition-smooth"
                >
                  Cookbook
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/Shashankss1205/CodeGraphContext/blob/main/CONTRIBUTING.md"
                  className="hover:text-foreground transition-smooth"
                >
                  Contributing
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/Shashankss1205/CodeGraphContext/issues"
                  className="hover:text-foreground transition-smooth"
                >
                  Issues
                </a>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-semibold mb-4">Contact</h4>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-muted-foreground">
                <Mail className="h-4 w-4" />
                <a
                  href="mailto:shashankshekharsingh1205@gmail.com"
                  className="hover:text-foreground transition-smooth text-sm break-all"
                >
                  shashankshekharsingh1205@gmail.com
                </a>
              </div>
              <div className="text-muted-foreground">
                <p className="font-medium">Shashank Shekhar Singh</p>
                <p className="text-sm">Creator & Maintainer</p>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-border/50 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-muted-foreground text-sm">
            © 2025 CodeGraphContext. Released under the MIT License.
          </p>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>Version {version}</span>
            <div className="w-1 h-1 bg-muted-foreground rounded-full" />
            <span>Python 3.8+</span>
            <div className="w-1 h-1 bg-muted-foreground rounded-full" />
            <span>Neo4j 5.15+</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
