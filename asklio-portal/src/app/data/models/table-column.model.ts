import { Type } from '@angular/core';

export interface TableColumn<T = unknown> {
  key: string;
  header: string;
  value?: (row: T) => string | number | boolean | null | undefined;
  cellComponent?: Type<unknown>;
  sortable?: boolean;
  sortValue?: (row: T) => string | number | Date;
  sortFunction?: (a: T, b: T) => number;
  width?: string;
  primary?: boolean;
  cellClass?: string;
}
