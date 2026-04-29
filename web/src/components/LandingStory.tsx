"use client";

import Image from "next/image";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { FadeIn } from "@/components/motion/FadeIn";
import { ThemeToggle } from "@/components/ThemeToggle";

const pillars = [
  {
    title: "Documents, understood.",
    body: "Ingest invoices and receipts. Structure emerges automatically.",
  },
  {
    title: "Spend, in context.",
    body: "Ask questions in plain language. Answers grounded in your data.",
  },
  {
    title: "Built for clarity.",
    body: "Minimal surface. Maximum signal. Nothing extra.",
  },
];

export function LandingStory() {
  const reduce = useReducedMotion();

  return (
    <div className="landing-story relative min-h-screen overflow-x-hidden bg-[#fbfbfd] text-neutral-900 dark:bg-[#050505] dark:text-neutral-100">
      <div
        className="landing-quirk-blob pointer-events-none absolute -right-24 top-32 h-72 w-72 rounded-full bg-teal-400/20 blur-3xl dark:bg-teal-500/10"
        aria-hidden
      />
      <div
        className="landing-quirk-blob landing-quirk-blob--delay pointer-events-none absolute -left-16 top-[60vh] h-64 w-64 rounded-full bg-violet-400/15 blur-3xl dark:bg-neutral-700/20"
        aria-hidden
      />

      <header className="sticky top-0 z-50 border-b border-black/[0.06] bg-[#fbfbfd]/80 backdrop-blur-xl dark:border-neutral-800 dark:bg-[#050505]/95 dark:backdrop-blur-md">
        <div className="mx-auto flex h-[3.75rem] max-w-6xl items-center justify-between px-6 sm:h-[4.25rem] sm:px-8">
          <motion.div
            whileHover={reduce ? undefined : { scale: 1.03 }}
            whileTap={reduce ? undefined : { scale: 0.98 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
          >
            <Link href="/" className="flex items-center gap-3">
              <Image
                src="/logo.png"
                alt="DocSage"
                width={220}
                height={60}
                className="h-11 w-auto sm:h-14 dark:hidden"
                priority
              />
              <Image
                src="/logo-dark.png"
                alt="DocSage"
                width={220}
                height={60}
                className="hidden h-11 w-auto sm:h-14 dark:block"
                priority
              />
            </Link>
          </motion.div>
          <div className="flex items-center gap-3 sm:gap-4">
            <ThemeToggle />
            <motion.div
              whileHover={reduce ? undefined : { y: -2 }}
              whileTap={reduce ? undefined : { y: 0 }}
              transition={{ type: "spring", stiffness: 500, damping: 28 }}
            >
              <Link
                href="/dashboard"
                className="group inline-flex items-center gap-1 text-sm font-medium text-teal-700 transition hover:text-teal-600 dark:text-teal-400 dark:hover:text-teal-300"
              >
                Open app
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </motion.div>
          </div>
        </div>
      </header>

      <main>
        <section className="relative mx-auto max-w-6xl px-6 pb-28 pt-24 sm:px-8 sm:pb-40 sm:pt-28 md:pb-44 md:pt-36 lg:pt-44">
          <div
            className="landing-quirk-dot pointer-events-none absolute right-[12%] top-8 h-3 w-3 rounded-full bg-teal-500/70 dark:bg-teal-500"
            aria-hidden
          />
          {/* Static hero copy on first paint (avoids SSR/hydration stuck at opacity:0 before animate runs) */}
          <h1 className="max-w-4xl text-4xl font-semibold leading-[1.08] tracking-tight text-neutral-900 dark:text-white sm:text-6xl md:text-7xl md:leading-[1.05]">
            Intelligence
            <br />
            for every document.
          </h1>
          <p className="mt-10 max-w-xl text-lg leading-relaxed text-neutral-500 dark:text-neutral-400 sm:text-xl">
            DocSage turns unstructured files into structured insight—quietly, precisely,
            without the noise.
          </p>
        </section>

        <section className="border-t border-black/[0.06] bg-white px-6 py-32 dark:border-neutral-800 dark:bg-[#0a0a0a] sm:px-8 md:py-40">
          <div className="mx-auto max-w-6xl">
            <FadeIn>
              <div className="max-w-3xl">
                <h2 className="text-3xl font-semibold tracking-tight text-neutral-900 dark:text-white sm:text-4xl">
                  Our mission
                </h2>
                <p className="mt-6 text-lg leading-relaxed text-neutral-600 dark:text-neutral-300 sm:text-xl">
                  Help people and teams trust what is in their documents—without drowning in
                  folders, spreadsheets, or opaque tools.
                </p>
                <p className="mt-6 text-base leading-relaxed text-neutral-500 dark:text-neutral-400 sm:text-lg">
                  DocSage exists because most financial and operational truth still lives in PDFs
                  and images. We built it to close the gap between &ldquo;we have the files&rdquo;
                  and &ldquo;we understand the story&rdquo;: structured data, anomalies you can
                  explain, and answers you can trace—so you spend less time reconciling and more
                  time deciding.
                </p>
              </div>
            </FadeIn>
          </div>
        </section>

        <section className="border-t border-black/[0.06] px-6 py-32 dark:border-neutral-800 sm:px-8 md:py-40">
          <div className="mx-auto max-w-6xl space-y-24 md:space-y-36">
            {pillars.map((pillar, i) => (
              <FadeIn key={pillar.title} delay={i * 0.06}>
                <div className="group max-w-3xl rounded-2xl border border-transparent bg-transparent p-6 transition duration-300 hover:-translate-y-1 hover:border-teal-200/40 hover:bg-white/60 hover:shadow-lg hover:shadow-teal-900/5 dark:hover:border-teal-600/35 dark:hover:bg-teal-500/[0.06] dark:hover:shadow-[0_0_40px_-12px_rgba(13,148,136,0.18)] md:p-8">
                  <h2 className="text-3xl font-semibold tracking-tight text-neutral-900 dark:text-white sm:text-4xl md:text-5xl">
                    {pillar.title}
                  </h2>
                  <p className="mt-6 max-w-md text-lg leading-relaxed text-neutral-500 dark:text-neutral-400">
                    {pillar.body}
                  </p>
                </div>
              </FadeIn>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-32 sm:px-8 md:py-44">
          <FadeIn>
            <div className="flex flex-col items-start gap-10 sm:gap-14">
              <p className="max-w-lg text-2xl font-semibold leading-snug tracking-tight text-neutral-800 dark:text-white sm:text-3xl">
                Ready when you are.
              </p>
              <motion.div
                whileHover={reduce ? undefined : { x: 4 }}
                whileTap={reduce ? undefined : { scale: 0.98 }}
                transition={{ type: "spring", stiffness: 420, damping: 24 }}
              >
                <Link
                  href="/dashboard"
                  className="group inline-flex items-center gap-2 text-base font-medium text-teal-700 underline decoration-teal-400/40 underline-offset-[10px] transition hover:decoration-teal-600 dark:text-teal-400 dark:decoration-teal-500/45 dark:hover:text-teal-300 dark:hover:decoration-teal-400"
                >
                  Enter DocSage
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </motion.div>
            </div>
          </FadeIn>
        </section>
      </main>

      <footer className="border-t border-black/[0.06] py-12 dark:border-neutral-800">
        <div className="mx-auto max-w-6xl px-6 text-center text-xs text-neutral-400 dark:text-neutral-600 sm:px-8">
          DocSage
        </div>
      </footer>
    </div>
  );
}
