import { Component, inject } from '@angular/core';
import { TableColumn } from '../../data/models/table-column.model';
import { RequestStatus } from '../../data/enums/request-status.enum';
import { FilterOption } from '../../data/models/filter-option.model';
import { ProcurementRequestLiteDto } from '../../data/dtos/procurement-request-lite.dto';
import { CommodityGroupDto } from '../../data/dtos/commodity-group.dto';
import { ProcurementService } from '../../services/procurement/procurement.service';
import { formatDateString, formatEuro } from '../../_utils/common';
import { StatusCellComponent } from '../procurement-management/status-cell/status-cell.component';
import { FilterChipsComponent } from '../layout/generic/filter-chips/filter-chips.component';
import { AskLioTableComponent } from '../layout/tables/asklio-table/asklio-table.component';
import { SkeletonTableComponent } from '../layout/tables/skeleton-table/skeleton-table.component';
import { CommonModule } from '@angular/common';
import { ErrorService } from '../../services/error/error.service';

@Component({
  selector: 'app-my-procurement-requests',
  standalone: true,
  imports: [
    CommonModule,
    FilterChipsComponent,
    AskLioTableComponent,
    SkeletonTableComponent
  ],
  templateUrl: './my-procurement-requests.component.html',
  styleUrl: './my-procurement-requests.component.scss'
})
export class MyProcurementRequestsComponent {
  private procurementService = inject(ProcurementService);
  private errorService = inject(ErrorService);

  loading = false;
  rows: ProcurementRequestLiteDto[] = [];
  commodityGroups: CommodityGroupDto[] = [];

  // Same filter options
  statusOptions: FilterOption<RequestStatus>[] = [
    { label: 'All', value: RequestStatus.All, icon: 'all_inclusive' },
    { label: 'Open', value: RequestStatus.Open, icon: 'markunread_mailbox' },
    { label: 'In Progress', value: RequestStatus.InProgress, icon: 'hourglass_top' },
    { label: 'Closed', value: RequestStatus.Closed, icon: 'check_circle' }
  ];
  statusSelected: RequestStatus = RequestStatus.All;

  // Table columns (omit Requestor/Department since it's "My")
  columns: TableColumn<ProcurementRequestLiteDto>[] = [
    {
      key: 'createdAt',
      header: 'Created',
      value: (item) => formatDateString(item.createdAt),
      cellClass: 'datetime',
      sortable: true,
      sortValue: (row) => new Date(row.createdAt)
    },
    {
      key: 'title',
      header: 'Title',
      value: (item) => item.title,
      sortable: true,
      primary: true
    },
    {
      key: 'commodityGroup',
      header: 'Commodity Group',
      value: (item) => item.commodityGroup?.name ?? '—',
      sortable: true
    },
    {
      key: 'vendorName',
      header: 'Vendor',
      value: (item) => item.vendorName,
      sortable: true
    },
    {
      key: 'totalCostsCent',
      header: 'Total',
      value: (item) => formatEuro(item.totalCostsCent),
      sortable: true,
      sortValue: (item) => item.totalCostsCent
    },
    {
      key: 'status',
      header: 'Status',
      cellComponent: StatusCellComponent
    },
  ];

  ngOnInit(): void {
    this.load();
  }

  onStatusChange(next: RequestStatus | null) {
    this.statusSelected = next ?? RequestStatus.All;
    this.load(this.statusSelected === RequestStatus.All ? undefined : this.statusSelected);
  }

  refresh(): void {
    this.load(this.statusSelected === RequestStatus.All ? undefined : this.statusSelected);
  }

  private load(status?: RequestStatus): void {
    this.loading = true;
    this.procurementService.getMyRequests(status).subscribe({
      next: (list) => { this.rows = list ?? []; this.loading = false; },
      error: (err) => { 
        this.errorService.handle(err, 'Failed to load my requests. Please try again later'); 
        this.rows = []; this.loading = false; 
      }
    });
  }

  trackById = (_: number, row: ProcurementRequestLiteDto) => row.id;
}
