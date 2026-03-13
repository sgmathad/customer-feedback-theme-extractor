import React from "react";
import { motion } from "framer-motion";
import { Lightbulb } from "lucide-react";
import { type Recommendation } from "@/interfaces";

interface RecommendationsPanelProps {
    recommendations: Recommendation[];
}

const PRIORITY_STYLES = [
    "border-rose-300 bg-rose-50",
    "border-orange-300 bg-orange-50",
    "border-amber-200 bg-amber-50",
    "border-blue-200 bg-blue-50",
    "border-slate-200 bg-slate-50",
];

const BADGE_STYLES = [
    "bg-rose-500 text-white",
    "bg-orange-500 text-white",
    "bg-amber-500 text-white",
    "bg-blue-500 text-white",
    "bg-slate-400 text-white",
];

export const RecommendationsPanel: React.FC<RecommendationsPanelProps> = ({ recommendations }) => {
    return (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6">
            <div className="flex items-center gap-2 mb-5">
                <Lightbulb size={18} className="text-amber-500" />
                <h2 className="font-semibold text-slate-800 text-lg">What to Fix First</h2>
            </div>

            <div className="space-y-3">
                {recommendations.map((rec, i) => {
                    const cardStyle = PRIORITY_STYLES[Math.min(i, PRIORITY_STYLES.length - 1)];
                    const badgeStyle = BADGE_STYLES[Math.min(i, BADGE_STYLES.length - 1)];

                    return (
                        <motion.div
                            key={rec.priority}
                            initial={{ opacity: 0, x: -12 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.07 }}
                            className={`flex gap-4 p-4 rounded-xl border ${cardStyle}`}
                        >
                            <span
                                className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${badgeStyle}`}
                            >
                                {rec.priority}
                            </span>
                            <div>
                                <p className="font-semibold text-slate-800 text-sm">{rec.title}</p>
                                <p className="text-sm text-slate-600 mt-0.5 leading-relaxed">{rec.description}</p>
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
};

RecommendationsPanel.displayName = "RecommendationsPanel";