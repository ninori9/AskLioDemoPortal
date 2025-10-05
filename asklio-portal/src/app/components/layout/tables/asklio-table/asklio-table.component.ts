import { ScrollingModule } from '@angular/cdk/scrolling';
import { CommonModule, NgComponentOutlet } from '@angular/common';
import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Injector,
  Input,
  NgZone,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import {
  MatPaginator,
  MatPaginatorModule,
} from '@angular/material/paginator';
import { MatSort, MatSortModule, Sort } from '@angular/material/sort';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { TableColumn } from '../../../../data/models/table-column.model';
import { MobilePaginatorComponent } from '../mobile-paginator/mobile-paginator.component';

@Component({
  selector: 'app-asklio-table',
  standalone: true,
  imports: [
    CommonModule,
    MatPaginatorModule,
    MatTableModule,
    MatSortModule,
    MatCardModule,
    NgComponentOutlet,
    MatButtonModule,
    MatIconModule,
    MatButtonModule,
    ScrollingModule,
    MobilePaginatorComponent
  ],
  templateUrl: './asklio-table.component.html',
  styleUrl: './asklio-table.component.scss',
})
export class AskLioTableComponent<T> implements AfterViewInit, OnChanges, OnDestroy {
  @Input({ required: true }) dataSource: T[] = [];
  @Input({ required: true }) columns!: TableColumn<T>[];

  @Input() trackBy: (i: number, r: T) => unknown = (_, r) => r;

  @Input() rowClickFn?: (row: T) => void;

  @Input() pageHeading?: string;
  @Input() isMainTable: boolean = false;

  pageSize = 10;
  mobilePageIndex = 0;

  /** Allow callbacks inside cell-components */
  @Input() parentComponent?: unknown;

  displayedColumns: string[] = [];
  matDataSource = new MatTableDataSource<T>();

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  private scrollEl?: HTMLElement;

  // Clone table parent element reference
  @ViewChild('cloneHost', { read: ElementRef }) cloneHost?: ElementRef<HTMLElement>;

  // Base table element reference
  private _baseTable?: ElementRef<HTMLTableElement>;
  @ViewChild('baseTable', { read: ElementRef })
  set baseTableRef(el: ElementRef<HTMLTableElement> | undefined) {
    this._baseTable = el;
    // Attach size observer
    if (el?.nativeElement && this.tableResizeObs) {
      this.tableResizeObs.observe(el.nativeElement);
    }
    // Align sticky clone position
    if (this.isMainTable && el) {
      this.syncStickyClone();
    }
  }

  // Observer for the table size
  private tableResizeObs?: ResizeObserver;

  // Header row clone related state
  headerWidths = new Map<string, number>();

  topbarHeight = 64; // px, adjust if top bar height changes
  showStickyClone = false;
  cloneLeft = 0;
  cloneWidth = 0;
  // Sticky clone is only enabled on desktop and with sufficient data
  enableStickyClone = false;

  constructor(private injector: Injector, private ngZone: NgZone, private cdr: ChangeDetectorRef) {}

