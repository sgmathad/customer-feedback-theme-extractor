import React from "react";

interface SentimentBadgeProps {
    sentiment: "positive" | "neutral" | "negative";
    size?: "sm" | "md";
}

const CONFIG = {
    positive: { label: "Positive", classes: "bg-emerald-100 text-emerald-700 border-emerald-200" },
    neutral: { label: "Neutral", classes: "bg-amber-100  text-amber-700  border-amber-200" },
    negative: { label: "Negative", classes: "bg-rose-100   text-rose-700   border-rose-200" },
};

export const SentimentBadge: React.FC<SentimentBadgeProps> = ({ sentiment, size = "sm" }) => {
    const { label, classes } = CONFIG[sentiment] ?? CONFIG.neutral;
    const padding = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";
    return (
        <span className={`inline-flex items-center font-medium rounded-full border ${padding} ${classes}`}>
            {label}
        </span>
    );
};

SentimentBadge.displayName = "SentimentBadge";