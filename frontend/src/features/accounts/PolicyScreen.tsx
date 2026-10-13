import { BackButton } from "@/components/ui/BackButton";
import { Screen } from "@/components/ui/Screen";

type Props = { title: string };

/** Placeholder until the legal text for Stage One is approved. */
export function PolicyScreen({ title }: Props) {
  return (
    <Screen>
      <div className="topbar">
        <BackButton fallbackHref="/signup" />
        <h1 className="title">{title}</h1>
      </div>
      <div className="card">
        <p className="lead">
          The full {title.toLowerCase()} will be published here before Maricho opens to the public.
        </p>
      </div>
    </Screen>
  );
}