  ngAfterViewInit(): void {
    this.displayedColumns = this.columns.map((c) => c.key);
    this.matDataSource = new MatTableDataSource(this.dataSource);

    // Pagination
    this.matDataSource.paginator = this.paginator;

    // Sorting
    this.matDataSource.sortingDataAccessor = (
      item,
      property
    ): string | number => {
      const col = this.columns.find((c) => c.key === property)!;
      if (col.sortValue) {
        const raw = col.sortValue(item);
        if (raw instanceof Date) {
          return raw.getTime();
        } else if (typeof raw === 'number' || typeof raw === 'string') {
          return raw;
        }
        return '';
      } else {
        const val = col.value ? col.value(item) : '';
        if (typeof val === 'number') {
          return val;
        }
        return (val ?? '').toString();
      }
    };

    this.matDataSource.sort = this.sort;

    this.matDataSource.sortData = (data, sort): T[] => {
      if (!sort.active || sort.direction === '') return data.slice();

      const col = this.columns.find((c) => c.key === sort.active);
      const dir = sort.direction === 'asc' ? 1 : -1;

      // Prefer a full comparator if provided
      if (col?.sortFunction) {
        return [...data].sort((a, b) => dir * col.sortFunction!(a, b));
      }

      // Fallback to accessor (existing behavior)
      return [...data].sort((a, b) => {
        const va = this.matDataSource.sortingDataAccessor(a, sort.active) as
          | string
          | number
          | Date
          | null
          | undefined;
        const vb = this.matDataSource.sortingDataAccessor(b, sort.active) as
          | string
          | number
          | Date
          | null
          | undefined;

        if (va == null && vb == null) return 0;
        if (va == null) return -1 * dir;
        if (vb == null) return 1 * dir;

        if (typeof va === 'string' && typeof vb === 'string') {
          // Sensible string compare with numeric sorting
          return (
            dir *
            va.localeCompare(vb, undefined, {
              numeric: true,
              sensitivity: 'base',
            })
          );
        }
        return dir * (va < vb ? -1 : va > vb ? 1 : 0);
      });
    };

    // If the table is a main page table, refine scrolling behavior
    if (this.isMainTable) {
      // Calculate whether sticky clone should be taken into account
      this.updateEnableStickyClone();

      // Get parent scroll element and attach a scroll listener
      const base = this._baseTable?.nativeElement ?? null;
      const scrollContainer = this.getScrollContainer(base);

      this.ngZone.runOutsideAngular(() => {
        if (scrollContainer === window) {
          window.addEventListener('scroll', this.syncStickyClone, { passive: true });
        } else {
          this.scrollEl = scrollContainer as HTMLElement;
          this.scrollEl.addEventListener('scroll', this.syncStickyClone, { passive: true });
        }
      });

      // Add a resize observer to the table
      this.tableResizeObs = new ResizeObserver(() => {
        this.afterLayout(() => {
          this.computeHeaderWidths();
          if (this.showStickyClone) {
            this.applyHeaderWidthsToClone();
          }
          this.syncStickyClone();
        });
      });
      
      // If the table is already there, start observing it
      if (this._baseTable?.nativeElement) {
        this.tableResizeObs.observe(this._baseTable.nativeElement);
      }

      requestAnimationFrame(() => this.syncStickyClone());
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['dataSource']) {
      this.matDataSource.data = this.dataSource;
      // Re-evaluate eligibility when the data length changes
      this.updateEnableStickyClone();

      // After enabling, compute widths and sync once the header is painted
      requestAnimationFrame(() => {
        this.computeHeaderWidths();
        this.syncStickyClone();
      });
    }
  }

  ngOnDestroy(): void {
    this.scrollEl?.removeEventListener('scroll', this.syncStickyClone);
  }

  getCellInjector(row: unknown, parent: unknown, key: unknown): Injector {
    return Injector.create({
      providers: [
        { provide: 'rowData', useValue: row },
        { provide: 'parentComponent', useValue: parent },
        { provide: 'cellKey', useValue: key },
      ],
      parent: this.injector,
    });
  }

  /* Sorting change to keep table reactive when data changes */
  onSortChange(sort: Sort): void {
    if (!sort.active || sort.direction === '') {
      this.matDataSource.data = [...this.dataSource];
      return;
    }
  }

  cellValue(
    col: TableColumn<T>,
    row: T
  ): string | number | boolean | null | undefined {
    return col.value?.(row) ?? '';
  }

  get mobilePagedData(): T[] {
    const start = this.mobilePageIndex * this.pageSize;
    return this.dataSource.slice(start, start + this.pageSize);
  }

  onMobilePage(event: { pageIndex: number }): void {
    this.mobilePageIndex = event.pageIndex;
  }

  // Make row clickable
  onRowClick(row: T): void {
    if (this.rowClickFn) {
      this.rowClickFn(row);
    }
  }

  // Indicate if row is deleted
  isDeleted(row: T): boolean {
    return !!(
      row &&
      typeof row === 'object' &&
      'deletedAt' in row &&
      (row as { deletedAt?: string | null | undefined }).deletedAt
    );
  }

  private afterLayout(callback: () => void): void {
    requestAnimationFrame(() => requestAnimationFrame(callback));
  }

