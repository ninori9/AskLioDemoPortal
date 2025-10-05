import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

@Component({
  selector: 'app-skeleton-table',
  standalone: true,
  imports: [CommonModule, MatCardModule],
  templateUrl: './skeleton-table.component.html',
  styleUrl: './skeleton-table.component.scss',
})
export class SkeletonTableComponent {
  @Input() rows = 5;
  @Input() columns: { header?: string }[] = [];

  get colsArray(): { header?: string }[] {
    return this.columns;
  }
  get rowsArray(): unknown[] {
    return Array(this.rows);
  }

  readonly mobileSkeletonCount = Array(4).fill(0);
}
