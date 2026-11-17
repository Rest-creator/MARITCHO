"use client";

import { useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { Sheet } from "@/components/ui/Sheet";
import {
  composeSkillWithWriteIn,
  findSkill,
  searchSkills,
  type SkillOption,
} from "@/core/format/trades";

type Props = {
  isOpen: boolean;
  selectedId: string | null;
  initialWriteIn?: string;
  onClose: () => void;
  onSelect: (skill: SkillOption) => void;
  onWriteInChange?: (writeIn: string) => void;
};

/** Design E3 · Pick the skill needed, or write in on top of your pick. */
export function TradePickerSheet({
  isOpen,
  selectedId,
  initialWriteIn = "",
  onClose,
  onSelect,
  onWriteInChange,
}: Props) {
  const [query, setQuery] = useState("");
  const [pendingId, setPendingId] = useState<string | null>(selectedId);
  const [writeIn, setWriteIn] = useState(initialWriteIn);
  const pending = findSkill(pendingId) ?? null;
  const groups = searchSkills(query);
  const resolved =
    composeSkillWithWriteIn(pending, writeIn) ??
    (query.trim() !== "" && groups.length === 0 ? composeSkillWithWriteIn(null, query) : null);

  function handleDone(): void {
    if (!resolved) return;
    const effectiveWriteIn =
      writeIn.trim() !== ""
        ? writeIn.trim()
        : pending === null && query.trim() !== ""
          ? query.trim()
          : "";
    if (onWriteInChange) {
      onWriteInChange(effectiveWriteIn);
      onSelect(pending ?? findSkill(resolved.id) ?? resolved);
    } else {
      onSelect(resolved);
    }
    onClose();
  }

  return (
    <Sheet
      title="Who do you need?"
      isOpen={isOpen}
      onClose={onClose}
      footer={
        <button
          type="button"
          className="btn btn--primary btn--cta"
          disabled={!resolved}
          onClick={handleDone}
        >
          {resolved ? `Done — ${resolved.label}` : "Pick a skill"}
        </button>
      }
    >
      <label className="search">
        <Icon name="search" />
        <input
          type="search"
          placeholder="Search, e.g. tiler, welder, solar"
          aria-label="Search skills"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>
      <div className="field" style={{ gap: 6 }}>
        <label htmlFor="tp-writein" className="field__label">
          Write in on top of your pick (optional)
        </label>
        <input
          id="tp-writein"
          type="text"
          className="input input--compact"
          placeholder={
            pending
              ? `Add details on top of ${pending.label} (e.g. geyser, ceiling)…`
              : "Or write in who you want (e.g. borehole plumber, carpenter)…"
          }
          aria-label="Write in on top of your pick"
          value={writeIn}
          maxLength={80}
          onChange={(event) => setWriteIn(event.target.value)}
        />
      </div>
      {groups.length === 0 && (
        <p className="meta meta--secondary">
          No preset skills match “{query}” — tap Done below to use it as a write-in.
        </p>
      )}
      {groups.map((group) => (
        <section key={group.title} aria-label={group.title}>
          <div className="eyebrow">{group.title}</div>
          <div className="chip-list" style={{ marginTop: 10 }}>
            {group.skills.map((skill) => {
              const isAvailable = skill.trade !== null;
              const isSelected = skill.id === pendingId;
              return (
                <button
                  key={skill.id}
                  type="button"
                  className="chip"
                  aria-pressed={isSelected}
                  disabled={!isAvailable}
                  onClick={() => setPendingId(skill.id)}
                >
                  {isSelected && <Icon name="check" size={16} strokeWidth={2.4} />}
                  {skill.label}
                  {!isAvailable && <span className="chip__soon">SOON</span>}
                </button>
              );
            })}
          </div>
        </section>
      ))}
    </Sheet>
  );
}
