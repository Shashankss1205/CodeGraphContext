"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";

const tableData = [
  {
    feature: "Code Completion",
    copilot: { text: "Strong", status: "good" },
    cursor: { text: "Strong", status: "good" },
    cgc: { text: "Strong", status: "good" },
  },
  {
    feature: "Refactoring Suggestions",
    copilot: { text: "Limited to context length", status: "warning" },
    cursor: { text: "Limited to context length", status: "warning" },
    cgc: { text: "Via dependency tracing", status: "good" },
  },
  {
    feature: "Codebase Understanding",
    copilot: { text: "Limited", status: "bad" },
    cursor: { text: "Partial (local context)", status: "warning" },
    cgc: { text: "Deep graph-based", status: "good" },
  },
  {
    feature: "Call Graph & Imports",
    copilot: { text: "No", status: "bad" },
    cursor: { text: "No", status: "bad" },
    cgc: { text: "Direct + Multi-hops", status: "good" },
  },
  {
    feature: "Cross-File Tracing",
    copilot: { text: "Very low", status: "bad" },
    cursor: { text: "Some", status: "warning" },
    cgc: { text: "Complete code", status: "good" },
  },
  {
    feature: "LLM Explainability",
    copilot: { text: "Low", status: "bad" },
    cursor: { text: "Hallucinate", status: "warning" },
    cgc: { text: "Extremely good", status: "good" },
  },
  {
    feature: "Performance on Large Codebases",
    copilot: { text: "Slows with size", status: "bad" },
    cursor: { text: "Slows with size", status: "bad" },
    cgc: { text: "Scales with graph DB", status: "good" },
  },
  {
    feature: "Extensible to Multiple Languages",
    copilot: { text: "Strong", status: "good" },
    cursor: { text: "Strong", status: "good" },
    cgc: { text: "Work-in-progress", status: "warning" },
  },
  {
    feature: "Set-up Time for new code",
    copilot: { text: "Low", status: "good" },
    cursor: { text: "Slows with size", status: "bad" },
    cgc: { text: "Slows with size", status: "bad" },
  },
];

const StatusBadge = ({ status, text }: { status: string; text: string }) => {
  const getStatusStyles = () => {
    switch (status) {
      case "good":
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-lg shadow-emerald-500/10";
      case "warning":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-lg shadow-amber-500/10";
      case "bad":
        return "bg-red-500/20 text-red-300 border-red-500/40 shadow-lg shadow-red-500/10";
      default:
        return "bg-secondary/50 text-muted-foreground";
    }
  };

  const getIcon = () => {
    switch (status) {
      case "good":
        return "✓";
      case "warning":
        return "⚠";
      case "bad":
        return "✕";
      default:
        return "";
    }
  };

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: "spring", stiffness: 400, damping: 17 }}
    >
      <Badge
        className={` 
          ${getStatusStyles()} 
          border-2 font-medium text-[0.65rem] px-3 py-1.5 
          backdrop-blur-sm relative overflow-hidden
          transition-all duration-300 hover:shadow-xl
        `}
      >
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent"
          initial={{ x: "-100%" }}
          whileHover={{ x: "100%" }}
          transition={{ duration: 0.6 }}
        />
        <span className="mr-2 font-bold">{getIcon()}</span>
        <span className="relative z-10">{text}</span>
      </Badge>
    </motion.div>
  );
};

const AnimatedCard = ({
  children,
  delay = 0,
}: {
  children: React.ReactNode;
  delay?: number;
}) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
};

