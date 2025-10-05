import { Component, inject } from '@angular/core';
import { FilterChipsComponent } from '../layout/generic/filter-chips/filter-chips.component';
import { RequestStatus } from '../../data/enums/request-status.enum';
import { FilterOption } from '../../data/models/filter-option.model';
import { ProcurementService } from '../../services/procurement/procurement.service';
import { TableColumn } from '../../data/models/table-column.model';
import { ProcurementRequestLiteDto } from '../../data/dtos/procurement-request-lite.dto';
import { AskLioTableComponent } from '../layout/tables/asklio-table/asklio-table.component';
import { SkeletonTableComponent } from '../layout/tables/skeleton-table/skeleton-table.component';
import { CommonModule } from '@angular/common';
import { StatusCellComponent } from './status-cell/status-cell.component';
import { EditRequestCellComponent } from './edit-request-cell/edit-request-cell.component';
import { formatDateString, formatEuro } from '../../_utils/common';
import { CommodityGroupDto } from '../../data/dtos/commodity-group.dto';
import { MatDialog } from '@angular/material/dialog';
import { ProcurementRequestDialogComponent } from './procurement-request-dialog-component/procurement-request-dialog.component';
import { ErrorService } from '../../services/error/error.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-procurement-management',
  standalone: true,
  imports: [
    CommonModule,
    FilterChipsComponent,
    AskLioTableComponent,
    SkeletonTableComponent
  ],
  templateUrl: './procurement-management.component.html',
  styleUrl: './procurement-management.component.scss'
})
export class ProcurementManagementComponent {
  private procurementService = inject(ProcurementService);
  private errorService = inject(ErrorService)
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);

  loading: boolean = false;

  rows: ProcurementRequestLiteDto[] = [];

  commodityGroups: CommodityGroupDto[] = [];

  // Status filter
  statusOptions: FilterOption<RequestStatus>[] = [
    { label: 'All', value: RequestStatus.All, icon: 'all_inclusive' },
    { label: 'Open', value: RequestStatus.Open, icon: 'markunread_mailbox' },
    { label: 'In Progress', value: RequestStatus.InProgress, icon: 'hourglass_top' },
    { label: 'Closed', value: RequestStatus.Closed, icon: 'check_circle' }
  ];
  statusSelected: RequestStatus = RequestStatus.All;

  columns: TableColumn<ProcurementRequestLiteDto>[] = [
    {
      key: 'createdAt',
      header: 'Created',
      value: (item) => formatDateString(item.createdAt),
      cellClass: 'datetime',
      sortable: true,
      sortValue: (row) => new Date(row.createdAt),
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
      key: 'requestor',
      header: 'Requestor',
      value: (item) => item.requestorName,
      sortable: true
    },
    {
      key: 'department',
      header: 'Department',
      value: (item) => item.requestorDepartment,
      sortable: true
    },
    {
      key: 'status',
      header: 'Status',
      cellComponent: StatusCellComponent
    },
    {
      key: 'actions',
      header: "",
      cellComponent: EditRequestCellComponent
    }
  ];


  ngOnInit(): void {
    this.procurementService.getCommodityGroups().subscribe({
      next: (groups) => this.commodityGroups = groups ?? [],
      error: (err) => this.errorService.handle(err, 'Failed to load commodity group. Please try again later.')
    });

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
    this.procurementService.getRequests(status).subscribe({
      next: (list) => {
        this.rows = list ?? [];
        this.loading = false;
      },
      error: (err) => {
        // TODO: Add error handling
        this.errorService.handle(err, "Failed to load procurement requests. Please try again later.");
        this.rows = [];
        this.loading = false;
      }
    });
  }

  trackById = (_: number, row: ProcurementRequestLiteDto) => row.id;

  editRequest(row: ProcurementRequestLiteDto): void {
    const openDialog = () => {
      this.dialog.open(ProcurementRequestDialogComponent, {
        width: '90vw',
        panelClass: 'pm-dialog',
        maxWidth: '98vw',
        height: '92vh',
        data: {
          id: row.id,
          commodityGroups: this.commodityGroups
        }
      }).afterClosed().subscribe(result => {
        if (result) {
          this.snackBar.open(
            `Request “${result.title}” updated successfully.`,
            'Close',
            { duration: 3500, panelClass: ['snackbar-success'] }
          );
          this.refresh();
        }
      });
    };
  
    if (!this.commodityGroups.length) {
      this.procurementService.getCommodityGroups().subscribe({
        next: (groups) => { this.commodityGroups = groups ?? []; openDialog(); },
        error: (err) => { 
          this.errorService.handle(err, "Failed to load commodity groups. Please try again later."); 
          openDialog(); 
        }
      });
    } else {
      openDialog();
    }
  }
}
