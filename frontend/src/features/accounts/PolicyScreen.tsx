import Link from "next/link";

import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";

type Props = { title: string };

interface PolicySection {
  heading: string;
  paragraphs: string[];
  bullets?: string[];
}

const TERMS_SECTIONS: readonly PolicySection[] = [
  {
    heading: "1. About Maritcho",
    paragraphs: [
      "Maritcho connects households, small businesses, and organizations (Employers / Buyers) with skilled tradespeople (Workers) across Zimbabwe. Using Maritcho to find work is free for workers.",
      "By creating an account, posting a job, or submitting an offer on Maritcho, you agree to these Terms and Conditions.",
    ],
  },
  {
    heading: "2. Job Pricing & Negotiation (Fixed, Negotiable & Price After Visit)",
    paragraphs: ["When posting a job, an employer may choose one of three pricing modes:"],
    bullets: [
      "Fixed price: The employer sets a clear price upfront. Workers can accept that price in one tap.",
      "Negotiable price (inDrive-style): The employer suggests a budget, and workers can either accept the suggested price or offer the price they are willing to do the work for. The employer reviews all offers, track records, and proximity before approving the worker they want.",
      "Price after visit: For jobs that need an on-site inspection before quoting, workers may visit first or suggest an initial estimate, and confirm the final labour + materials price once on site.",
    ],
  },
  {
    heading: "3. Deposits, On-Site Quotes & Payment Release",
    paragraphs: [
      "When an employer approves a worker, a booking deposit is held in the chosen settlement currency (Cash USD, EcoCash, or ZWG).",
      "Upon arriving at the job, the worker confirms the full quote split into labour and materials. Once the work is finished and the employer signs off, the balance is released and an immutable work record is added to the worker's Maritcho profile.",
    ],
  },
  {
    heading: "4. Redo Guarantee & Dispute Resolution",
    paragraphs: [
      "If an employer raises a concern before signing off, payment is placed on hold and the worker's standing is paused (never automatically penalised without a chance to respond).",
      "The worker is given the opportunity to respond with photos or notes and arrange a return visit to put the work right.",
    ],
  },
  {
    heading: "5. Worker Vetting & Police Clearance Verification",
    paragraphs: [
      "Workers can join Maritcho and browse jobs immediately as Registered tradespeople. To unlock higher trust tiers and verification badges:",
    ],
    bullets: [
      "National ID check: A worker submits a clear photo of their National ID. Once the Maritcho team has checked it, the worker reaches the ID Checked tier.",
      "Police Clearance Certificate (optional): After the worker's ID is checked, the Maritcho team checks the certificate against it. The Police Cleared badge is shown to employers for 12 months from the certificate's issue date. It means Maritcho checked the certificate; the Zimbabwe Republic Police do not offer an online check.",
      "Client References & Peer Vouches: Contactable client references and vouches from Journeyman or Expert tradespeople unlock Apprentice, Journeyman, and Expert tiers.",
    ],
  },
  {
    heading: "6. Editing Job Postings & Accurate Information",
    paragraphs: [
      "Employers can edit an open job posting (skill, description, location, timing, or pricing mode) at any time before a worker is booked if they need to correct a mistake.",
      "Exact street addresses, landmark directions, and GPS coordinates are kept private on open listings and revealed only to the worker the employer approves.",
    ],
  },
];

