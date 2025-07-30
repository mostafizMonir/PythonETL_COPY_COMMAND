export interface SourceDatabaseConfig {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
}

export interface DestinationDatabaseConfig {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
}

export interface TransferConfig {
  table_name: string;
  warehouse_table: string;
  source_db_schema: string;
  dest_db_schema: string;
  batch_size: number;
  transfer_mode: 'full' | 'daily' | 'custom';
  date_filter?: string;
  ssl_mode: string;
  verify_transfer: boolean;
}

export interface DataTransferRequest {
  source_db: SourceDatabaseConfig;
  dest_db: DestinationDatabaseConfig;
  transfer_config: TransferConfig;
}

export interface TransferResponse {
  message: string;
  transfer_id: string;
  status: string;
}

export interface StatusResponse {
  is_running: boolean;
  current_batch: number;
  total_rows: number;
  transferred_rows: number;
  progress_percentage: number;
  start_time?: string;
  estimated_completion?: string;
  status: string;
  error_message?: string;
  logs: string[];
}

export interface LogResponse {
  logs: string[];
} 