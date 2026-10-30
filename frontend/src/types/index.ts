export type UserRole = 'admin' | 'hydrologist' | 'emergency_commander' | 'viewer';

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  token?: string;
  mfa_enabled?: boolean;
}

export type FeatureId =
  | 'landing'
  | 'f01_mission_control'
  | 'f02_new_scenario'
  | 'f04_run_monitor'
  | 'f05_results_explorer'
  | 'f06_engine_comparison'
  | 'f07_satellite_validation'
  | 'f08_live_flood'
  | 'f09_impact'
  | 'f10_evacuation'
  | 'f11_cascade'
  | 'f14_library'
  | 'f15_batch'
  | 'f16_lake_watch'
  | 'f17_alerts'
  | 'f18_catalogue'
  | 'f19_benchmarks'
  | 'f20_health'
  | 'f21_audit'
  | 'f22_admin'
  | 'signin';

export type StatusType =
  | 'RUN AND PASSED'
  | 'RUN AND FAILED'
  | 'NOT RUN'
  | 'PENDING'
  | 'UNVERIFIED'
  | 'TESTED'
  | 'PRECOMPUTED'
  | 'DEMO';
