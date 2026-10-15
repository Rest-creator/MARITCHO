"use client";

import { useState, type FormEvent } from "react";

import { Icon } from "@/components/ui/Icon";
import type { Trade } from "@/core/api/schemas";
import { matchSkills, tradeLabel, TRADES, type SkillOption } from "@/core/format/trades";

type Props = {
  /** Skills already saved on the worker's account (can't be removed here). */
  registered: ReadonlySet<Trade>;
  /** Skills picked on this screen, not saved yet. */
  picked: readonly Trade[];
  max: number;
  onToggle: (trade: Trade) => void;
};

/**
 * "What work can you do?" — shows only the worker's own skills. The list of
 * all skills stays hidden until they tap "Add a skill" or type; typing
 * accepts everyday words or a sentence ("I fix geysers and leaking taps").
 */
export function SkillPicker({ registered, picked, max, onToggle }: Props) {
  const [isAdding, setIsAdding] = useState(false);
  const [query, setQuery] = useState("");

  const mine: Trade[] = [...registered, ...picked.filter((trade) => !registered.has(trade))];
  const isFull = mine.length >= max;
  const matches = matchSkills(query);
  const suggestions: SkillOption[] =
    query.trim() === ""
      ? TRADES.map((trade) => ({ id: trade, label: tradeLabel(trade), trade }))
      : matches;
  const available = suggestions.filter(
    (skill) => skill.trade === null || !mine.includes(skill.trade),
  );

  function add(skill: SkillOption): void {
    if (skill.trade === null || isFull) return;
    onToggle(skill.trade);
    setQuery("");
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const best = available.find((skill) => skill.trade !== null);
    if (best) add(best);
  }

  return (
    <section className="stack" style={{ gap: 12 }} aria-label="Your skills">
      {mine.length > 0 && (
        <div className="chip-list" role="list" aria-label="Skills you do">
          {mine.map((trade) => {
            const isSaved = registered.has(trade);
            return (
              <span key={trade} role="listitem" className="chip chip--emerald">
                <Icon name="check" size={16} strokeWidth={2.4} />
                {tradeLabel(trade)}
                {!isSaved && (
                  <button
                    type="button"
                    className="chip__remove"
                    aria-label={`Remove ${tradeLabel(trade)}`}
                    onClick={() => onToggle(trade)}
                  >
                    <Icon name="close" size={14} strokeWidth={2.4} />
                  </button>
                )}
              </span>
            );
          })}
        </div>
      )}

      {!isAdding ? (
        <button
          type="button"
          className="btn btn--soft"
          disabled={isFull}
          onClick={() => setIsAdding(true)}
        >
          <Icon name="plus" size={18} strokeWidth={2} />
          {isFull ? `That's ${max} skills — the most you can add` : "Add a skill"}
        </button>
      ) : (
        <form onSubmit={handleSubmit} className="stack" style={{ gap: 10 }}>
          <label className="search" style={{ height: 48 }}>
            <Icon name="search" />
            <input
              type="search"
              // The worker just tapped "Add a skill": put them straight in the box.
              autoFocus
              placeholder="Type what you do, e.g. I fix geysers"
              aria-label="Type a skill"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>

          {query.trim() !== "" && matches.length === 0 && (
            <p className="meta meta--secondary" role="status">
              No skill matches “{query.trim()}” yet. Try a simple word, like plumber or welding.
            </p>
          )}

          {available.length > 0 && (
            <div className="chip-list" role="group" aria-label="Skills you can add">
              {available.map((skill) =>
                skill.trade === null ? (
                  <button key={skill.id} type="button" className="chip" disabled>
                    {skill.label}
                    <span className="chip__soon">SOON</span>
                  </button>
                ) : (
                  <button
                    key={skill.id}
                    type="button"
                    className="chip"
                    disabled={isFull}
                    onClick={() => add(skill)}
                  >
                    <Icon name="plus" size={14} strokeWidth={2.4} />
                    {skill.label}
                  </button>
                ),
              )}
            </div>
          )}

          <button
            type="button"
            className="text-link"
            style={{ alignSelf: "flex-start" }}
            onClick={() => {
              setIsAdding(false);
              setQuery("");
            }}
          >
            Done adding
          </button>
        </form>
      )}
    </section>
  );
}
