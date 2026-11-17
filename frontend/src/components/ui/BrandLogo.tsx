type Props = {
  /** Hide from assistive tech when the surrounding UI already names the app. */
  isDecorative?: boolean;
};

/**
 * The one Maritcho logo lockup (mark on a white tile + lowercase wordmark),
 * used by every surface that shows the brand so they can't drift apart.
 * `/brand/mark-96.png` is the official mark at 96 px (≈7 KB): sharp at 2×
 * for the 26 px render, a fifth of the size of the old SVG-wrapped PNG.
 */
export function BrandLogo({ isDecorative = false }: Props) {
  return (
    <span className="brand" aria-hidden={isDecorative || undefined}>
      <span className="brand__mark">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/brand/mark-96.png" alt="" width={26} height={26} />
      </span>
      <span className="brand__name">Maritcho</span>
    </span>
  );
}
