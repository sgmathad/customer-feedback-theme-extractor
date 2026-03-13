export interface Quote {
  text: string;
  sentiment: 'positive' | 'neutral' | 'negative';
}

export interface SentimentCounts {
  positive: number;
  neutral: number;
  negative: number;
}

export interface Theme {
  cluster_id: number;
  theme_name: string;
  description: string;
  count: number;
  percentage: number;
  sentiment_counts: SentimentCounts;
  quotes: Quote[];
}

export interface Recommendation {
  priority: number;
  title: string;
  description: string;
}

export interface AnalysisResult {
  success: boolean;
  analysis_id: string;
  total_feedback: number;
  processed_feedback: number;
  removed_entries: number;
  num_themes: number;
  themes: Theme[];
  overall_sentiment: SentimentCounts;
  recommendations: Recommendation[];
  message: string;
}
