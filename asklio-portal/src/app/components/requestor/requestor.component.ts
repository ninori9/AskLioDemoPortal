import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { NewProcurementRequestDialogComponent } from './new-procurement-request-dialog/new-procurement-request-dialog.component';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ProcurementRequestLiteDto } from '../../data/dtos/procurement-request-lite.dto';
import { ProcurementService } from '../../services/procurement/procurement.service';
import { RequestDraftDto } from '../../data/dtos/request-draft.dto';
import { ErrorService } from '../../services/error/error.service';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-requestor',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatCardModule,
    MatButtonModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './requestor.component.html',
  styleUrl: './requestor.component.scss'
})
export class RequestorComponent {
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);
  private procurementService = inject(ProcurementService);
  private errorService = inject(ErrorService);

  selectedFile: File | null = null;
  selectedFileName = '';
  isProcessing = false;

  onFileSelected(evt: Event): void {
    const input = evt.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.selectedFile = file || null;
    this.selectedFileName = file ? file.name : '';
  }

  processUpload(): void {
    if (!this.selectedFile || this.isProcessing) return;

    console.log(this.selectedFile);

    this.isProcessing = true;

    this.procurementService.extractDraftFromPdf(this.selectedFile).subscribe({
      next: (draft: RequestDraftDto) => {
        this.isProcessing = false;

        // Open the dialog prefilled with the extracted draft
        const dialogRef = this.dialog.open(NewProcurementRequestDialogComponent, {
          data: { initial: draft },
        });

        dialogRef.afterClosed().subscribe((created?: ProcurementRequestLiteDto) => {
          if (!created) return;
          this.snackBar.open(
            `Request “${created.title}” submitted successfully.`,
            'Close',
            { duration: 3500, panelClass: ['snackbar-success'] }
          );
          // Clear file selection after success
          this.selectedFile = null;
          this.selectedFileName = '';
        });
      },
      error: (err) => {
        this.isProcessing = false;
        // Error messages for common cases (mirrors backend)
        let msg = 'Extraction failed. Please try another PDF.';
        if (err.status === 415) msg = 'Unsupported file type. Please upload a PDF.';
        else if (err.status === 413) msg = 'File too large. Maximum file size is 5 MB.';
        else if (err.status === 422) msg = 'That PDF does not look like an offer or procurement request.';
        this.errorService.handle(err, msg);
      },
    });
  }


  startManual(): void {
    const ref = this.dialog.open(NewProcurementRequestDialogComponent, {
      data: {}
    });

    ref.afterClosed().subscribe((created?: ProcurementRequestLiteDto) => {
      if (!created) return;
      this.snackBar.open(
        `Request “${created.title}” submitted successfully.`,
        'Close',
        { duration: 3500, panelClass: ['snackbar-success'] }
      );
    });
  }
}
