import { ChangeDetectorRef, Component, Inject, inject } from '@angular/core';
import { ProcurementService } from '../../../services/procurement/procurement.service';
import { FormBuilder, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ProcurementRequestDto } from '../../../data/dtos/procurement-request.dto';
import { RequestStatus } from '../../../data/enums/request-status.enum';
import { Subscription } from 'rxjs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { CommonModule } from '@angular/common';
import { formatDateString, formatEuro } from '../../../_utils/common';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { CommodityGroupDto } from '../../../data/dtos/commodity-group.dto';
import { MatButtonModule } from '@angular/material/button';
import { ErrorService } from '../../../services/error/error.service';
import { REQUEST_STATUS_LABELS } from '../../../_utils/const';
import { UpdateProcurementRequestDto } from '../../../data/dtos/update-procurement-request.dto';
import { HttpErrorResponse } from '@angular/common/http';


@Component({
  selector: 'app-procurement-request-dialog-component',
  standalone: true,
  imports: [
    CommonModule,
    MatChipsModule,
    FormsModule,
    ReactiveFormsModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
    MatProgressSpinnerModule,
    MatDialogModule,
    MatButtonModule
  ],
  templateUrl: './procurement-request-dialog.component.html',
  styleUrl: './procurement-request-dialog.component.scss'
})
export class ProcurementRequestDialogComponent {
  private fb = inject(FormBuilder);
  private procurementService = inject(ProcurementService);
  private errorService = inject(ErrorService);
  private dialogRef = inject(MatDialogRef<ProcurementRequestDialogComponent>);
  private cdr = inject(ChangeDetectorRef);

  RequestStatus = RequestStatus;
  loading = true;
  commodityGroups: CommodityGroupDto[] = [];
  request: ProcurementRequestDto | null = null;
  sub?: Subscription;

  // Minimal editable model (status + commodity group)
  form = this.fb.group({
    status: [RequestStatus.Open as RequestStatus],
    commodityGroupId: [null as number | null]
  });

  statusOptions: RequestStatus[] = [RequestStatus.Open, RequestStatus.InProgress, RequestStatus.Closed];

  private readonly statusText: Record<RequestStatus, string> = {
    [RequestStatus.Open]: 'Open',
    [RequestStatus.InProgress]: 'In Progress',
    [RequestStatus.Closed]: 'Closed',
    [RequestStatus.All]: '-',
  };

  private readonly LOW_THRESHOLD = 0.5;

  statusLabel(s?: RequestStatus | null): string {
    return s ? REQUEST_STATUS_LABELS[s] ?? String(s) : '—';
  }

  constructor(@Inject(MAT_DIALOG_DATA) public data: { id: string, commodityGroups: CommodityGroupDto[] }) {}

  ngOnInit(): void {
    this.commodityGroups = this.data.commodityGroups;
    this.sub = this.procurementService.getRequestByID(this.data.id).subscribe(req => {
      this.request = req;
      this.form.setValue({
        status: req.status,
        commodityGroupId: req.commodityGroup.id
      });
      this.loading = false;
      this.cdr.detectChanges();
    });
  }

  ngOnDestroy(): void { this.sub?.unsubscribe(); }

  close(): void { this.dialogRef.close(); }

  save(): void {
    if (!this.request) return;

    const formVal = this.form.value;
    const payload: UpdateProcurementRequestDto = {
      version: this.request.version,
      status: formVal.status ?? undefined,
      commodityGroupID: formVal.commodityGroupId ?? undefined,
    };

    this.loading = true;
    this.procurementService.updateRequest(this.request.id, payload).subscribe({
      next: (updated) => {
        this.loading = false;
        this.dialogRef.close(updated);
      },
      error: (err) => {
        this.loading = false;

        let message = "Failed to update procurement request. Please try again later.";

        // Handle optimistic concurrency error
        if (err instanceof HttpErrorResponse && err.status === 409) {
          message = 'This request was updated by someone else. Please refresh and try again.';
        }

        this.errorService.handle(err, message);
      }
    });
  }

  statusClass(s?: RequestStatus | null) {
    switch (s) {
      case RequestStatus.Open: return 'status-open';
      case RequestStatus.InProgress: return 'status-inprogress';
      case RequestStatus.Closed: return 'status-closed';
      default: return '';
    }
  }

  // Amount helpers
  linesSubtotalCents(): number {
    if (!this.request?.orderLines?.length) return 0;
    return this.request.orderLines.reduce((sum, l) => sum + (l.totalPriceCents || 0), 0);
  }

  shippingCents(): number {
    return this.request?.shippingCents ?? 0;
  }
  taxCents(): number {
    return this.request?.taxCents ?? 0;
  }
  discountCents(): number {
    return this.request?.totalDiscountCents ?? 0;
  }

  finalTotalCents(): number {
    return this.request?.totalCostsCent ?? 0;
  }

  // Commodity group confidence
  confidencePct(): string | null {
    const v = this.request?.commodityGroupConfidence;
    if (v === undefined || v === null) return null;
    return `${Math.round(v * 100)}%`;
  }
  hasConfidence(): boolean {
    const v = this.request?.commodityGroupConfidence;
    return typeof v === 'number';
  }
  isCritical(): boolean {
    const v = this.request?.commodityGroupConfidence;
    return v === 0;
  }
  isLow(): boolean {
    const v = this.request?.commodityGroupConfidence;
    return typeof v === 'number' && v > 0 && v < this.LOW_THRESHOLD;
  }

  formatDate = formatDateString;
  formatAmount = formatEuro;
}
