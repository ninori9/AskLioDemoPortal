import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FilterOption } from '../../../../data/models/filter-option.model';
import { CommonModule } from '@angular/common';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-filter-chips',
  standalone: true,
  imports: [
    CommonModule, 
    MatChipsModule, 
    MatIconModule
  ],
  templateUrl: './filter-chips.component.html',
  styleUrl: './filter-chips.component.scss'
})
export class FilterChipsComponent<T = any> {
  @Input() options: FilterOption<T>[] = [];

  @Input() selected: T | null = null;
  @Input() allowDeselect = false;

  @Input() compareWith: (a: T | null, b: T) => boolean = (a, b) => Object.is(a, b);

  @Output() selectionChange = new EventEmitter<T | null>();

  trackByValue = (_: number, o: FilterOption<T>) => o.value;

  isSelected(v: T): boolean {
    return this.compareWith(this.selected, v);
  }

  onSelect(v: T): void {
    const next = (this.allowDeselect && this.isSelected(v)) ? null : v;
    this.selected = next;
    this.selectionChange.emit(next);
  }
}
