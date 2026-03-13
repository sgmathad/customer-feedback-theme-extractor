import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, Quote } from "lucide-react";
import { type Theme } from "@/interfaces";
import { SentimentBadge } from "@/reusables";
import { SentimentChart } from "./SentimentChart";

interface ThemeCardProps {
    theme: Theme;
    rank: number;
}

export const ThemeCard: React.FC<ThemeCardProps> = ({ theme, rank }) => {
    const [expanded, setExpanded] = useState(false);

    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: rank * 0.05 }}
            className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow overflow-hidden"
        >
            {/* Header */}
            <div className="p-5">
                <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                        <span className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-700 text-sm font-bold flex items-center justify-center">
                            {rank}
                        </span>
                        <div className="min-w-0">
                            <h3 className="font-semibold text-slate-800 truncate">{theme.theme_name}</h3>
                            <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{theme.description}</p>
                        </div>
                    </div>
                    <div className="flex-shrink-0 text-right">
                        <span className="text-lg font-bold text-slate-700">{theme.count}</span>
                        <p className="text-xs text-slate-400">mentions</p>
                        <p className="text-xs text-blue-500 font-medium">{theme.percentage}%</p>
                    </div>
                </div>

                {/* Compact sentiment bar */}
                {theme.sentiment_counts && (
                    <div className="mt-4">
                        <SentimentChart counts={theme.sentiment_counts} compact />
                    </div>
                )}
            </div>

            {/* Expand toggle */}
            <button
                onClick={() => setExpanded((v) => !v)}
                className="w-full flex items-center justify-center gap-1 py-2 text-xs text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-colors border-t border-slate-100"
            >
                {expanded ? (
                    <>Hide quotes <ChevronUp size={14} /></>
                ) : (
                    <>Show {theme.quotes?.length ?? 0} quotes <ChevronDown size={14} /></>
                )}
            </button>

            {/* Quotes */}
            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25 }}
                        className="overflow-hidden"
                    >
                        <div className="px-5 pb-5 space-y-3">
                            {(theme.quotes ?? []).map((q, i) => (
                                <div
                                    key={i}
                                    className="flex gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100"
                                >
                                    <Quote size={14} className="text-slate-300 flex-shrink-0 mt-0.5" />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-slate-600 italic leading-relaxed">"{q.text}"</p>
                                        <div className="mt-1.5">
                                            <SentimentBadge sentiment={q.sentiment} />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

ThemeCard.displayName = "ThemeCard";