import HeroSection from "@/components/HeroSection";
import FeaturesSection from "@/components/FeaturesSection";
import ExportShowcaseSection from "@/components/ExportShowcaseSection";
import InstallationSection from "@/components/InstallationSection";
import DemoSection from "@/components/DemoSection";
import ExamplesSection from "@/components/ExamplesSection";
import CookbookSection from "@/components/CookbookSection";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <main className="min-h-screen">
      <HeroSection />
      <DemoSection />
      <FeaturesSection />
      <ExportShowcaseSection />
      <InstallationSection />
      <ExamplesSection />
      <CookbookSection />
      <Footer />
    </main>
  );
};

export default Index;
