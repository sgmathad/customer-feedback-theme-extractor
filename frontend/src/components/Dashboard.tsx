import React, { useState } from "react";
import { motion } from "framer-motion";
import { Download, ArrowLeft, BarChart2, MessageSquare, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { type AnalysisResult } from "@/interfaces";
import { SentimentChart } from "./SentimentChart";
import { ThemeCard } from "./ThemeCard";
import { RecommendationsPanel } from "./RecommendationsPanel";

interface DashboardProps {
    result: AnalysisResult;
}

export const Dashboard: React.FC<DashboardProps> = ({ result }) => {
    const navigate = useNavigate();
    const [downloading, setDownloading] = useState(false);

    const handleDownloadPdf = async () => {
        setDownloading(true);
        try {
            const response = await axios.get(
                `http://127.0.0.1:8000/results/${result.analysis_id}/pdf`,
                { responseType: "blob" }
            );
            const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", `feedback_report_${result.analysis_id}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (e) {
            console.error("PDF download failed:", e);
        } finally {
            setDownloading(false);
        }
    };

    const stats = [
        {
            label: "Total Feedback",
            value: result.total_feedback,
            icon: MessageSquare,
            color: "text-blue-600",
            bg: "bg-blue-50",
        },
        {
            label: "Themes Found",
            value: result.num_themes,
            icon: BarChart2,
            color: "text-purple-600",
            bg: "bg-purple-50",
        },
        {
            label: "Processed",
            value: result.processed_feedback,
            icon: Users,
            color: "text-emerald-600",
            bg: "bg-emerald-50",
        },
    ];

    return (
        <div className="min-h-screen bg-gray-50 py-10 px-4">
            <div className="max-w-5xl mx-auto">

                {/* Top bar */}
                <div className="flex items-center justify-between mb-8">
                    <button
                        onClick={() => navigate("/upload")}
                        className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 transition-colors"
                    >
                        <ArrowLeft size={16} /> Back to Upload
                    </button>
                    <motion.button
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={handleDownloadPdf}
                        disabled={downloading}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        <Download size={15} />
                        {downloading ? "Generating PDF…" : "Download Report"}
                    </motion.button>
                </div>

                {/* Title */}
                <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8 text-center"
                >
                    <h1 className="text-3xl font-bold text-slate-800">Feedback Insights</h1>
                    <p className="text-slate-500 mt-1 text-sm">{result.message}</p>
                </motion.div>

                {/* Stat cards */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                    {stats.map((s, i) => (
                        <motion.div
                            key={s.label}
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex items-center gap-4"
                        >
                            <span className={`p-3 rounded-xl ${s.bg}`}>
                                <s.icon size={20} className={s.color} />
                            </span>
                            <div>
                                <p className="text-2xl font-bold text-slate-800">{s.value}</p>
                                <p className="text-xs text-slate-500">{s.label}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* Overall sentiment */}
                {result.overall_sentiment && (
                    <motion.div
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 mb-8"
                    >
                        <SentimentChart
                            counts={result.overall_sentiment}
                            title="Overall Sentiment Distribution"
                        />
                    </motion.div>
                )}

                {/* Two-column: themes + recommendations */}
                <div className="grid lg:grid-cols-5 gap-6">
                    {/* Themes list */}
                    <div className="lg:col-span-3 space-y-4">
                        <h2 className="font-semibold text-slate-700 text-base mb-1">
                            Top Themes ({result.themes.length})
                        </h2>
                        {result.themes.map((theme, i) => (
                            <ThemeCard key={theme.cluster_id} theme={theme} rank={i + 1} />
                        ))}
                    </div>

                    {/* Recommendations sticky panel */}
                    <div className="lg:col-span-2">
                        <div className="sticky top-6">
                            <RecommendationsPanel recommendations={result.recommendations ?? []} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

Dashboard.displayName = "Dashboard";