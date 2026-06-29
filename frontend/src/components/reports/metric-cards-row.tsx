import type { ReactNode } from 'react';
import { MetricCardSmall, type MetricCardData } from './shared';

export interface MetricCardsRowProps {
  cards: MetricCardData[];
  columns?: 3 | 4 | 6;
}

const gridCols = {
  3: 'grid-cols-1 sm:grid-cols-3',
  4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  6: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6',
};

export function MetricCardsRow({ cards, columns = 4 }: MetricCardsRowProps) {
  if (cards.length === 0) return null;
  return (
    <div className={`grid gap-4 ${gridCols[columns]}`}>
      {cards.map((card, i) => (
        <MetricCardSmall key={i} {...card} />
      ))}
    </div>
  );
}