const PRIVACY_SECTIONS: readonly PolicySection[] = [
  {
    heading: "1. Information We Collect",
    paragraphs: [
      "We collect only the information needed to match employers and skilled workers safely and reliably:",
    ],
    bullets: [
      "Account details: Your name, Zimbabwean mobile number (+263), password (stored as a secure cryptographic hash), and optional next-of-kin emergency contact number.",
      "Location details: Your suburb, street address, landmark directions, and optional device GPS coordinates when you tap 'Use my location'.",
      "Work & vetting records: Trade skills, photos of past work, job offers, signed-off job history, National ID photo, Police Clearance certificate image, and client reference contacts.",
    ],
  },
  {
    heading: "2. How Your Location & Address Are Protected",
    paragraphs: [
      "Open job listings show only the suburb and approximate distance (e.g. 'Same suburb · 0.8 km') so nearby workers can judge travel.",
      "Your street address, landmark directions, and GPS pin are never shown on public job boards — they are shared only with the specific worker you approve and hire.",
    ],
  },
  {
    heading: "3. Photos, Media & Data Bundles",
    paragraphs: [
      "To protect your privacy and save mobile data bundles, photos taken or selected in Maritcho are compressed on your device (≤1280 px JPEG) and stripped of embedded camera EXIF/GPS metadata before upload.",
      "Job and chat photos use tap-to-load previews so your phone never downloads large images without your permission.",
    ],
  },
  {
    heading: "4. Vetting Documents & Police Clearance",
    paragraphs: [
      "National ID photos and Police Clearance certificate images are used only to verify your identity. They are kept privately: only you and the Maritcho team can see them, and they are never shown to employers or other workers. Employers see only your verification status ('ID checked' and 'Police Cleared').",
      "From your ID we keep the name as printed and a coded (hashed) form of the ID number, so one ID can't be used for two accounts. The ID number itself is not stored.",
      "We do not sell or rent your personal information or vetting documents to third parties.",
    ],
  },
  {
    heading: "5. Offline Storage & Your Choices",
    paragraphs: [
      "Maritcho is built offline-first: recent jobs, messages, and your theme preference (Dark mode or White & Blue Light mode) are cached on your device so you can keep working when signal drops.",
      "You can update your name, suburb, travel reach, emergency contact, or verification documents at any time from your Account screen, or sign out to clear your active session.",
    ],
  },
];

/** Terms and Conditions & Privacy Policy screen. */
export function PolicyScreen({ title }: Props) {
  const isPrivacy = title.toLowerCase().includes("privacy");
  const sections = isPrivacy ? PRIVACY_SECTIONS : TERMS_SECTIONS;

  return (
    <Screen>
      <div className="topbar">
        <BackButton fallbackHref="/signup" />
        <div className="topbar__text">
          <h1 className="title">{isPrivacy ? "Privacy Policy" : "Terms and Conditions"}</h1>
          <div className="meta">Effective for Maritcho Zimbabwe · Updated 2026</div>
        </div>
      </div>

      <div className="banner banner--emerald" style={{ borderRadius: 16 }}>
        <Icon name="shieldCheck" size={20} />
        <span>
          {isPrivacy
            ? "Your exact address and vetting documents stay private. Photos are compressed and stripped of camera GPS data on your phone."
            : "Clear pricing (Fixed, Negotiable, or Price after visit), held deposits, and fair work records for both employers and workers."}
        </span>
      </div>

      <div className="stack" style={{ gap: 12 }}>
        {sections.map((section) => (
          <section key={section.heading} className="card stack" style={{ gap: 8 }}>
            <h2 style={{ fontSize: 15, fontWeight: 700 }}>{section.heading}</h2>
            {section.paragraphs.map((paragraph) => (
              <p
                key={paragraph}
                className="meta meta--secondary"
                style={{ fontSize: 14, lineHeight: 1.55 }}
              >
                {paragraph}
              </p>
            ))}
            {section.bullets && (
              <ul
                className="meta meta--secondary"
                style={{
                  margin: "4px 0 0",
                  paddingLeft: 18,
                  fontSize: 13.5,
                  lineHeight: 1.55,
                  display: "flex",
                  flexDirection: "column",
                  gap: 6,
                }}
              >
                {section.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </div>

      <div className="card card--compact row row--between">
        <span className="meta">
          {isPrivacy ? "Looking for our service rules?" : "Want to see how we protect your data?"}
        </span>
        <Link href={isPrivacy ? "/terms" : "/privacy"} className="text-link">
          {isPrivacy ? "Terms and Conditions" : "Privacy Policy"}
        </Link>
      </div>
    </Screen>
  );
}
