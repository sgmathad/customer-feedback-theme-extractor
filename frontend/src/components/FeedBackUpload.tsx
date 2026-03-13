import { useState, type ChangeEvent } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { FileList } from "./FileList";
import { FileUpload } from "@/reusables";
import { type FileType, type AnalysisResult } from "@/interfaces";
import { CloudUpload, Sparkles, Loader2 } from "lucide-react";
import { Dashboard } from "./Dashboard";

type Step = "idle" | "uploading" | "uploaded" | "analyzing" | "done" | "error";

export const FeedBackUpload: React.FC = () => {
    const [files, setFiles] = useState<FileType[]>([]);
    const [step, setStep] = useState<Step>("idle");
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [errorMsg, setErrorMsg] = useState<string>("");
    const [demoLoading, setDemoLoading] = useState(false);

    const processFiles = (e: ChangeEvent<HTMLInputElement>) => {
        if (!e.target?.files) return;
        const newFiles = Array.from(e.target.files).map((file) => ({
            id: file.name,
            progress: 0,
            file,
        }));
        setFiles((prev) => [...prev, ...newFiles]);
    };

    const uploadFiles = async () => {
        if (files.length === 0 || step === "uploading") return;
        setStep("uploading");
        const uploadPromises = files.map(async (file) => {
            const formData = new FormData();
            formData.append("files", file.file);
            try {
                await axios.post("http://127.0.0.1:8000/upload", formData, {
                    onUploadProgress: (progressEvent) => {
                        const progress = Math.round(
                            (progressEvent.loaded * 100) / (progressEvent.total || 1)
                        );
                        setFiles((prev) =>
                            prev.map((f) => (f.id === file.id ? { ...f, progress } : f))
                        );
                    },
                });
            } catch (e) {
                console.error(e);
            }
        });
        await Promise.all(uploadPromises);
        setStep("uploaded");
    };

    const analyzeFiles = async () => {
        setStep("analyzing");
        setErrorMsg("");
        try {
            const { data } = await axios.post<AnalysisResult>("http://127.0.0.1:8000/analyze");
            setResult(data);
            setStep("done");
        } catch (e: unknown) {
            console.error(e);
            const msg =
                axios.isAxiosError(e) && e.response?.data?.detail
                    ? e.response.data.detail
                    : "Analysis failed. Please try again.";
            setErrorMsg(msg);
            setStep("error");
        }
    };

    const clearFiles = async () => {
        try {
            await axios.delete("http://127.0.0.1:8000/clear");
        } catch (e) {
            console.error(e);
        }
        setFiles([]);
        setStep("idle");
        setResult(null);
        setErrorMsg("");
    };

    const loadDemo = async () => {
        setDemoLoading(true);
        setErrorMsg("");
        try {
            await axios.post("http://127.0.0.1:8000/demo");
            setFiles([{ id: "demo", progress: 100, file: new File([], "demo_dataset") }]);
            setStep("uploaded");
        } catch (e) {
            console.error(e);
            setErrorMsg("Failed to load demo dataset.");
        } finally {
            setDemoLoading(false);
        }
    };

    // Show full dashboard when done
    if (step === "done" && result) {
        return <Dashboard result={result} />;
    }

    return (
        <motion.div
            initial="hidden"
            animate="visible"
            className="flex flex-col sm:w-[50%] w-full gap-6"
        >
            {/* Upload Area */}
            <motion.div
                whileHover={{ scale: 1.01 }}
                className="border border-dashed flex flex-col justify-center items-center gap-3 h-64 rounded-2xl bg-white hover:shadow-md transition-shadow"
            >
                <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 120, delay: 0.2 }}
                    className="border rounded-lg p-2 border-slate-300"
                >
                    <CloudUpload className="text-slate-500" />
                </motion.span>

                <motion.div
                    whileHover={{ scale: 1.05 }}
                    className="font-medium cursor-pointer text-blue-400 hover:text-blue-500 hover:underline"
                >
                    <FileUpload
                        accept=".pdf,.xlsx,.csv,.docx,.txt,.json"
                        multiple
                        onFileupload={processFiles}
                    />
                </motion.div>

                <div className="flex flex-wrap gap-2 justify-center">
                    {["CSV", "XLSX", "PDF", "DOCX", "TXT", "JSON"].map((type) => (
                        <span
                            key={type}
                            className="px-3 py-1 text-xs font-medium rounded-full bg-slate-100 text-slate-600"
                        >
                            {type}
                        </span>
                    ))}
                </div>
            </motion.div>

            {/* Demo button */}
            <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                onClick={loadDemo}
                disabled={demoLoading}
                className="flex items-center justify-center gap-2 w-full py-3 rounded-xl border-2 border-dashed border-pink-300 bg-pink-50 text-pink-600 text-sm font-medium hover:bg-pink-100 transition-colors disabled:opacity-60"
            >
                {demoLoading ? (
                    <Loader2 size={15} className="animate-spin" />
                ) : (
                    <Sparkles size={15} />
                )}
                {demoLoading ? "Loading demo…" : "Try with sample data"}
            </motion.button>

            {/* Error */}
            {step === "error" && errorMsg && (
                <div className="rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm px-4 py-3">
                    {errorMsg}
                </div>
            )}

            {/* Analyzing overlay */}
            <AnimatePresence>
                {step === "analyzing" && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col items-center gap-3 py-4"
                    >
                        <Loader2 size={28} className="animate-spin text-blue-500" />
                        <p className="text-sm text-slate-500">
                            Running AI analysis… this may take a minute.
                        </p>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Action Buttons */}
            {step !== "analyzing" && (
                <div className="flex justify-end gap-3">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        disabled={step !== "uploaded"}
                        className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                        onClick={analyzeFiles}
                    >
                        Analyze
                    </motion.button>

                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        disabled={step === "uploading" || files.length === 0 || step === "uploaded"}
                        className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                        onClick={uploadFiles}
                    >
                        {step === "uploading" ? "Uploading…" : "Upload"}
                    </motion.button>

                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="px-4 py-2 rounded-lg border border-slate-300 text-sm"
                        onClick={clearFiles}
                    >
                        Clear
                    </motion.button>
                </div>
            )}

            {/* File List */}
            <div className="flex flex-col gap-3">
                <AnimatePresence>
                    {files.filter(f => f.id !== "demo").map((upload) => {
                        const { name, size } = upload.file;
                        return (
                            <motion.div
                                key={upload.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                transition={{ duration: 0.25 }}
                            >
                                <FileList name={name} size={size} progress={upload.progress} />
                            </motion.div>
                        );
                    })}
                </AnimatePresence>

                {/* Demo indicator */}
                {files.some(f => f.id === "demo") && step === "uploaded" && (
                    <div className="flex items-center gap-2 text-sm text-pink-600 bg-pink-50 border border-pink-200 rounded-xl px-4 py-3">
                        <Sparkles size={14} />
                        Demo dataset loaded (42 synthetic feedback entries across 3 file types). Click <strong>Analyze</strong> to continue.
                    </div>
                )}
            </div>
        </motion.div>
    );
};