// app/components/table-cells/commodity-group-cell.component.ts
import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ProcurementRequestLiteDto } from '../../../data/dtos/procurement-request-lite.dto';

@Component({
  selector: 'app-commodity-group-cell',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatTooltipModule],
  template: `
    <div class="cg-wrap">
      <span class="cg-name">{{ row.commodityGroup.name }}</span>

      <ng-container *ngIf="row.commodityGroupConfidence !== undefined && row.commodityGroupConfidence !== null">
        <span class="pill">{{ asPct(row.commodityGroupConfidence) }}</span>

        <!-- Critical: 0.0 -->
        <mat-icon
          *ngIf="isCritical(row.commodityGroupConfidence)"
          class="icon critical"
          [matTooltip]="'No confidence — requires manager review'"
          aria-label="No confidence — action required"
        >
          error
        </mat-icon>

        <!-- Low: (0, LOW_THRESHOLD) -->
        <mat-icon
          *ngIf="isLow(row.commodityGroupConfidence)"
          class="icon warn"
          [matTooltip]="'Low confidence — please verify'"
          aria-label="Low confidence — please verify"
        >
          warning
        </mat-icon>
      </ng-container>
    </div>
  `,
  styles: [`
    .cg-wrap {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      max-width: 100%;
    }
    .cg-name {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .pill {
      font-size: 12px;
      line-height: 1;
      padding: 2px 6px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.12);
      background: rgba(255,255,255,0.05);
      color: currentColor;
      opacity: 0.9;
    }
    .icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
      vertical-align: middle;
    }
    .icon.warn { color: #f57c00; }     /* Orange */
    .icon.critical { color: #e53935; } /* Red */
  `],
})
export class CommodityGroupCellComponent {
  private readonly LOW_THRESHOLD = 0.5;

  constructor(@Inject('rowData') public row: ProcurementRequestLiteDto) {}

  asPct(v: number): string {
    const pct = Math.round((v ?? 0) * 100);
    return `${pct}%`;
  }

  isCritical(v: number | undefined): boolean {
    return v === 0;
  }

  isLow(v: number | undefined): boolean {
    return typeof v === 'number' && v > 0 && v < this.LOW_THRESHOLD;
  }
}