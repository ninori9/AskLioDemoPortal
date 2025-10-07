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
import { RequestDraftDto } from '../../../data/dtos/request-draft.dto';
import { ProcurementRequestDto } from '../../../data/dtos/procurement-request.dto';
import { formatEuro, numberWithCommaValidator, numberWithCommaValidatorZero, parseLocaleNumber, positiveIntegerValidator } from '../../../_utils/common';
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
  orderLines:       FormArray<LineFG>;
  shipping:         FormControl<string>;
  tax:              FormControl<string>;
  totalDiscount:    FormControl<string>;
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
    MatProgressSpinnerModule,
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

  extractedGrandTotalCents: number | null = null;

  constructor(
    @Inject(MAT_DIALOG_DATA)
    public data: {
      initial?: RequestDraftDto | ProcurementRequestDto;
    }
  ) {}

  isEdit = false;
  saving = false;

  form!: RequestForm;

  ngOnInit(): void {
    this.initForm();

    const initial = this.data?.initial;
    if (initial) {
      console.log("initial", initial);
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
      title: this.formBuilder.nonNullable.control('', [Validators.required, Validators.maxLength(200)]),
      vendorName: this.formBuilder.nonNullable.control('', [Validators.required, Validators.maxLength(200)]),
      vatNumber: this.formBuilder.nonNullable.control('', [Validators.required, Validators.pattern(/^[A-Z]{2}[A-Z0-9]{8,12}$/i)]),
      orderLines: this.formBuilder.array<LineFG>([]),

      shipping:      this.formBuilder.nonNullable.control('', [numberWithCommaValidatorZero()]),
      tax:           this.formBuilder.nonNullable.control('', [numberWithCommaValidatorZero()]),
      totalDiscount: this.formBuilder.nonNullable.control('', [numberWithCommaValidatorZero()]),
    });
  }

  private patchInitial(initial: RequestDraftDto | ProcurementRequestDto) {
    // Common fields
    this.form.patchValue({
      title:      ('title' in initial ? initial.title ?? '' : ''),
      vendorName: ('vendorName' in initial ? initial.vendorName ?? '' : ''),
      vatNumber:  ('vatNumber' in initial ? initial.vatNumber ?? '' : ''),

      shipping: this.centsToLocaleString((initial as any).shippingCents),
      tax: this.centsToLocaleString((initial as any).taxCents),
      totalDiscount: this.centsToLocaleString((initial as any).totalDiscountCents),
    });

    this.extractedGrandTotalCents =
    typeof (initial as any).totalPriceCents === 'number'
      ? (initial as any).totalPriceCents
      : null;
  
    // Normalize line list
    const initialLines = Array.isArray((initial as any).orderLines)
      ? (initial as any).orderLines
      : [];
  
    this.lineGroups.clear();
  
    if (!initialLines.length) {
      this.addLine();
      return;
    }
  
    for (const line of initialLines) {
      // Support both draft (unitPriceCents) and potential other shapes (unitPrice, amountCents)
      const description = (line as any).description ?? '';
      const unit = (line as any).unit ?? 'pcs';
  
      // Prefer cents if present
      let unitPriceCents: number | undefined =
        typeof (line as any).unitPriceCents === 'number'
          ? (line as any).unitPriceCents
          : undefined;
  
      if (unitPriceCents === undefined) {
        // Fallback: "unitPrice" in euros -> convert to cents
        if (typeof (line as any).unitPrice === 'number') {
          unitPriceCents = Math.round((line as any).unitPrice * 100);
        } else if (typeof (line as any).amountCents === 'number') {
          unitPriceCents = (line as any).amountCents;
        } else {
          unitPriceCents = 0;
        }
      }
  
      // Quantity is not part of RequestDraftDto -> default to 1
      const quantity = typeof (line as any).quantity === 'number'
        ? (line as any).quantity
        : 1;
  
      const lineForm: LineFG = this.formBuilder.group({
        description: this.formBuilder.nonNullable.control(
          description,
          { validators: [Validators.required, Validators.maxLength(200)] }
        ),
        // Dialog expects a *string* in euros with locale formatting
        unitPrice: this.formBuilder.nonNullable.control(
          this.centsToLocaleString(unitPriceCents),
          { validators: [Validators.required, numberWithCommaValidator()] }
        ),
        quantity: this.formBuilder.nonNullable.control(
          String(quantity),
          { validators: [Validators.required, numberWithCommaValidator()] }
        ),
        unit: this.formBuilder.nonNullable.control(
          unit,
          { validators: [Validators.required, Validators.maxLength(50)] }
        ),
      });
  
      this.lineGroups.push(lineForm);
    }
  }
  
  // ----- Order lines -----

  get lineGroups(): FormArray<LineFG> {
    return this.form.controls.orderLines;
  }
  
  addLine() {
    const lineForm: LineFG = this.formBuilder.group({
      description: this.formBuilder.nonNullable.control('', { validators: [Validators.required, Validators.maxLength(300)] }),
      unitPrice:   this.formBuilder.nonNullable.control('', { validators: [Validators.required, numberWithCommaValidator()] }),
      quantity:    this.formBuilder.nonNullable.control('1', { validators: [Validators.required, numberWithCommaValidator()] }),
      unit:        this.formBuilder.nonNullable.control('pcs', { validators: [Validators.required, Validators.maxLength(50)] })
    });
  
    this.lineGroups.push(lineForm);
  }
  
  removeLine(index: number) {
    this.lineGroups.removeAt(index);
  }
  
  // ----- Totals & Validation -----

  private headerPartsCents() {
    const shippingCents = this.toCents(this.form.controls.shipping.value);
    const taxCents = this.toCents(this.form.controls.tax.value);
    const discountCents = this.toCents(this.form.controls.totalDiscount.value);
    return { shippingCents, taxCents, discountCents };
  }

  lineTotalCents(lineIndex: number): number {
    const lineForm = this.lineGroups.at(lineIndex);
    const unitPriceCents = this.toCents(lineForm.controls.unitPrice.value);
    const quantity = this.toPositiveNumber(lineForm.controls.quantity.value);
    if (quantity <= 0 || unitPriceCents <= 0) return 0;
    return unitPriceCents * quantity;
  }

  linesSubtotalCents(): number {
    let total = 0;
    for (let i = 0; i < this.lineGroups.length; i++) total += this.lineTotalCents(i);
    return total;
  }

  expectedTotalCents(): number {
    const { shippingCents, taxCents, discountCents } = this.headerPartsCents();
    return this.linesSubtotalCents() + shippingCents + taxCents - discountCents;
  }

  readonly TOLERANCE_CENTS = 2; // +/- 0.02

  hasMismatch(): boolean {
    if (this.extractedGrandTotalCents == null) return false;
    return Math.abs(this.expectedTotalCents() - this.extractedGrandTotalCents) > this.TOLERANCE_CENTS;
  }

  mismatchMessage(): string {
    if (this.extractedGrandTotalCents == null) return '';
    const expected = this.expectedTotalCents();
    return `Attention: extracted total is ${this.formatAmount(this.extractedGrandTotalCents)}. Calculated total is ${this.formatAmount(expected)}. Please verify the extracted content.`;
  }

  computedTotalNegative(): boolean {
    return this.expectedTotalCents() < 0; // hard stop
  }


  // ----- Close & Save -----

  close(): void {
    this.dialogRef.close();
  }

  save(): void {
    if (this.form.invalid || this.lineGroups.length === 0) {
      this.logInvalidControls();
      return;
    };
  
    this.saving = true;
    const raw = this.form.getRawValue();

    const { shippingCents, taxCents, discountCents } = this.headerPartsCents();
  
    const payload: CreateProcurementRequestDto = {
      title: raw.title.trim(),
      vendorName: raw.vendorName.trim(),
      vatID: raw.vatNumber.trim(),
      shippingCents: shippingCents > 0 ? shippingCents : undefined,
      taxCents: taxCents > 0 ? taxCents : undefined,
      totalDiscountCents: discountCents > 0 ? discountCents : undefined,
      orderLines: raw.orderLines.map(l => {
        const unitPriceCents = this.toCents(l.unitPrice);
        const quantity = this.toPositiveNumber(l.quantity);;
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

  // ----- Helpers -----

  formatAmount = (cents: number) => formatEuro(cents);

  private toCents(input: string): number {
    const n = parseLocaleNumber(input);
    if (!isFinite(n) || n <= 0) return 0;
    return Math.round(n * 100);
  }

  private centsToLocaleString(cents?: number): string {
    const v = (cents ?? 0) / 100;
    return v.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      useGrouping: false,
    });
  }

  private toPositiveNumber(input: string): number {
    const s = String(input ?? '').trim();
    if (!s) return 0;
    const n = parseLocaleNumber(s);
    return Number.isFinite(n) && n > 0 ? n : 0;
  }

  private logInvalidControls(): void {
    const errs: any = {};
  
    const dump = (grp: any, path: string[] = []) => {
      Object.keys(grp.controls ?? {}).forEach(key => {
        const c = grp.controls[key];
        const p = [...path, key];
        if (c instanceof FormGroup || c instanceof FormArray) {
          dump(c, p);
        } else {
          if (c.invalid) {
            errs[p.join('.')] = c.errors;
          }
        }
      });
    };
  
    dump(this.form);
    console.warn('INVALID CONTROLS →', errs);
  }
}
