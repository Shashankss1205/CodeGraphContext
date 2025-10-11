import { OrbitingCircles } from "./ui/orbiting-circles";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const avatars = [
  { imageUrl: "https://avatars.githubusercontent.com/u/161715841?v=4", profileUrl: "https://github.com/athaxv" },
  { imageUrl: "https://avatars.githubusercontent.com/u/20110627?v=4", profileUrl: "https://github.com/tomonarifeehan" },
  { imageUrl: "https://avatars.githubusercontent.com/u/106103625?v=4", profileUrl: "https://github.com/BankkRoll" },
  { imageUrl: "https://avatars.githubusercontent.com/u/59228569?v=4", profileUrl: "https://github.com/safethecode" },
  { imageUrl: "https://avatars.githubusercontent.com/u/59442788?v=4", profileUrl: "https://github.com/sanjay-mali" },
  { imageUrl: "https://avatars.githubusercontent.com/u/89768406?v=4", profileUrl: "https://github.com/itsarghyadas" },
];

export default function TestimonialSection() {
  const reviews = useMemo(() => [
    { quote: "We’ve cut our task completion time in half since adopting CodeGraphContext. The DX is phenomenal.", author: "Sarah L.", role: "Operations Manager" },
    { quote: "Querying code relationships is finally effortless. Our team relies on it daily.", author: "Miguel A.", role: "Tech Lead" },
    { quote: "The visual graph helps new engineers onboard dramatically faster.", author: "Priya K.", role: "Engineering Manager" },
    { quote: "Rock‑solid performance, great documentation, and fantastic support.", author: "Daniel W.", role: "Staff Engineer" },
  ], []);

  const [index, setIndex] = useState(0);
  const next = () => setIndex((i) => (i + 1) % reviews.length);
  const prev = () => setIndex((i) => (i - 1 + reviews.length) % reviews.length);

  return (
    <section className="py-24 px-4" data-aos="fade-in">
      <div className="container mx-auto max-w-6xl">
        <div className="text-center mb-16" data-aos="fade-down">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-primary via-primary to-accent bg-clip-text text-transparent py-2">
            What Teams Are Saying
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Real feedback from engineers and leaders using CodeGraphContext.
          </p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="relative mx-auto h-[400px] lg:h-[500px] w-full flex items-center justify-center overflow-hidden" data-aos="zoom-in">
            <OrbitingCircles iconSize={56} radius={180} speed={1.4}>
              {avatars.map((avatar, i) => (
                <a key={i} href={avatar.profileUrl} target="_blank" rel="noopener noreferrer">
                  <img src={avatar.imageUrl} alt={`avatar-${i}`} className="w-14 h-14 rounded-full border-2 border-white shadow-md dark:border-neutral-800" />
                </a>
              ))}
            </OrbitingCircles>
            <OrbitingCircles iconSize={44} radius={100} reverse speed={2}>
              {avatars.slice(1, 5).map((avatar, i) => (
                 <a key={i} href={avatar.profileUrl} target="_blank" rel="noopener noreferrer">
                    <img src={avatar.imageUrl} alt={`avatar-inner-${i}`} className="w-11 h-11 rounded-full border-2 border-white shadow-md dark:border-neutral-800" />
                 </a>
              ))}
            </OrbitingCircles>
          </div>

          <div data-aos="fade-left" data-aos-delay="200">
            <Card className="dark:bg-card/50 shadow-sm min-h-[300px] flex flex-col justify-between">
              <CardHeader>
                <CardTitle className="text-3xl md:text-4xl font-bold bg-gradient-primary bg-clip-text text-transparent py-2">
                  Teams Love It
                </CardTitle>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                  >
                    <CardDescription className="text-base md:text-lg text-muted-foreground pt-4">
                      “{reviews[index].quote}”
                    </CardDescription>
                  </motion.div>
                </AnimatePresence>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between gap-4">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={index}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.3, delay: 0.1 }}
                    >
                      <p className="font-semibold">{reviews[index].author}</p>
                      <p className="text-sm text-muted-foreground">{reviews[index].role}</p>
                    </motion.div>
                  </AnimatePresence>
                  <div className="flex gap-2">
                    <Button onClick={prev} size="icon" variant="outline"><ChevronLeft className="h-4 w-4" /></Button>
                    <Button onClick={next} size="icon"><ChevronRight className="h-4 w-4" /></Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  )
}

