import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, timer } from 'rxjs';
import { catchError, retry, switchMap } from 'rxjs/operators';
import {
  DataTransferRequest,
  TransferResponse,
  StatusResponse,
  LogResponse,
  SourceDatabaseConfig,
  SchemasResponse,
  TablesResponse,
  TableDetailInfo
} from '../models/transfer.models';

@Injectable({
  providedIn: 'root'
})
export class TransferService {
  private readonly apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  /**
   * Start a data transfer job
   */
  startTransfer(config: DataTransferRequest): Observable<TransferResponse> {
    return this.http.post<TransferResponse>(`${this.apiUrl}/transfer/start`, config)
      .pipe(
        retry(1),
        catchError(this.handleError)
      );
  }

  /**
   * Get transfer status
   */
  getTransferStatus(): Observable<StatusResponse> {
    return this.http.get<StatusResponse>(`${this.apiUrl}/transfer/status`)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Stop the current transfer
   */
  stopTransfer(): Observable<{message: string}> {
    return this.http.post<{message: string}>(`${this.apiUrl}/transfer/stop`, {})
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Get all transfer logs
   */
  getTransferLogs(): Observable<LogResponse> {
    return this.http.get<LogResponse>(`${this.apiUrl}/transfer/logs`)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Get all schemas from the source database
   */
  getSchemas(sourceDb: SourceDatabaseConfig): Observable<SchemasResponse> {
    return this.http.post<SchemasResponse>(`${this.apiUrl}/database/schemas`, sourceDb)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Get all tables and views from a specific schema
   */
  getTablesAndViews(sourceDb: SourceDatabaseConfig, schemaName: string): Observable<TablesResponse> {
    const params = { schema_name: schemaName };
    return this.http.post<TablesResponse>(`${this.apiUrl}/database/tables`, sourceDb, { params })
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Get detailed information about a specific table
   */
  getTableInfo(sourceDb: SourceDatabaseConfig, schemaName: string, tableName: string): Observable<TableDetailInfo> {
    const params = { 
      schema_name: schemaName,
      table_name: tableName
    };
    return this.http.post<TableDetailInfo>(`${this.apiUrl}/database/table-info`, sourceDb, { params })
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Health check
   */
  healthCheck(): Observable<{status: string, timestamp: string}> {
    return this.http.get<{status: string, timestamp: string}>(`${this.apiUrl}/health`)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Poll transfer status every interval
   * @param intervalMs Interval in milliseconds (default: 2000ms)
   */
  pollTransferStatus(intervalMs: number = 2000): Observable<StatusResponse> {
    return timer(0, intervalMs).pipe(
      switchMap(() => this.getTransferStatus())
    );
  }

  /**
   * Handle HTTP errors
   */
  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An unknown error occurred';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Client Error: ${error.error.message}`;
    } else {
      // Server-side error
      if (error.status === 0) {
        errorMessage = 'Unable to connect to the server. Please check if the API is running.';
      } else if (error.status === 409) {
        errorMessage = 'A transfer is already in progress';
      } else if (error.status === 400) {
        errorMessage = error.error?.detail || 'Bad request';
      } else if (error.status === 500) {
        errorMessage = 'Internal server error. Please check the server logs.';
      } else {
        errorMessage = `Server Error: ${error.status} - ${error.error?.detail || error.message}`;
      }
    }

    console.error('Transfer service error:', error);
    return throwError(() => new Error(errorMessage));
  }
} 