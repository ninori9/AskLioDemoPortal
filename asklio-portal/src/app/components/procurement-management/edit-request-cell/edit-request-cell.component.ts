import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ProcurementManagementComponent } from '../procurement-management.component';
import { ProcurementRequestLiteDto } from '../../../data/dtos/procurement-request-lite.dto';

@Component({
  selector: 'app-edit-request-cell',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule],
  template: `
    <div class="edit-request-cell">
      <button mat-button color="primary" (click)="parent.editRequest(row)">
        <mat-icon>edit</mat-icon>
        Details
      </button>
    </div>
  `,
  styles: [
    `
      .edit-request-cell {
        display: flex;
        justify-content: start;
        align-items: center;
        flex-wrap: nowrap;
      }
      .edit-request-cell button {
        color: white;
        font-weight: 500;
        white-space: nowrap;
      }
      .edit-request-cell mat-icon {
        margin-right: 6px;
      }
    `,
  ],
})
export class EditRequestCellComponent {
  constructor(
    @Inject('rowData') public row: ProcurementRequestLiteDto,
    @Inject('parentComponent') public parent: ProcurementManagementComponent
  ) {}
}