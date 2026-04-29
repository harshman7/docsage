"use client";

import { FadeIn } from "@/components/motion/FadeIn";

export function PageHeader({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <FadeIn className="mb-8" y={16}>
      <header>
        <h1 className="font-display text-2xl font-semibold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          {title}
        </h1>
        {description ? (
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-neutral-400">
            {description}
          </p>
        ) : null}
      </header>
    </FadeIn>
  );
}
