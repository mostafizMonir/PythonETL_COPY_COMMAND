import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subscription } from 'rxjs';
import { TransferService } from './services/transfer.service';
import {
  DataTransferRequest,
  StatusResponse,
  SourceDatabaseConfig,
  DestinationDatabaseConfig,
  TransferConfig
} from './models/transfer.models';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'PostgreSQL Data Transfer';
  
  transferForm!: FormGroup;
  isTransferRunning = false;
  transferStatus: StatusResponse | null = null;
  statusSubscription?: Subscription;
  
  transferModes = [
    { value: 'full', label: 'Full Transfer' },
    { value: 'daily', label: 'Daily Incremental' },
    { value: 'custom', label: 'Custom Date Range' }
  ];

  sslModes = [
    { value: 'require', label: 'Require' },
    { value: 'prefer', label: 'Prefer' },
    { value: 'verify-ca', label: 'Verify CA' },
    { value: 'verify-full', label: 'Verify Full' }
  ];

  constructor(
    private fb: FormBuilder,
    private transferService: TransferService,
    private snackBar: MatSnackBar
  ) {
    this.createForm();
  }

  ngOnInit() {
    // Load initial status
    this.loadTransferStatus();
    
    // Start polling for status updates
    this.startStatusPolling();
  }

  ngOnDestroy() {
    if (this.statusSubscription) {
      this.statusSubscription.unsubscribe();
    }
  }

  createForm() {
    this.transferForm = this.fb.group({
      // Source Database Configuration
      sourceDb: this.fb.group({
        host: ['202.4.127.189', [Validators.required]],
        port: [5634, [Validators.required, Validators.min(1), Validators.max(65535)]],
        database: ['warehouse_brac_mne_data', [Validators.required]],
        user: ['postgres', [Validators.required]],
        password: ['9ENag2FO9guhTaL', [Validators.required]]
      }),
      
      // Destination Database Configuration
      destDb: this.fb.group({
        host: ['202.4.127.189', [Validators.required]],
        port: [5634, [Validators.required, Validators.min(1), Validators.max(65535)]],
        database: ['warehouse_brac_mne_data', [Validators.required]],
        user: ['postgres', [Validators.required]],
        password: ['9ENag2FO9guhTaL', [Validators.required]]
      }),
      
      // Transfer Configuration
      transferConfig: this.fb.group({
        table_name: ['catchment', [Validators.required]],
        warehouse_table: ['catchment', [Validators.required]],
        source_db_schema: ['public', [Validators.required]],
        dest_db_schema: ['my', [Validators.required]],
        batch_size: [10000, [Validators.required, Validators.min(100), Validators.max(50000)]],
        transfer_mode: ['full', [Validators.required]],
        date_filter: [''],
        ssl_mode: ['require', [Validators.required]],
        verify_transfer: [true]
      })
    });
  }

  loadTransferStatus() {
    this.transferService.getTransferStatus().subscribe({
      next: (status) => {
        this.transferStatus = status;
        this.isTransferRunning = status.is_running;
      },
      error: (error) => {
        console.error('Error loading transfer status:', error);
      }
    });
  }

  startStatusPolling() {
    this.statusSubscription = this.transferService.pollTransferStatus(2000).subscribe({
      next: (status) => {
        this.transferStatus = status;
        this.isTransferRunning = status.is_running;
        
        // Show completion notification
        if (!status.is_running && status.status === 'completed' && this.transferStatus?.status !== 'completed') {
          this.showSnackBar('Transfer completed successfully!', 'success');
        } else if (!status.is_running && status.status === 'failed') {
          this.showSnackBar('Transfer failed: ' + (status.error_message || 'Unknown error'), 'error');
        }
      },
      error: (error) => {
        console.error('Error polling transfer status:', error);
      }
    });
  }

  onStartTransfer() {
    if (this.transferForm.valid && !this.isTransferRunning) {
      const formValue = this.transferForm.value;
      
      const transferRequest: DataTransferRequest = {
        source_db: formValue.sourceDb as SourceDatabaseConfig,
        dest_db: formValue.destDb as DestinationDatabaseConfig,
        transfer_config: formValue.transferConfig as TransferConfig
      };

      this.transferService.startTransfer(transferRequest).subscribe({
        next: (response) => {
          this.showSnackBar('Transfer started successfully!', 'success');
          this.isTransferRunning = true;
        },
        error: (error) => {
          this.showSnackBar('Failed to start transfer: ' + error.message, 'error');
        }
      });
    } else {
      this.showSnackBar('Please fill in all required fields correctly', 'warning');
      this.markFormGroupTouched(this.transferForm);
    }
  }

  onStopTransfer() {
    if (this.isTransferRunning) {
      this.transferService.stopTransfer().subscribe({
        next: (response) => {
          this.showSnackBar('Transfer stop requested', 'info');
        },
        error: (error) => {
          this.showSnackBar('Failed to stop transfer: ' + error.message, 'error');
        }
      });
    }
  }

  onTransferModeChange() {
    const transferMode = this.transferForm.get('transferConfig.transfer_mode')?.value;
    const dateFilterControl = this.transferForm.get('transferConfig.date_filter');
    
    if (transferMode === 'custom') {
      dateFilterControl?.setValidators([Validators.required]);
    } else {
      dateFilterControl?.clearValidators();
      dateFilterControl?.setValue('');
    }
    dateFilterControl?.updateValueAndValidity();
  }

  isFieldInvalid(fieldPath: string): boolean {
    const field = this.transferForm.get(fieldPath);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  getFieldError(fieldPath: string): string {
    const field = this.transferForm.get(fieldPath);
    if (field && field.errors) {
      if (field.errors['required']) return 'This field is required';
      if (field.errors['min']) return `Minimum value is ${field.errors['min'].min}`;
      if (field.errors['max']) return `Maximum value is ${field.errors['max'].max}`;
    }
    return '';
  }

  private markFormGroupTouched(formGroup: FormGroup) {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      } else {
        control?.markAsTouched();
      }
    });
  }

  private showSnackBar(message: string, type: 'success' | 'error' | 'warning' | 'info') {
    const config = {
      duration: 5000,
      panelClass: [`snackbar-${type}`]
    };
    
    this.snackBar.open(message, 'Close', config);
  }

  getProgressBarColor(): string {
    if (!this.transferStatus) return 'primary';
    
    switch (this.transferStatus.status) {
      case 'completed': return 'accent';
      case 'failed': 
      case 'error': return 'warn';
      default: return 'primary';
    }
  }

  getStatusIcon(): string {
    if (!this.transferStatus) return 'help_outline';
    
    switch (this.transferStatus.status) {
      case 'idle': return 'pause_circle_outline';
      case 'initializing': return 'refresh';
      case 'counting_rows': return 'calculate';
      case 'creating_tables': return 'table_view';
      case 'transferring': return 'sync';
      case 'verifying': return 'verified';
      case 'completed': return 'check_circle';
      case 'failed':
      case 'error': return 'error';
      case 'stopped': return 'stop_circle';
      default: return 'help_outline';
    }
  }
} 