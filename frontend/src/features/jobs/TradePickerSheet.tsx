"use client";

import { useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { Sheet } from "@/components/ui/Sheet";
import { findSkill, searchSkills, type SkillOption } from "@/core/format/trades";

type Props = {
  isOpen: boolean;
  selectedId: string | null;
  onClose: () => void;
  onSelect: (skill: SkillOption) => void;
};

/** Design E3 · Pick the skill needed. */
export function TradePickerSheet({ isOpen, selectedId, onClose, onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [pendingId, setPendingId] = useState<string | null>(selectedId);
  const pending = findSkill(pendingId);
  const groups = searchSkills(query);

  function handleDone(): void {
    if (pending) onSelect(pending);
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
          disabled={!pending}
          onClick={handleDone}
        >
          {pending ? `Done — ${pending.label}` : "Pick a skill"}
        </button>
      }
    >
      <label className="search" style={{ marginTop: -4 }}>
        <Icon name="search" />
        <input
          type="search"
          placeholder="Search, e.g. tiler, welder, solar"
          aria-label="Search skills"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>
      {groups.length === 0 && <p className="meta meta--secondary">No skills match “{query}”.</p>}
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