const FloatingBackground = () => (
  <div className="absolute inset-0 overflow-hidden pointer-events-none">
    <motion.div
      className="absolute -top-40 -right-40 w-80 h-80 bg-primary/5 rounded-full blur-3xl"
      animate={{
        x: [0, 30, 0],
        y: [0, -40, 0],
      }}
      transition={{
        duration: 20,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    />
    <motion.div
      className="absolute -bottom-40 -left-40 w-80 h-80 bg-accent/5 rounded-full blur-3xl"
      animate={{
        x: [0, -30, 0],
        y: [0, 40, 0],
      }}
      transition={{
        duration: 25,
        repeat: Infinity,
        ease: "easeInOut",
        delay: 2,
      }}
    />
  </div>
);

export default function ComparisonTable() {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });

  return (
    <section
      ref={containerRef}
      className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-secondary/5 overflow-hidden"
      style={{
        maxWidth: "100vw",
        overflow: "hidden",
        padding: "2rem 1rem",
      }}
    >
      <FloatingBackground />

      <div className="container mx-auto max-w-7xl relative z-10">
        <AnimatedCard delay={0.1}>
          <div className="text-center mb-16">
            <motion.h2
              className="text-2xl sm:text-4xl md:text-5xl font-bold mb-6 pb-4 bg-gradient-to-r from-primary via-primary/90 to-accent bg-clip-text text-transparent"
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              Why CodeGraphContext?
            </motion.h2>
            <motion.p
              className="text-lg text-muted-foreground max-w-3xl mx-auto leading-relaxed"
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              Experience the next generation of AI-powered code understanding
              with graph-based intelligence
            </motion.p>
          </div>
        </AnimatedCard>

        <AnimatedCard delay={0.3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={isInView ? { opacity: 1, scale: 1 } : {}}
            transition={{ duration: 0.8, delay: 0.5 }}
          >
            <Card className="bg-background/70 backdrop-blur-xl border-border/30 shadow-2xl shadow-primary/5 rounded-3xl overflow-hidden">
              <CardContent className="p-0">
                <div className="overflow-hidden rounded-3xl">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border/20 bg-gradient-to-r from-secondary/10 via-secondary/5 to-secondary/10 backdrop-blur-sm">
                        <th className="p-4 sm:p-6 text-left font-bold text-foreground text-sm sm:text-base">
                          <motion.span
                            initial={{ opacity: 0, x: -20 }}
                            animate={isInView ? { opacity: 1, x: 0 } : {}}
                            transition={{ duration: 0.6, delay: 0.7 }}
                          >
                            Feature
                          </motion.span>
                        </th>
                        <th className="p-4 sm:p-6 text-center font-bold text-foreground text-sm sm:text-base min-w-[140px]">
                          <motion.span
                            initial={{ opacity: 0, y: -20 }}
                            animate={isInView ? { opacity: 1, y: 0 } : {}}
                            transition={{ duration: 0.6, delay: 0.8 }}
                          >
                            GitHub Copilot
                          </motion.span>
                        </th>
                        <th className="p-4 sm:p-6 text-center font-bold text-foreground text-sm sm:text-base min-w-[140px]">
                          <motion.span
                            initial={{ opacity: 0, y: -20 }}
                            animate={isInView ? { opacity: 1, y: 0 } : {}}
                            transition={{ duration: 0.6, delay: 0.9 }}
                          >
                            Cursor
                          </motion.span>
                        </th>
                        <th className="p-4 sm:p-6 text-center font-bold text-primary text-sm sm:text-base min-w-[140px] relative">
                          <motion.span
                            initial={{ opacity: 0, y: -20 }}
                            animate={isInView ? { opacity: 1, y: 0 } : {}}
                            transition={{ duration: 0.6, delay: 1.0 }}
                            className="relative"
                          >
                            CodeGraphContext
                          </motion.span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {tableData.map((row, index) => (
                        <motion.tr
                          key={row.feature}
                          initial={{ opacity: 0, x: -20 }}
                          animate={isInView ? { opacity: 1, x: 0 } : {}}
                          transition={{
                            duration: 0.6,
                            delay: 0.7 + index * 0.1,
                          }}
                          className={`
                            border-b border-border/10 transition-all duration-300 
                            hover:bg-primary/5 group relative overflow-hidden
                            ${
                              index % 2 === 0
                                ? "bg-background/30"
                                : "bg-secondary/3"
                            }
                          `}
                        >
                          <motion.td
                            className="p-4 sm:p-6 text-foreground font-semibold text-xs sm:text-sm relative z-10"
                            whileHover={{ x: 8 }}
                            transition={{
                              type: "spring",
                              stiffness: 400,
                              damping: 25,
                            }}
                          >
                            {row.feature}
                            <motion.div
                              className="absolute left-0 top-0 w-1 h-0 bg-gradient-to-b from-primary to-accent group-hover:h-full transition-all duration-500"
                              initial={{ height: 0 }}
                              whileHover={{ height: "100%" }}
                            />
                          </motion.td>
                          <td className="p-4 sm:p-6 text-center">
                            <div className="flex justify-center">
                              <StatusBadge
                                status={row.copilot.status}
                                text={row.copilot.text}
                              />
                            </div>
                          </td>
                          <td className="p-4 sm:p-6 text-center">
                            <div className="flex justify-center">
                              <StatusBadge
                                status={row.cursor.status}
                                text={row.cursor.text}
                              />
                            </div>
                          </td>
                          <td className="p-4 sm:p-6 text-center relative">
                            <div className="flex justify-center">
                              <StatusBadge
                                status={row.cgc.status}
                                text={row.cgc.text}
                              />
                            </div>
                            {row.cgc.status === "good" && (
                              <motion.div
                                className="absolute inset-0 bg-gradient-to-r from-primary/5 to-accent/5 rounded-lg"
                                initial={{ opacity: 0 }}
                                whileHover={{ opacity: 1 }}
                                transition={{ duration: 0.3 }}
                              />
                            )}
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </AnimatedCard>

        <AnimatedCard delay={0.9}>
          <motion.div
            className="text-center mt-12"
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8, delay: 1.5 }}
          >
            <motion.p
              className="text-base text-muted-foreground mb-6"
              initial={{ opacity: 0 }}
              animate={isInView ? { opacity: 1 } : {}}
              transition={{ duration: 0.8, delay: 1.7 }}
            >
              Experience the power of graph-based code understanding
            </motion.p>
            
          </motion.div>
        </AnimatedCard>
      </div>
    </section>
  );
}
