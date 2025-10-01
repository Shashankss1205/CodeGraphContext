import HeroSection from "@/components/HeroSection";
import FeaturesSection from "@/components/FeaturesSection";
import InstallationSection from "@/components/InstallationSection";
import DemoSection from "@/components/DemoSection";
import InteractiveGraphSection from "@/components/InteractiveGraphSection";
import ExamplesSection from "@/components/ExamplesSection";
import CookbookSection from "@/components/CookbookSection";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <main className="min-h-screen">
      <HeroSection />
      <DemoSection />
      <InteractiveGraphSection />
      <FeaturesSection />
      <InstallationSection />
      <ExamplesSection />
      <CookbookSection />
      <Footer />
    </main>
  );
};

export default Index;
