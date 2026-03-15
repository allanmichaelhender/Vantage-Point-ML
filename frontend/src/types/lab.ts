// 🎯 This matches your FastAPI 'PerformanceSummary'
export interface PerformanceSummary {
  roi: number;
  total_profit: number;
  win_rate: number;
  brier_score: number;
  total_bets: number;
}

// 🎯 This matches your 'WeeklyPoint'
export interface WeeklyPoint {
  date: string;
  balance: number;
}

// 🎯 The big response object
export interface ModelPerformanceResponse {
  summary: PerformanceSummary;
  equity_curve: WeeklyPoint[];
  monthly_breakdown: any[]; // We'll use 'any' for now to keep it simple
}


export interface CalibrationPoint {
  bin: string;       // e.g., "60-70%"
  expected: number;  // The midpoint (0.65)
  actual: number;    // The actual win rate (0.68)
}

export interface EdgeBucket {
  range: string;     // e.g., "2-4%"
  roi: number;       // e.g., 0.08
  match_count: number;     // How many bets fell in this edge range
}

// Update your main response interface
export interface ModelPerformanceResponse {
  summary: PerformanceSummary;
  equity_curve: WeeklyPoint[];
  monthly_breakdown: any[];
  calibration_data: CalibrationPoint[]; // 🎯 ADD THIS
  edge_analysis: EdgeBucket[];          // 🎯 ADD THIS
}

