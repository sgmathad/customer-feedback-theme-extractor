import React from "react";
import { motion } from "framer-motion";
import { type SentimentCounts } from "@/interfaces";

interface SentimentChartProps {
    counts: SentimentCounts;
    title?: string;
    compact?: boolean;
}

const COLORS = {
    positive: { bar: "bg-emerald-500", text: "text-emerald-600", label: "Positive" },
    neutral: { bar: "bg-amber-400", text: "text-amber-600", label: "Neutral" },
    negative: { bar: "bg-rose-500", text: "text-rose-600", label: "Negative" },
};

export const SentimentChart: React.FC<SentimentChartProps> = ({ counts, title, compact = false }) => {
    const total = (counts.positive + counts.neutral + counts.negative) || 1;

    const bars: { key: keyof SentimentCounts; pct: number }[] = [
        { key: "positive", pct: (counts.positive / total) * 100 },
        { key: "neutral", pct: (counts.neutral / total) * 100 },
        { key: "negative", pct: (counts.negative / total) * 100 },
    ];

    if (compact) {
        // Stacked bar for theme cards
        return (
            <div className="w-full">
                <div className="flex h-2 rounded-full overflow-hidden gap-px">
                    {bars.map(({ key, pct }) => (
                        <motion.div
                            key={key}
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.6, ease: "easeOut" }}
                            className={`h-full ${COLORS[key].bar}`}
                            title={`${COLORS[key].label}: ${pct.toFixed(0)}%`}
                        />
                    ))}
                </div>
                <div className="flex justify-between mt-1">
                    {bars.map(({ key, pct }) => (
                        <span key={key} className={`text-xs ${COLORS[key].text}`}>
                            {pct.toFixed(0)}%
                        </span>
                    ))}
                </div>
            </div>
        );
    }

    // Full chart for dashboard
    return (
        <div className="w-full">
            {title && <h4 className="text-sm font-semibold text-slate-700 mb-3">{title}</h4>}
            <div className="space-y-3">
                {bars.map(({ key, pct }) => (
                    <div key={key} className="flex items-center gap-3">
                        <span className={`w-16 text-xs font-medium ${COLORS[key].text}`}>
                            {COLORS[key].label}
                        </span>
                        <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${pct}%` }}
                                transition={{ duration: 0.7, ease: "easeOut", delay: 0.1 }}
                                className={`h-full rounded-full ${COLORS[key].bar}`}
                            />
                        </div>
                        <span className="w-10 text-xs text-right text-slate-500">
                            {pct.toFixed(0)}%
                        </span>
                        <span className="w-8 text-xs text-right text-slate-400">
                            ({counts[key]})
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
};

SentimentChart.displayName = "SentimentChart";