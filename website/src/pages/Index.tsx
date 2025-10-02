import HeroSection from "@/components/HeroSection";
import FeaturesSection from "@/components/FeaturesSection";
import ExportShowcaseSection from "@/components/ExportShowcaseSection";
import InstallationSection from "@/components/InstallationSection";
import DemoSection from "@/components/DemoSection";
import InteractiveGraphSection from "@/components/InteractiveGraphSection";
import ExamplesSection from "@/components/ExamplesSection";
import CookbookSection from "@/components/CookbookSection";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <>
      <main className="min-h-screen">
        <HeroSection />
        <DemoSection />
        <InteractiveGraphSection />
        <FeaturesSection />
        <ExportShowcaseSection />
        <InstallationSection />
        <ExamplesSection />
        <CookbookSection />
      </main>
      <Footer />
    </>
  );
};

export default Index;