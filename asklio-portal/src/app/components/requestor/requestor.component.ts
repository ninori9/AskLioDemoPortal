import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { NewProcurementRequestDialogComponent } from './new-procurement-request-dialog/new-procurement-request-dialog.component';
import { CommodityGroupDto } from '../../data/dtos/commodity-group.dto';
import { ProcurementService } from '../../services/procurement/procurement.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { errorSnackBarConfig } from '../../_utils/common';
import { ProcurementRequestLiteDto } from '../../data/dtos/procurement-request-lite.dto';
import { ErrorService } from '../../services/error/error.service';

@Component({
  selector: 'app-requestor',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatCardModule,
    MatButtonModule,
  ],
  templateUrl: './requestor.component.html',
  styleUrl: './requestor.component.scss'
})
export class RequestorComponent implements OnInit {
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);
  private procurementService = inject(ProcurementService);
  private errorService = inject(ErrorService)

  selectedFile: File | null = null;
  selectedFileName = '';

  commodityGroups: CommodityGroupDto[] = [];

  ngOnInit(): void {
    this.procurementService.getCommodityGroups().subscribe({
      next: (groups) => this.commodityGroups = groups ?? [],
      error: (err) => this.errorService.handle(err, "Error fetching commodity groups. Please try again later.")
    });
  }

  onFileSelected(evt: Event): void {
    const input = evt.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.selectedFile = file || null;
    this.selectedFileName = file ? file.name : '';
  }

  processUpload(): void {
    if (!this.selectedFile) return;
    // TODO: upload + extract, then open prefilled dialog
    console.log('Process file:', this.selectedFileName);
  }

  startManual(): void {
    const ref = this.dialog.open(NewProcurementRequestDialogComponent, {
      data: { commodityGroups: this.commodityGroups }
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
