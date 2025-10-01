import { Button } from "@/components/ui/button";
import { Github, ExternalLink, Mail, MapPin, Phone } from "lucide-react";
import { FaDiscord } from "react-icons/fa";
import { useEffect, useState } from "react";
import { toast } from "sonner";

const Footer = () => {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
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
  const handleNewsletterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email) {
      toast.error("Please enter your email address");
      return;
    }

    if (!/\S+@\S+\.\S+/.test(email)) {
      toast.error("Please enter a valid email address");
      return;
    }

    setIsLoading(true);

    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      toast.success("Thank you for subscribing to our newsletter!");
      setEmail("");
    } catch (error) {
      toast.error("Failed to subscribe. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <footer className="border-t border-border/50 py-16 px-6 bg-muted/10">
      <div className="container mx-auto max-w-7xl">
        {/* Top Section */}
        <div className="flex flex-col lg:flex-row justify-between gap-12">
          {/* Left Side: Brand + Resources (closer together) */}
          <div className="flex-1 flex flex-col sm:flex-row gap-12">
            {/* Brand */}
            <div className="flex-1">
              <h3 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent mb-4">
                CodeGraphContext
              </h3>
              <p className="text-muted-foreground mb-6 leading-relaxed max-w-sm">
                Transform your codebase into an intelligent knowledge graph for
                AI assistants.
              </p>
              <div className="flex gap-3 flex-wrap">
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
                    href="https://discord.com/invite/dR4QY32uYQ"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <FaDiscord className="h-4 w-4 mr-2" />
                    Discord
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

            {/* Resources */}
            <div className="w-48">
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
          </div>

          {/* Right Side: Contact + Newsletter */}
          <div className="flex-1 flex flex-col sm:flex-row gap-12">
            {/* Contact */}
            <div className="w-56">
              <h4 className="font-semibold mb-4">Contact</h4>
              <div className="space-y-5 text-muted-foreground">
                <div className="flex items-start gap-3">
                  <Mail className="h-5 w-5 mt-1 text-primary" />
                  <a
                    href="mailto:shashankshekharsingh1205@gmail.com"
                    className="hover:text-foreground transition-smooth text-sm break-all"
                  >
                    shashankshekharsingh1205@gmail.com
                  </a>
                </div>
                {/* <div className="flex items-start gap-3">
                  <Phone className="h-5 w-5 mt-1 text-primary" />
                  <a
                    href="tel:+911234567890"
                    className="hover:text-foreground transition-smooth text-sm"
                  >
                    +91 12345 67890
                  </a>
                </div> */}
                <div className="flex items-start gap-3">
                  <MapPin className="h-5 w-5 mt-1 text-primary" />
                  <p className="text-sm">
                    (Available Worldwide 🌍)
                  </p>
                </div>
                <div>
                  <p className="font-medium text-foreground">
                    Shashank Shekhar Singh
                  </p>
                  <p className="text-sm">Creator & Maintainer</p>
                </div>
              </div>
            </div>

            {/* Newsletter */}
            <div className="flex-1">
              <h4 className="font-semibold mb-4">Newsletter</h4>
              <p className="text-muted-foreground mb-4 text-sm leading-relaxed">
                Stay updated with the latest features, releases, and code
                intelligence insights.
              </p>
              <form onSubmit={handleNewsletterSubmit} className="space-y-3">
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isLoading}
                    className="flex-1 px-3 py-2 text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-smooth disabled:opacity-50"
                    required
                  />
                  <Button
                    type="submit"
                    size="sm"
                    disabled={isLoading}
                    className="whitespace-nowrap"
                  >
                    {isLoading ? "Subscribing..." : "Subscribe"}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  No spam. Unsubscribe at any time.
                </p>
              </form>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
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
