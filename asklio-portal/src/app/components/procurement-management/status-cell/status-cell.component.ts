import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { MatChipsModule } from '@angular/material/chips';
import { ProcurementRequestLiteDto } from '../../../data/dtos/procurement-request-lite.dto';
import { RequestStatus } from '../../../data/enums/request-status.enum';
import { REQUEST_STATUS_LABELS } from '../../../_utils/const';

@Component({
  selector: 'app-request-status-chip',
  standalone: true,
  imports: [CommonModule, MatChipsModule],
  template: `
    <mat-chip [ngClass]="statusClass(row.status)">
      {{ labelFor(row.status) }}
    </mat-chip>
  `,
  styles: [`
    mat-chip {
      font-weight: 600;
      font-size: 0.85rem;
      border-radius: 12px;
      padding: 0 8px;
      height: 24px;
    }
    .open {
      background: #1976d2;
    }

    .in-progress {
      background: #f57c00;
    }

    .closed {
      background: #388e3c;
    }
  `],
})
export class StatusCellComponent {
  constructor(@Inject('rowData') public row: ProcurementRequestLiteDto) {}

  labelFor(status: RequestStatus): string {
    return REQUEST_STATUS_LABELS[status] ?? String(status);
  }

  statusClass(status: RequestStatus): string {
    switch (status) {
      case RequestStatus.Open: return 'open';
      case RequestStatus.InProgress: return 'in-progress';
      case RequestStatus.Closed: return 'closed';
      default: return '';
    }
  }
}
