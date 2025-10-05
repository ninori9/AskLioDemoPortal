import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-mobile-paginator',
  standalone: true,
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './mobile-paginator.component.html',
  styleUrl: './mobile-paginator.component.scss',
})
export class MobilePaginatorComponent {
  @Input() length: number = 0;
  @Input() pageSize: number = 10;
  @Input() pageIndex: number = 0;

  @Output() page = new EventEmitter<{ pageIndex: number }>();

  get totalPages(): number {
    return Math.ceil(this.length / this.pageSize);
  }

  get rangeStart(): number {
    return this.length === 0 ? 0 : this.pageIndex * this.pageSize + 1;
  }

  get rangeEnd(): number {
    const end = (this.pageIndex + 1) * this.pageSize;
    return end > this.length ? this.length : end;
  }

  firstPage(): void {
    if (this.pageIndex > 0) this.changePage(0);
  }

  prevPage(): void {
    if (this.pageIndex > 0) this.changePage(this.pageIndex - 1);
  }

  nextPage(): void {
    if (this.pageIndex < this.totalPages - 1)
      this.changePage(this.pageIndex + 1);
  }

  lastPage(): void {
    if (this.pageIndex < this.totalPages - 1)
      this.changePage(this.totalPages - 1);
  }

  private changePage(newIndex: number): void {
    this.page.emit({ pageIndex: newIndex });
  }
}
