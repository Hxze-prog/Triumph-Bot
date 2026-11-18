import Image from "next/image";
import Link from "next/link";

type BrandProps = {
  href?: string | null;
  compact?: boolean;
  className?: string;
};

export function Brand({ href = "/", compact = false, className = "" }: BrandProps) {
  const content = (
    <span className={`flex items-center gap-3 ${className}`}>
      <span className="relative flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-gold-500/30 bg-navy-900 shadow-[0_0_28px_-10px_rgba(212,175,55,0.7)]">
        <Image
          src="/triumph-icon.png"
          alt="Triumph logo"
          width={44}
          height={44}
          priority
          className="h-full w-full object-contain p-1"
        />
      </span>
      {!compact ? (
        <span className="flex flex-col leading-none">
          <span className="font-display text-lg font-semibold tracking-[0.3em] text-mist-100">
            TRIUMPH
          </span>
          <span className="mt-1 text-[10px] uppercase tracking-[0.22em] text-mist-500">
            Discord command center
          </span>
        </span>
      ) : null}
    </span>
  );

  if (!href) {
    return content;
  }

  return (
    <Link href={href} className="inline-flex" aria-label="Triumph home">
      {content}
    </Link>
  );
}