  /**
   * applyHeaderWidthsToClone() resizes the widths of the header columns of the sticky clone
   */
  private applyHeaderWidthsToClone(): void {
    const host = this.cloneHost?.nativeElement;
    if (!host) return;

    const cloneTable = host.querySelector('table.mat-mdc-table') as HTMLTableElement | null;
    if (!cloneTable) return;

    const cloneHeaders = cloneTable.querySelectorAll('thead th.mat-mdc-header-cell');
    if (!cloneHeaders.length) {
      // Clone header not painted yet—try next frame.
      requestAnimationFrame(() => this.applyHeaderWidthsToClone());
      return;
    }

    // Apply cached widths (by displayed column order)
    this.displayedColumns.forEach((key, i) => {
      const th = cloneHeaders[i] as HTMLElement | undefined;
      const baseTableThWidth = this.headerWidths.get(key);
      if (th && baseTableThWidth) {
        const px = `${baseTableThWidth}px`;
        th.style.width = px;
        th.style.minWidth = px;
        th.style.maxWidth = px;
      }
    });
  }

  /**
   * computeHeaderWidths() computes the header widths of the base table, used by the sticky clone
   */
  private computeHeaderWidths(): void {
    if (!this.isMainTable || !this.enableStickyClone) {
      // Not a main page table or not sufficient screen size -> scrolling behavior not intended
      return;
    }

    const base = this._baseTable?.nativeElement;
    if (!base) {
      // Base table not found
      return;
    }

    const ths = base.querySelectorAll('thead th.mat-mdc-header-cell');
    if (!ths.length) {
      // No header elements found
      return;
    }

    this.headerWidths.clear();
    this.displayedColumns.forEach((key, index) => {
      const th = ths[index] as HTMLElement | undefined;
      if (th) {
        const thWidth = Math.round(th.getBoundingClientRect().width);
        this.headerWidths.set(key, thWidth);
      }
    });
    this.cdr.markForCheck();
  }

  /**
   * updateEnableStickyClone() is used to compute whether we should even bother rendering and keeping up with the sticky
   * clone. This is not the case on small screens and with few data entries
   */
  private updateEnableStickyClone(): void {
    const next = window.innerWidth > 920 && (this.dataSource?.length ?? 0) > 4;
    if (next !== this.enableStickyClone) {
      this.enableStickyClone = next;
      // If we turned it off while it was visible, hide immediately
      if (!next && this.showStickyClone) {
        this.showStickyClone = false;
      }
      this.cdr.markForCheck();
    }
  }

  /**
   * syncStickyClone() calculates / applies values related to whether we should show the sticky clone and with which dimensions 
   */
  private syncStickyClone = (): void => {
    if (!this.enableStickyClone) {
      return;
    }

    const tableBaseElement = this._baseTable?.nativeElement;
    if (!tableBaseElement) {
      return;
    }

    const rect = tableBaseElement.getBoundingClientRect();
    const headerRow =
      (tableBaseElement.tHead?.rows?.[0] as HTMLElement | null) ||
      (tableBaseElement.querySelector('thead tr') as HTMLElement | null);
    const headerH = headerRow ? headerRow.getBoundingClientRect().height : 0;

    // Show sticky table clone when the "real" header row is partly hidden by the top bar
    const referenceHeight = this.pageHeading ? (this.topbarHeight + 58) : this.topbarHeight;
    const shouldShow = rect.top < referenceHeight && rect.bottom - headerH > referenceHeight;

    if (shouldShow) {
      // Update positions
      const left = Math.round(rect.left);
      const width = Math.round(rect.width);
      if (left !== this.cloneLeft || width !== this.cloneWidth) {
        this.cloneLeft = left;
        this.cloneWidth = width;
      }
    }

    if (shouldShow !== this.showStickyClone) {
      this.ngZone.run(() => {
        this.showStickyClone = shouldShow;
        if (shouldShow) {
          requestAnimationFrame(() => this.applyHeaderWidthsToClone());
        }
      });
    }
  };

  // Get parent scroll container
  private getScrollContainer(el: HTMLElement | null): HTMLElement | Window {
    let node: HTMLElement | null = el?.parentElement ?? null;
    while (node) {
      const style = getComputedStyle(node);
      const canScrollY =
        /(auto|scroll|overlay)/.test(style.overflowY) &&
        node.scrollHeight > node.clientHeight;
  
      if (canScrollY) return node;
      node = node.parentElement;
    }
    return window;
  }

  scrollToTableTop(): void {
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const behavior: ScrollBehavior = prefersReduced ? 'auto' : 'smooth';
  
    if (this.scrollEl && 'scrollTo' in this.scrollEl) {
      this.scrollEl.scrollTo({ top: 0, behavior });
    } else {
      window.scrollTo({ top: 0, behavior });
    }
  }
}
