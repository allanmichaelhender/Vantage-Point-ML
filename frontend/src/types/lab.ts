// 📂 src/types/lab.ts

export interface PerformanceSummary {
  roi: number;
  total_profit: number;
  win_rate: number;
  brier_score: number;
  total_bets: number;
}

export interface WeeklyPoint {
  date: string;
  balance: number;
}

export interface CalibrationPoint {
  prob_bucket: string;   // 🎯 Match your FastAPI 'prob_bucket'
  avg_predicted: number; 
  actual_win_rate: number;
  match_count: number;
}

export interface EdgeBucket {
  bucket: string;        // 🎯 Match your FastAPI 'bucket'
  roi: number;
  match_count: number;
}

// 🎯 Represents the data for a single model
export interface ModelProfile {
  summary: PerformanceSummary;
  equity_curve: WeeklyPoint[];
  monthly_breakdown: any[];
  calibration_data: CalibrationPoint[];
  edge_analysis: EdgeBucket[];
}

export type ModelType = 'xgboost_nn' | 'xgboost';

export interface LabData {
  xgboost_nn: ModelProfile;
  xgboost: ModelProfile;
}

