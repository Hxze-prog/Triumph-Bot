export function PreviewNotice({ feature }: { feature: string }) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-royal-400/25 bg-royal-700/15 px-4 py-3 text-sm text-mist-300">
      <span className="inline-flex h-6 items-center rounded-full border border-royal-400/30 px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-royal-400">
        Read-only
      </span>
      <p>
        {feature} is displayed live from Supabase. Changes are still made from
        Discord for this section.
      </p>
    </div>
  );
}
