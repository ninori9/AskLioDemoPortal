import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, Inject, inject } from '@angular/core';
import { FormArray, FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { CommodityGroupDto } from '../../../data/dtos/commodity-group.dto';
import { RequestDraftDto } from '../../../data/dtos/request-draft.dto';
import { ProcurementRequestDto } from '../../../data/dtos/procurement-request.dto';
import { formatEuro, numberWithCommaValidator, parseLocaleNumber, positiveIntegerValidator } from '../../../_utils/common';
import { CreateProcurementRequestDto } from '../../../data/dtos/create-procurement-request.dto';
import { ProcurementService } from '../../../services/procurement/procurement.service';
import { ErrorService } from '../../../services/error/error.service';

type LineFG = FormGroup<{
  description: FormControl<string>;
  unitPrice:   FormControl<string>;
  quantity:    FormControl<string>;
  unit:        FormControl<string>;
}>;

type RequestForm = FormGroup<{
  title:            FormControl<string>;
  vendorName:       FormControl<string>;
  vatNumber:        FormControl<string>;
  commodityGroupId: FormControl<number | null>;
  orderLines:       FormArray<LineFG>;
}>;

@Component({
  selector: 'app-new-procurement-request-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatIconModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './new-procurement-request-dialog.component.html',
  styleUrl: './new-procurement-request-dialog.component.scss'
})
export class NewProcurementRequestDialogComponent {
  private formBuilder = inject(FormBuilder);
  private dialogRef = inject(MatDialogRef<NewProcurementRequestDialogComponent>);
  private cdr = inject(ChangeDetectorRef);
  private procurementService = inject(ProcurementService);
  private errorService = inject(ErrorService);

  constructor(
    @Inject(MAT_DIALOG_DATA)
    public data: {
      commodityGroups: CommodityGroupDto[];
      initial?: RequestDraftDto | ProcurementRequestDto;
    }
  ) {}

  commodityGroups: CommodityGroupDto[] = [];
  isEdit = false;
  saving = false;

  form!: RequestForm;

  ngOnInit(): void {
    this.commodityGroups = this.data?.commodityGroups ?? [];
    this.initForm();

    const initial = this.data?.initial;
    if (initial) {
      this.isEdit = true;
      this.patchInitial(initial);
    } else {
      // Start with one empty line for convenience
      this.addLine();
    }

    this.cdr.detectChanges();
  }

  private initForm() {
    this.form = this.formBuilder.group({
      title: this.formBuilder.nonNullable.control('', [Validators.required, Validators.maxLength(160)]),
      vendorName: this.formBuilder.nonNullable.control('', [Validators.required, Validators.maxLength(120)]),
      vatNumber: this.formBuilder.nonNullable.control('', [Validators.required, Validators.pattern(/^[A-Z]{2}[A-Z0-9]{8,12}$/i)]),
      commodityGroupId: this.formBuilder.control<number | null>(null, { validators: [Validators.required] }),
      orderLines: this.formBuilder.array<LineFG>([])
    });
  }

  private patchInitial(initial: RequestDraftDto | ProcurementRequestDto) {
    const commodityGroupId =
      ('commodityGroup' in initial && initial.commodityGroup)
        ? initial.commodityGroup.id
        : (initial as RequestDraftDto).commodityGroupID ?? null;
  
    this.form.patchValue({
      title: ('title' in initial ? initial.title ?? '' : ''),
      vendorName: ('vendorName' in initial ? initial.vendorName ?? '' : ''),
      vatNumber: ('vatNumber' in initial ? initial.vatNumber ?? '' : ''),
      commodityGroupId
    });
  
    const initialLines = ('orderLines' in initial && Array.isArray(initial.orderLines))
      ? initial.orderLines
      : [];
  
    if (!initialLines.length) {
      this.addLine();
      return;
    }
  
    for (const line of initialLines) {
      const description = (line as any).description ?? '';
      const unit = (line as any).unit ?? 'pcs';
  
      const unitPriceNumeric =
        'unitPrice' in (line as any)
          ? (line as any).unitPrice
          : 'amountCents' in (line as any)
            ? (line as any).amountCents / 100
            : null;
  
      const quantityNumeric = 'quantity' in (line as any) ? (line as any).quantity : 1;
  
      const unitPriceStr = unitPriceNumeric != null ? String(unitPriceNumeric) : '';
      const quantityStr = quantityNumeric != null ? String(quantityNumeric) : '1';
  
      const lineForm: LineFG = this.formBuilder.group({
        description: this.formBuilder.nonNullable.control(description, { validators: [Validators.required, Validators.maxLength(200)] }),
        unitPrice: this.formBuilder.nonNullable.control(unitPriceStr, { validators: [Validators.required, numberWithCommaValidator()] }),
        quantity: this.formBuilder.nonNullable.control(quantityStr, { validators: [Validators.required, positiveIntegerValidator()] }),
        unit: this.formBuilder.nonNullable.control(unit, { validators: [Validators.required, Validators.maxLength(32)] })
      });
  
      this.lineGroups.push(lineForm);
    }
  }
  
  get lineGroups(): FormArray<LineFG> {
    return this.form.controls.orderLines;
  }
  
  addLine() {
    const lineForm: LineFG = this.formBuilder.group({
      description: this.formBuilder.nonNullable.control('', { validators: [Validators.required, Validators.maxLength(200)] }),
      unitPrice: this.formBuilder.nonNullable.control('', { validators: [Validators.required, numberWithCommaValidator()] }),
      quantity: this.formBuilder.nonNullable.control('1', { validators: [Validators.required, numberWithCommaValidator()] }),
      unit: this.formBuilder.nonNullable.control('pcs', { validators: [Validators.required, Validators.maxLength(32)] })
    });
  
    this.lineGroups.push(lineForm);
  }
  
  removeLine(index: number) {
    this.lineGroups.removeAt(index);
  }
  
  lineTotalCents(lineIndex: number): number {
    const lineForm = this.lineGroups.at(lineIndex);
    const unitPriceCents = this.toCents(lineForm.controls.unitPrice.value);
    const quantity = this.toPositiveInt(lineForm.controls.quantity.value);
    if (quantity <= 0 || unitPriceCents <= 0) return 0;
    return unitPriceCents * quantity;
  }
  
  grandTotalCents(): number {
    let total = 0;
    for (let lineIndex = 0; lineIndex < this.lineGroups.length; lineIndex++) {
      total += this.lineTotalCents(lineIndex);
    }
    return total;
  }

  formatAmount = (cents: number) => formatEuro(cents);

  close(): void {
    this.dialogRef.close();
  }

  save(): void {
    if (this.form.invalid || this.lineGroups.length === 0) return;
  
    this.saving = true;
    const raw = this.form.getRawValue();
  
    const payload: CreateProcurementRequestDto = {
      title: raw.title.trim(),
      vendorName: raw.vendorName.trim(),
      vatID: raw.vatNumber.trim(),
      commodityGroupID: raw.commodityGroupId as number,
      orderLines: raw.orderLines.map(l => {
        const unitPriceCents = this.toCents(l.unitPrice);
        const qtyRaw = parseLocaleNumber(l.quantity);
        const quantity = this.toPositiveInt(l.quantity);;
        return {
          description: l.description.trim(),
          unitPriceCents,
          quantity,
          unit: l.unit.trim(),
        };
      }),
    };
  
    this.procurementService.createRequest(payload).subscribe({
      next: created => {
        this.saving = false;
        this.dialogRef.close(created);
      },
      error: err => {
        this.saving = false;
        this.errorService.handle(err, "Failed to create procurement request. Please try again later.");
      }
    });
  }

  private toCents(input: string): number {
    const n = parseLocaleNumber(input);
    if (!isFinite(n) || n <= 0) return 0;
    return Math.round(n * 100);
  }

  private toPositiveInt(input: string): number {
    const s = String(input ?? '').trim();
    if (!/^\d+$/.test(s)) return 0;
    const n = Number(s);
    return Number.isFinite(n) && n > 0 ? n : 0;
  }
}
